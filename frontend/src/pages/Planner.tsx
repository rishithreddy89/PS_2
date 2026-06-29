import { useAgents, usePlannerExecutions } from '@/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Zap, Database, CheckCircle, XCircle, Clock, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatDateTime } from '@/lib/utils';

export function Planner() {
  const { data: agents, isLoading: agentsLoading } = useAgents();
  const { data: executions, isLoading: execsLoading, refetch: refetchExecs } = usePlannerExecutions();
  
  // Ensure agents is always an array
  const agentList = Array.isArray(agents) ? agents : [];
  const activeAgents = agentList.filter(a => a.status === 'ACTIVE');
  const totalCapabilities = agentList.reduce((acc, a) => acc + (a.capabilities?.length || 0), 0);

  const executionList = Array.isArray(executions) ? executions : [];

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running': case 'pending': return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default: return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success';
      case 'failed': return 'destructive';
      case 'running': return 'warning';
      default: return 'outline';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Agent Planner</h1>
        <Button variant="outline" size="sm" onClick={() => refetchExecs()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Agents</p>
                <p className="text-3xl font-bold mt-2">{agentList.length}</p>
              </div>
              <Activity className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Agents</p>
                <p className="text-3xl font-bold mt-2">{activeAgents.length}</p>
              </div>
              <Zap className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Capabilities</p>
                <p className="text-3xl font-bold mt-2">{totalCapabilities}</p>
              </div>
              <Database className="h-8 w-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Execution History */}
      <Card>
        <CardHeader>
          <CardTitle>Execution History</CardTitle>
        </CardHeader>
        <CardContent>
          {execsLoading ? (
            <div className="flex items-center justify-center gap-2 py-8">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-muted-foreground">Loading executions...</span>
            </div>
          ) : executionList.length > 0 ? (
            <div className="space-y-3">
              {executionList.map((exec: any) => {
                const trace = exec.meta_data?.execution_trace || [];
                const completedAgents = trace.filter((t: any) => t.status === 'completed').map((t: any) => t.agent_name || t.agent_id);
                const failedAgents = trace.filter((t: any) => t.status === 'failed').map((t: any) => t.agent_name || t.agent_id);

                return (
                  <div key={exec.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(exec.status)}
                        <div>
                          <p className="font-medium text-sm">
                            {exec.workflow_type || 'Full Analysis'}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {exec.created_at ? formatDateTime(exec.created_at) : 'Unknown'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {exec.duration_ms && (
                          <Badge variant="outline" className="text-xs">
                            {exec.duration_ms}ms
                          </Badge>
                        )}
                        <Badge variant={getStatusBadge(exec.status) as any}>
                          {exec.status}
                        </Badge>
                      </div>
                    </div>

                    {(completedAgents.length > 0 || failedAgents.length > 0) && (
                      <div className="flex flex-wrap gap-1">
                        {completedAgents.map((agent: string, i: number) => (
                          <Badge key={`c-${i}`} variant="outline" className="text-xs">
                            <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                            {agent}
                          </Badge>
                        ))}
                        {failedAgents.map((agent: string, i: number) => (
                          <Badge key={`f-${i}`} variant="outline" className="text-xs">
                            <XCircle className="h-3 w-3 mr-1 text-red-500" />
                            {agent}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {exec.error_message && (
                      <div className="bg-destructive/10 rounded p-2">
                        <p className="text-xs text-destructive">{exec.error_message}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">No executions recorded yet</p>
          )}
        </CardContent>
      </Card>

      {/* Registered Agents */}
      <Card>
        <CardHeader>
          <CardTitle>Registered Agents</CardTitle>
        </CardHeader>
        <CardContent>
          {agentsLoading ? (
            <div className="flex items-center justify-center gap-2 py-8">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-muted-foreground">Loading agents...</span>
            </div>
          ) : agentList.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agentList.map(agent => (
                <Card key={agent.agent_id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{agent.name}</CardTitle>
                        <p className="text-xs text-muted-foreground mt-1">v{agent.version}</p>
                      </div>
                      <Badge variant={agent.status === 'ACTIVE' ? 'success' : 'outline'}>
                        {agent.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-3">{agent.description}</p>
                    <div>
                      <p className="text-xs font-medium mb-2">Capabilities:</p>
                      <div className="flex flex-wrap gap-1">
                        {(agent.capabilities || []).map((cap: string) => (
                          <Badge key={cap} variant="outline" className="text-xs">{cap}</Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">No agents registered</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
