import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Case } from '@/types';
import { formatDate } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';
import { Trash2 } from 'lucide-react';
import { Button } from './ui/button';

interface Props {
  case_: Case;
  onDelete?: (e: React.MouseEvent) => void;
}

const priorityColors: Record<string, string> = {
  CRITICAL: 'destructive',
  HIGH: 'warning',
  MEDIUM: 'default',
  LOW: 'outline',
  // lowercase variants
  critical: 'destructive',
  high: 'warning',
  medium: 'default',
  low: 'outline',
  urgent: 'destructive',
};

const statusColors: Record<string, string> = {
  DRAFT: 'outline',
  ACTIVE: 'success',
  ON_HOLD: 'warning',
  CLOSED: 'default',
  ARCHIVED: 'outline',
  // lowercase variants
  open: 'success',
  closed: 'default',
  draft: 'outline',
  active: 'success',
  on_hold: 'warning',
  archived: 'outline',
};

export function CaseCard({ case_, onDelete }: Props) {
  const navigate = useNavigate();

  return (
    <Card 
      className="cursor-pointer hover:border-primary/50 transition-colors group"
      onClick={() => navigate(`/cases/${case_.id}`)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <CardTitle className="text-base mb-2 truncate">{case_.title}</CardTitle>
            <p className="text-xs text-muted-foreground">{case_.case_number}</p>
          </div>
          <div className="flex flex-col gap-1 items-end flex-shrink-0">
            <Badge variant={(priorityColors[case_.priority] || 'default') as any}>{case_.priority}</Badge>
            <Badge variant={(statusColors[case_.status] || 'default') as any}>{case_.status}</Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {case_.description && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{case_.description}</p>
        )}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{case_.case_type}</span>
          <div className="flex items-center gap-2">
            <span>{formatDate(case_.created_at)}</span>
            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={onDelete}
              >
                <Trash2 className="h-3.5 w-3.5 text-destructive" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
