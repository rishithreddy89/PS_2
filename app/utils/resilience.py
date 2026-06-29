"""
Retry and error recovery utilities for production resilience.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions


def retry_async(config: Optional[RetryConfig] = None):
    """
    Decorator for async functions with retry logic.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function with retry capability
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = config.initial_delay
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            "Max retry attempts reached",
                            function=func.__name__,
                            attempts=attempt,
                            error=str(e),
                        )
                        raise
                    
                    logger.warning(
                        "Retrying after failure",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=config.max_attempts,
                        delay=delay,
                        error=str(e),
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * config.exponential_base, config.max_delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    
    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                "Circuit breaker opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold,
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.last_failure_time is None:
            return True
        
        elapsed = asyncio.get_event_loop().time() - self.last_failure_time
        return elapsed >= self.recovery_timeout


class ErrorRecoveryManager:
    """Manages error recovery strategies for different error types."""
    
    def __init__(self):
        self.strategies = {}
    
    def register_strategy(
        self,
        exception_type: Type[Exception],
        strategy: Callable[[Exception], Any],
    ):
        """Register recovery strategy for exception type."""
        self.strategies[exception_type] = strategy
    
    async def recover(self, exception: Exception) -> Any:
        """
        Attempt to recover from exception.
        
        Args:
            exception: Exception to recover from
            
        Returns:
            Recovery result or None
        """
        exception_type = type(exception)
        
        if exception_type in self.strategies:
            strategy = self.strategies[exception_type]
            
            try:
                logger.info(
                    "Attempting recovery",
                    exception_type=exception_type.__name__,
                )
                return await strategy(exception)
                
            except Exception as e:
                logger.error(
                    "Recovery failed",
                    exception_type=exception_type.__name__,
                    error=str(e),
                )
                return None
        
        return None


# Global instances
default_recovery_manager = ErrorRecoveryManager()
