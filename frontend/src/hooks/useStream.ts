import { useEffect, useState, useCallback, useRef } from 'react';

export interface StreamEvent {
  event: string;
  [key: string]: any;
}

export interface UseStreamOptions {
  onEvent?: (event: StreamEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
  autoStart?: boolean;
}

export function useStream(url: string, options: UseStreamOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      return; // Already connected
    }

    setIsConnected(false);
    setIsComplete(false);
    setError(null);

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('SSE connection opened:', url);
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      const error = new Error('Stream connection error');
      setError(error);
      options.onError?.(error);
      disconnect();
    };

    // Handle different event types
    const eventTypes = [
      'workflow_started',
      'ingestion_started',
      'ingestion_completed',
      'planning_started',
      'planning_completed',
      'orchestration_started',
      'agent_completed',
      'orchestration_completed',
      'workflow_completed',
      'workflow_failed',
      'completed',
      'error',
      'message',
      'status_update',
    ];

    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          const event: StreamEvent = { event: eventType, ...data };
          
          setEvents((prev) => [...prev, event]);
          options.onEvent?.(event);

          if (eventType === 'workflow_completed' || eventType === 'workflow_failed' || eventType === 'completed') {
            setIsComplete(true);
            options.onComplete?.();
            disconnect();
          }
        } catch (err) {
          console.error('Failed to parse SSE data:', err);
        }
      });
    });

    return () => {
      disconnect();
    };
  }, [url, options]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const reset = useCallback(() => {
    disconnect();
    setEvents([]);
    setError(null);
    setIsComplete(false);
  }, [disconnect]);

  useEffect(() => {
    if (options.autoStart !== false) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url]);

  return {
    events,
    isConnected,
    isComplete,
    error,
    connect,
    disconnect,
    reset,
  };
}
