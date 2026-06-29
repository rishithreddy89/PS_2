import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Memory } from '@/types';
import { formatDateTime } from '@/lib/utils';
import { Clock } from 'lucide-react';

interface Props {
  memories: Memory[];
}

const memoryTypeColors = {
  SHORT_TERM: 'default',
  LONG_TERM: 'success',
  CONVERSATION: 'warning',
  CASE: 'outline',
} as const;

export function MemoryTimeline({ memories }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Memory Timeline</CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {memories.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No memory entries</p>
          ) : (
            memories.map((memory) => (
              <div key={memory.id} className="relative pl-6 pb-4 border-l-2 border-border last:border-l-0 last:pb-0">
                <div className="absolute left-[-9px] top-0 h-4 w-4 rounded-full bg-accent border-2 border-background" />
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={memoryTypeColors[memory.memory_type]}>{memory.memory_type}</Badge>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDateTime(memory.created_at)}
                    </span>
                  </div>
                  
                  <div className="text-sm">
                    {Object.entries(memory.content).map(([key, value]) => (
                      <div key={key} className="mb-2">
                        <span className="font-medium text-foreground">{key}: </span>
                        <span className="text-muted-foreground">{JSON.stringify(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
