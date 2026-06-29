import { useState, useEffect, useCallback } from 'react';
import { onToast } from '@/lib/api';

export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: 'default' | 'destructive' | 'success';
}

let globalToastFn: ((toast: Omit<Toast, 'id'>) => void) | null = null;

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((props: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { ...props, id };
    setToasts(prev => [...prev, newToast]);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Register as global toast handler
  useEffect(() => {
    globalToastFn = toast;
    const unsubscribe = onToast((t) => {
      toast(t);
    });
    return () => {
      globalToastFn = null;
      unsubscribe();
    };
  }, [toast]);

  return { toast, toasts, dismiss };
}

// Standalone toast function for use outside React components
export function showToast(props: Omit<Toast, 'id'>) {
  if (globalToastFn) {
    globalToastFn(props);
  } else {
    console.log('[Toast]', props.title, props.description);
  }
}
