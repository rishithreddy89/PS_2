import { useMemories, useMemoryStats, useDeleteMemory, useReindexMemory } from '@/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database, Clock, MessageSquare, Trash2, RefreshCw, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { formatDateTime } from '@/lib/utils';

export function Memory() {
  const [filter, setFilter] = useState<string | undefined>();
  const { data: memories, isLoading, refetch } = useMemories(filter ? { memory_type: filter } : undefined);
  const { data: stats } = useMemoryStats();
  const deleteMemory = useDeleteMemory();
  const reindexMemory = useReindexMemory();
  const { toast } = useToast();

  const memoryList = Array.isArray(memories) ? memories : [];

  const statCards = [
    { label: 'Total Memories', value: stats?.total || memoryList.length, icon: Database, color: 'text-blue-400' },
    { label: 'Long-term', value: stats?.by_type?.LONG_TERM || memoryList.filter((m: any) => m.memory_type === 'LONG_TERM').length, icon: Clock, color: 'text-green-400' },
    { label: 'Conversations', value: stats?.by_type?.CONVERSATION || memoryList.filter((m: any) => m.memory_type === 'CONVERSATION').length, icon: MessageSquare, color: 'text-purple-400' },
  ];

  const filters = ['SHORT_TERM', 'LONG_TERM', 'CONVERSATION', 'CASE'];

  const memoryTypeColors: Record<string, string> = {
    SHORT_TERM: 'default',
    LONG_TERM: 'success',
    CONVERSATION: 'warning',
    CASE: 'outline',
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this memory entry?')) return;
    try {
      await deleteMemory.mutateAsync(id);
      toast({ title: 'Memory deleted', variant: 'success' });
      refetch();
    } catch {
      // Error handled by interceptor
    }
  };

  const handleReindex = async (id: string) => {
    try {
      await reindexMemory.mutateAsync(id);
      toast({ title: 'Re-index requested', variant: 'success' });
      refetch();
    } catch {
      // Error handled by interceptor
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Memory Timeline</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-3xl font-bold mt-2">{stat.value}</p>
                </div>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <CardTitle>Memory Entries</CardTitle>
            <div className="flex gap-2 flex-wrap">
              <Button
                size="sm"
                variant={filter === undefined ? 'default' : 'outline'}
                onClick={() => setFilter(undefined)}
              >
                All
              </Button>
              {filters.map(f => (
                <Button
                  key={f}
                  size="sm"
                  variant={filter === f ? 'default' : 'outline'}
                  onClick={() => setFilter(f)}
                >
                  {f.replace('_', ' ')}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center gap-2 py-8">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-muted-foreground">Loading memories...</span>
            </div>
          ) : memoryList.length > 0 ? (
            <div className="space-y-4">
              {memoryList.map((memory: any) => (
                <div key={memory.id} className="relative pl-6 pb-4 border-l-2 border-border last:border-l-0 last:pb-0">
                  <div className="absolute left-[-9px] top-0 h-4 w-4 rounded-full bg-accent border-2 border-background" />
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={(memoryTypeColors[memory.memory_type] || 'default') as any}>
                          {memory.memory_type}
                        </Badge>
                        {memory.key && (
                          <span className="text-xs font-mono text-muted-foreground">{memory.key}</span>
                        )}
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {memory.created_at ? formatDateTime(memory.created_at) : 'Unknown'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleReindex(memory.id)}
                          disabled={reindexMemory.isPending}
                          title="Re-index"
                        >
                          <RefreshCw className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(memory.id)}
                          disabled={deleteMemory.isPending}
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="text-sm">
                      {memory.content && typeof memory.content === 'object' ? (
                        Object.entries(memory.content).map(([key, value]) => (
                          <div key={key} className="mb-1">
                            <span className="font-medium text-foreground">{key}: </span>
                            <span className="text-muted-foreground">
                              {typeof value === 'string' ? value : JSON.stringify(value)}
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground">{String(memory.content)}</p>
                      )}
                    </div>

                    {memory.metadata && (
                      <div className="flex gap-2 flex-wrap">
                        {memory.metadata.reindex_status && (
                          <Badge variant="outline" className="text-xs">
                            Index: {memory.metadata.reindex_status}
                          </Badge>
                        )}
                        {memory.case_id && (
                          <Badge variant="outline" className="text-xs">
                            Case: {memory.case_id.substring(0, 8)}...
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">No memory entries found</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
