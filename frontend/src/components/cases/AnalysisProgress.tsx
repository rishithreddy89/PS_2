import { useState, useEffect, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface AnalysisProgressProps {
  caseId: string;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

interface ExecutionEvent {
  event: string;
  agent_name?: string;
  status?: string;
  duration_ms?: number;
  error?: string;
  plan?: any;
}

const WORKFLOW_TIMEOUT_MS = 180_000; // 180 seconds

export function AnalysisProgress({ caseId, open, onClose, onComplete }: AnalysisProgressProps) {
  const [status, setStatus] = useState<string>('Starting...');
  const [currentAgent, setCurrentAgent] = useState<string>('');
  const [completedAgents, setCompletedAgents] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const terminatedRef = useRef(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Safely close everything and dismiss the modal */
  const terminateWorkflow = (
    reason: 'success' | 'failure' | 'timeout',
    errorMsg?: string,
    delayMs: number = 1500
  ) => {
    if (terminatedRef.current) return;
    terminatedRef.current = true;

    console.log(`[AnalysisProgress] Terminating: reason=${reason}, error=${errorMsg}`);

    // Close SSE connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Clear timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    if (reason === 'success') {
      setStatus('Analysis complete!');
      setProgress(100);
    } else {
      setStatus('Analysis failed');
      setError(errorMsg || 'Unknown error');
    }

    setTimeout(() => {
      onComplete();
      onClose();
    }, delayMs);
  };

  useEffect(() => {
    if (!open) return;

    // Reset state for a new run
    terminatedRef.current = false;
    setLogs([]);
    setProgress(0);
    setError(null);
    setStatus('Starting...');
    setCurrentAgent('');
    setCompletedAgents([]);

    const startAnalysis = async () => {
      try {
        // POST to start analysis
        console.log('[AnalysisProgress] POST /analyze');
        const response = await fetch(
          `http://localhost:8000/api/v1/analysis/cases/${caseId}/analyze`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to start analysis');
        }

        await response.json();
        setStatus('Analysis started');
        setLogs(prev => [...prev, 'Analysis workflow started']);

        // Start the hard timeout — if nothing finishes in 180s, force-close
        timeoutRef.current = setTimeout(() => {
          console.warn('[AnalysisProgress] Workflow timeout reached (180s)');
          setLogs(prev => [...prev, '⏱ Workflow timeout — forcing close']);
          terminateWorkflow('timeout', 'Workflow exceeded maximum time limit (180s). Please try again.');
        }, WORKFLOW_TIMEOUT_MS);

        // Connect to SSE stream
        console.log('[AnalysisProgress] Opening SSE connection');
        const eventSource = new EventSource(
          `http://localhost:8000/api/v1/analysis/cases/${caseId}/stream`
        );
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          try {
            const data: ExecutionEvent = JSON.parse(event.data);
            console.log('[AnalysisProgress] SSE event:', data.event, data);

            switch (data.event) {
              case 'workflow_started':
                setStatus('Workflow started');
                setLogs(prev => [...prev, 'Workflow execution started']);
                break;

              case 'planning_started':
                setStatus('Planning workflow...');
                setLogs(prev => [...prev, 'Planner analyzing case']);
                setProgress(10);
                break;

              case 'planning_completed':
                setStatus('Plan created');
                setLogs(prev => [...prev, `Plan: ${data.plan?.agent_count} agents selected`]);
                setProgress(20);
                break;

              case 'orchestration_started':
                setStatus('Executing agents...');
                setLogs(prev => [...prev, 'Starting agent execution']);
                setProgress(30);
                break;

              case 'agent_completed':
                setCurrentAgent('');
                setCompletedAgents(prev => [...prev, data.agent_name || '']);
                setLogs(prev => [...prev, `✓ ${data.agent_name} completed (${data.duration_ms}ms)`]);
                setProgress(prev => Math.min(prev + 10, 90));
                break;

              case 'orchestration_completed':
                setStatus('Saving results...');
                setLogs(prev => [...prev, 'All agents completed']);
                setProgress(95);
                break;

              case 'workflow_completed':
                setStatus('Analysis complete!');
                setLogs(prev => [...prev, 'Workflow completed successfully']);
                setProgress(100);
                break;

              case 'completed':
                setLogs(prev => [...prev, 'Connection closed cleanly']);
                if (data.status === 'failed') {
                  terminateWorkflow('failure', data.error || 'Workflow failed', 3000);
                } else {
                  terminateWorkflow('success');
                }
                break;

              case 'workflow_failed':
                setLogs(prev => [...prev, `✗ Error: ${data.error}`]);
                terminateWorkflow('failure', data.error || 'Unknown error', 3000);
                break;

              case 'error':
                setLogs(prev => [...prev, `✗ Stream error: ${data.error}`]);
                terminateWorkflow('failure', data.error || 'Stream error', 3000);
                break;

              default:
                console.log('[AnalysisProgress] Unhandled SSE event:', data.event);
                break;
            }
          } catch (parseErr) {
            console.error('[AnalysisProgress] Failed to parse SSE data:', parseErr);
          }
        };

        eventSource.onerror = () => {
          console.error('[AnalysisProgress] SSE connection error');
          terminateWorkflow('failure', 'Connection to server lost', 3000);
        };

      } catch (err: any) {
        console.error('[AnalysisProgress] Start analysis error:', err);
        terminateWorkflow('failure', err.message || 'Failed to start analysis', 3000);
      }
    };

    startAnalysis();

    // Cleanup on unmount or when modal closes
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [open, caseId]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>AI Analysis in Progress</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center gap-2">
            {error ? (
              <XCircle className="h-5 w-5 text-destructive" />
            ) : progress === 100 ? (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            ) : (
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            )}
            <span className="font-medium">{status}</span>
          </div>

          <Progress value={progress} className="w-full" />

          {currentAgent && (
            <div className="flex items-center gap-2">
              <Badge variant="outline">{currentAgent}</Badge>
              <span className="text-sm text-muted-foreground">Running...</span>
            </div>
          )}

          <div className="border rounded-lg p-4 max-h-60 overflow-auto bg-muted/50">
            <p className="text-xs font-medium mb-2">Execution Log</p>
            <div className="space-y-1">
              {logs.map((log, i) => (
                <p key={i} className="text-xs font-mono text-muted-foreground">
                  {log}
                </p>
              ))}
            </div>
          </div>

          {completedAgents.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Completed Agents</p>
              <div className="flex flex-wrap gap-2">
                {completedAgents.map((agent, i) => (
                  <Badge key={i} variant="outline">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    {agent}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded p-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
