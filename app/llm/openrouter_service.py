"""OpenRouter service for LLM interactions."""

import json
import os
import time
from typing import Dict, Any, Optional, List, Type, TypeVar, Callable
from pydantic import BaseModel

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

T = TypeVar('T', bound=BaseModel)


class OpenRouterService:
    """Centralized OpenRouter service using OpenAI-compatible API."""
    
    def __init__(self):
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.openrouter_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        
        # Required headers for OpenRouter
        self.extra_headers = {
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "LexMind AI"
        }
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=2, max=60))
    async def complete(
        self,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Type[T]] = None
    ) -> Dict[str, Any]:
        """Generate completion with retry logic."""
        start_time = time.time()
        
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if prompt:
                messages.append({"role": "user", "content": prompt})
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens or 6000,
                "extra_headers": self.extra_headers
            }
            
            if response_format:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if not response or not hasattr(response, 'choices') or not response.choices:
                error_msg = f"Invalid response structure from OpenRouter: {response}"
                logger.error("OpenRouter response parsing failed", error=error_msg, duration_ms=duration_ms)
                raise ValueError(error_msg)
                
            if not response.choices[0].message:
                error_msg = "OpenRouter response choice missing message"
                logger.error("OpenRouter response parsing failed", error=error_msg, duration_ms=duration_ms)
                raise ValueError(error_msg)
            
            content = response.choices[0].message.content

            
            result = {
                "content": content,
                "model": response.model,
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
                "duration_ms": duration_ms,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(
                "OpenRouter completion",
                model=response.model,
                tokens=result["total_tokens"],
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            from openai import RateLimitError, APIStatusError
            if isinstance(e, RateLimitError) or (isinstance(e, APIStatusError) and e.status_code == 429):
                logger.warning("OpenRouter rate limit hit (HTTP 429)", error=str(e))
            else:
                logger.error("OpenRouter completion failed", error=str(e))
            raise
    
    async def complete_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 1,
        normalize_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        return_meta: bool = False
    ) -> Any:
        """Generate structured completion with validation."""
        current_prompt = prompt
        
        start_time = time.time()
        for attempt in range(max_retries + 1):
            try:
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": current_prompt})
                
                accumulated_content = ""
                finish_reason = None
                total_input = 0
                total_output = 0
                
                for cont_attempt in range(2):
                    result = await self.complete(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=6000,
                        response_format=response_model
                    )
                    
                    content_chunk = result.get("content") or ""
                    accumulated_content += content_chunk
                    total_input += result.get("input_tokens", 0)
                    total_output += result.get("output_tokens", 0)
                    finish_reason = result.get("finish_reason")
                    
                    if finish_reason == "length":
                        logger.warning("LLM output truncated (finish_reason=length), requesting continuation...")
                        messages.append({"role": "assistant", "content": content_chunk})
                        messages.append({"role": "user", "content": "Continue the previous JSON exactly where it stopped. Do not output a new JSON opening bracket unless required, just continue the exact string."})
                    else:
                        break
                
                content = accumulated_content
                if not content:
                    raise ValueError("LLM returned no content.")
                    
                logger.info(
                    "Raw OpenRouter response",
                    extra={
                        "model": result.get("model"),
                        "content": content,
                        "usage": {
                            "input_tokens": total_input,
                            "output_tokens": total_output,
                            "total_tokens": total_input + total_output
                        },
                        "finish_reason": finish_reason,
                        "attempt": attempt + 1
                    }
                )
                
                # Parse JSON
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # Clean markdown code blocks and extract JSON
                    start_idx = content.find("{")
                    end_idx = content.rfind("}")
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        cleaned = content[start_idx:end_idx+1]
                        try:
                            data = json.loads(cleaned)
                        except json.JSONDecodeError:
                            data = None
                    else:
                        data = None
                        
                    if data is None:
                        cleaned = content.strip()
                        if cleaned.startswith("```"):
                            nl_idx = cleaned.find("\n")
                            if nl_idx != -1:
                                cleaned = cleaned[nl_idx:].strip()
                            if cleaned.endswith("```"):
                                cleaned = cleaned[:-3].strip()
                        
                        try:
                            data = json.loads(cleaned)
                        except json.JSONDecodeError as e:
                            logger.error(
                                "Failed to extract JSON from OpenRouter response", 
                                extra={"raw_content": content, "error": str(e)}
                            )
                            raise ValueError(f"Could not extract valid JSON from the LLM response. Error: {e}")
                        
                logger.debug("Parsed JSON", extra={"parsed": data, "attempt": attempt + 1})
                
                # Normalize JSON if a function is provided
                if normalize_func and isinstance(data, dict):
                    data = normalize_func(data)
                    logger.debug("Normalized JSON", normalized=data, attempt=attempt + 1)
                
                # Validate with Pydantic
                from pydantic import ValidationError
                try:
                    validated = response_model(**data)
                except ValidationError as ve:
                    logger.warning("Validation errors", errors=ve.errors(), attempt=attempt + 1)
                    
                    if attempt < max_retries:
                        # Append the error to the prompt and try again
                        error_msg = f"\n\nSystem Notice: The previous response failed validation with these errors:\n{ve}\n\nPlease repair ONLY the JSON. Return ONLY valid JSON matching the exact schema required. DO NOT include markdown formatting or explanations."
                        current_prompt += error_msg
                        continue
                    else:
                        raise ve
                
                logger.info(
                    "Structured completion validated",
                    extra={
                        "model": response_model.__name__,
                        "attempt": attempt + 1
                    }
                )
                
                # Log final validated object
                logger.info("Parsed recommendation object", extra={"parsed": validated.model_dump()})
                
                if return_meta:
                    return validated, {
                        "input_tokens": total_input,
                        "output_tokens": total_output,
                        "duration_ms": (time.time() - start_time) * 1000,
                        "validation_retries": attempt
                    }
                return validated
                
            except Exception as e:
                logger.warning(
                    "Structured completion attempt failed",
                    extra={
                        "attempt": attempt + 1,
                        "error": str(e)
                    }
                )
                
                if attempt == max_retries:
                    # Fail gracefully without crashing
                    logger.error("Structured completion failed after all retries", extra={"error": str(e)})
                    raise ValueError(f"Failed to generate valid {response_model.__name__}: {e}")
    
    async def complete_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate completion with conversation history."""
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                extra_headers=self.extra_headers
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            logger.error("OpenRouter completion with history failed", error=str(e))
            raise
    
    async def stream_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """Stream completion tokens."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                stream=True,
                extra_headers=self.extra_headers
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error("OpenRouter streaming failed", error=str(e))
            raise
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD (approximate rates)."""
        # OpenRouter pricing is variable depending on model
        return 0.0


_openrouter_service: Optional[OpenRouterService] = None


def get_openrouter_service() -> OpenRouterService:
    """Get singleton OpenRouter service."""
    global _openrouter_service
    if _openrouter_service is None:
        _openrouter_service = OpenRouterService()
    return _openrouter_service
