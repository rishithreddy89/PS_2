import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TimelineEvent } from '@/types';
import { CalendarDays } from 'lucide-react';

export function TimelineView({ events }: { events?: TimelineEvent[] }) {
  if (!events || events.length === 0) return null;

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <CalendarDays className="h-5 w-5 text-primary" />
          Chronological Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative border-l border-muted-foreground/20 ml-3 pl-4 space-y-6 mt-4">
          {events.map((event, idx) => (
            <div key={idx} className="relative">
              <span className={`absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-background
                ${event.importance?.toLowerCase() === 'high' ? 'bg-destructive' : 
                  event.importance?.toLowerCase() === 'medium' ? 'bg-amber-500' : 'bg-primary'}`} 
              />
              <div className="flex flex-col gap-1">
                <span className="text-sm font-bold text-foreground">{event.date}</span>
                <p className="text-sm text-muted-foreground">{event.event}</p>
                {event.source_document && (
                  <span className="text-xs text-muted-foreground/70 italic flex items-center gap-1 mt-1">
                    Source: {event.source_document}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
