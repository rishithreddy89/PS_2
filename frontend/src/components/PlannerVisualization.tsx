import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { PlannerExecution } from '@/types';
import { CheckCircle, XCircle, Clock, ArrowDown } from 'lucide-react';

interface Props {
  execution: PlannerExecution;
}

const statusColors = {
  COMPLETED: 'success',
  RUNNING: 'warning',
  FAILED: 'destructive',
  PENDING: 'outline',
  CANCELLED: 'outline',
} as const;

export function PlannerVisualization({ execution }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Planner Execution</span>
          <Badge variant={statusColors[execution.status]}>{execution.status}</Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          <div className="text-sm">
            <p className="text-muted-foreground">Workflow: <span className="text-foreground">{execution.workflow_type}</span></p>
            {execution.total_duration_ms && (
              <p className="text-muted-foreground">Duration: <span className="text-foreground">{execution.total_duration_ms}ms</span></p>
            )}
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Execution Flow</h4>
            <div className="space-y-3">
              {execution.executed_agents.map((agent, idx) => (
                <div key={idx}>
                  <div className="flex items-center gap-3 p-3 rounded-md bg-accent/50">
                    <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="font-medium">{agent}</p>
                      <p className="text-xs text-muted-foreground">Completed successfully</p>
                    </div>
                  </div>
                  {idx < execution.executed_agents.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowDown className="h-4 w-4 text-muted-foreground" />
                    </div>
                  )}
                </div>
              ))}

              {execution.failed_agents.map((agent, idx) => (
                <div key={`failed-${idx}`} className="flex items-center gap-3 p-3 rounded-md bg-destructive/20">
                  <XCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium">{agent}</p>
                    <p className="text-xs text-muted-foreground">Failed</p>
                  </div>
                </div>
              ))}

              {execution.skipped_agents.map((agent, idx) => (
                <div key={`skipped-${idx}`} className="flex items-center gap-3 p-3 rounded-md bg-muted/50">
                  <Clock className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-muted-foreground">{agent}</p>
                    <p className="text-xs text-muted-foreground">Skipped</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
