import { useState } from 'react';
import { useStream, StreamEvent } from '@/hooks/useStream';
import { Check, X, Loader2, AlertCircle } from 'lucide-react';

interface WorkflowExecutionProps {
  caseId: string;
  workflowType?: string;
  onComplete?: (result: any) => void;
}

export function WorkflowExecution({ caseId, workflowType = 'full_analysis', onComplete }: WorkflowExecutionProps) {
  const [stages, setStages] = useState<Record<string, { status: string; details?: any }>>({});
  const [completedAgents, setCompletedAgents] = useState<string[]>([]);

  const handleEvent = (event: StreamEvent) => {
    console.log('Workflow event:', event);

    switch (event.event) {
      case 'workflow_started':
        setStages({ workflow: { status: 'running' } });
        break;

      case 'ingestion_started':
        setStages((prev) => ({ ...prev, ingestion: { status: 'running', details: event } }));
        break;

      case 'ingestion_completed':
        setStages((prev) => ({ ...prev, ingestion: { status: 'completed' } }));
        break;

      case 'planning_started':
        setStages((prev) => ({ ...prev, planning: { status: 'running' } }));
        break;

      case 'planning_completed':
        setStages((prev) => ({ ...prev, planning: { status: 'completed', details: event.plan } }));
        break;

      case 'orchestration_started':
        setStages((prev) => ({ ...prev, orchestration: { status: 'running' } }));
        break;

      case 'agent_completed':
        setCompletedAgents((prev) => [...prev, event.agent_name]);
        break;

      case 'orchestration_completed':
        setStages((prev) => ({ ...prev, orchestration: { status: 'completed', details: event } }));
        break;

      case 'workflow_completed':
        setStages((prev) => ({ ...prev, workflow: { status: 'completed', details: event.final_output } }));
        onComplete?.(event.final_output);
        break;

      case 'workflow_failed':
        setStages((prev) => ({ ...prev, workflow: { status: 'failed', details: event } }));
        break;
    }
  };

  const { isConnected, error } = useStream(
    `/api/v1/stream/workflow/${caseId}?workflow_type=${workflowType}`,
    {
      onEvent: handleEvent,
      autoStart: true,
    }
  );

  const getStageIcon = (status?: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
      case 'completed':
        return <Check className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <X className="w-5 h-5 text-red-500" />;
      default:
        return <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
        <span className="text-sm text-gray-600">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-red-900">Workflow Error</h4>
            <p className="text-sm text-red-700">{error.message}</p>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {stages.ingestion && (
          <div className="flex items-start gap-4 bg-white border border-gray-200 rounded-lg p-4">
            {getStageIcon(stages.ingestion.status)}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Document Ingestion</h3>
              {stages.ingestion.details?.document_count && (
                <p className="text-sm text-gray-600">Processing {stages.ingestion.details.document_count} documents</p>
              )}
            </div>
          </div>
        )}

        {stages.planning && (
          <div className="flex items-start gap-4 bg-white border border-gray-200 rounded-lg p-4">
            {getStageIcon(stages.planning.status)}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Planning</h3>
              {stages.planning.details && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Agents: {stages.planning.details.agent_count}</p>
                  <p>Estimated: {stages.planning.details.estimated_duration_ms}ms</p>
                </div>
              )}
            </div>
          </div>
        )}

        {stages.orchestration && (
          <div className="flex items-start gap-4 bg-white border border-gray-200 rounded-lg p-4">
            {getStageIcon(stages.orchestration.status)}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Agent Execution</h3>
              {completedAgents.length > 0 && (
                <p className="text-sm text-gray-600">Completed: {completedAgents.length}</p>
              )}
            </div>
          </div>
        )}

        {stages.workflow && (
          <div className="flex items-start gap-4 bg-white border border-gray-200 rounded-lg p-4">
            {getStageIcon(stages.workflow.status)}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Workflow Status</h3>
              <p className="text-sm text-gray-600 capitalize">{stages.workflow.status}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
