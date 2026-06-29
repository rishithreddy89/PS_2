import { useToast } from '@/hooks/use-toast';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

export function Toaster() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-md">
      {toasts.map((toast) => {
        const isDestructive = toast.variant === 'destructive';
        const isSuccess = toast.variant === 'success';

        return (
          <div
            key={toast.id}
            className={`
              flex items-start gap-3 p-4 rounded-lg shadow-lg border
              animate-in slide-in-from-right-full duration-300
              ${isDestructive
                ? 'bg-red-950/90 border-red-800 text-red-100'
                : isSuccess
                  ? 'bg-green-950/90 border-green-800 text-green-100'
                  : 'bg-card border-border text-card-foreground'
              }
            `}
          >
            <div className="flex-shrink-0 mt-0.5">
              {isDestructive ? (
                <AlertCircle className="h-5 w-5 text-red-400" />
              ) : isSuccess ? (
                <CheckCircle className="h-5 w-5 text-green-400" />
              ) : (
                <Info className="h-5 w-5 text-blue-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold">{toast.title}</p>
              {toast.description && (
                <p className="text-xs mt-1 opacity-80">{toast.description}</p>
              )}
            </div>
            <button
              onClick={() => dismiss(toast.id)}
              className="flex-shrink-0 p-1 rounded hover:bg-white/10 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
