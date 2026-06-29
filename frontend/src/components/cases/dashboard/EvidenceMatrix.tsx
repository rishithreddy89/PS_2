import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EvidenceItem, Contradiction } from '@/types';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileText, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

export function EvidenceMatrix({ 
  evidence, 
  contradictions,
  missingEvidence
}: { 
  evidence?: EvidenceItem[],
  contradictions?: Contradiction[],
  missingEvidence?: string[]
}) {
  if (!evidence) return null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Evidence Matrix
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fact</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Reliability</TableHead>
                  <TableHead>Source</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {evidence.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium text-sm">{item.fact}</TableCell>
                    <TableCell>
                      {item.status.toLowerCase() === 'available' ? (
                        <span className="flex items-center gap-1 text-emerald-500 text-xs font-bold">
                          <CheckCircle2 className="h-3 w-3" /> Available
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-destructive text-xs font-bold">
                          <XCircle className="h-3 w-3" /> Missing
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        item.reliability.toLowerCase() === 'high' ? 'bg-emerald-500/10 text-emerald-500' :
                        item.reliability.toLowerCase() === 'medium' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-destructive/10 text-destructive'
                      }`}>
                        {item.reliability}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{item.source}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {contradictions && contradictions.length > 0 && (
        <Card className="border-l-4 border-l-destructive bg-destructive/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Detected Contradictions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {contradictions.map((c, idx) => (
                <div key={idx} className="space-y-2">
                  <p className="font-medium text-sm">{c.description}</p>
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span className="bg-background px-2 py-1 rounded border">Source A: {c.source_a}</span>
                    <span className="bg-background px-2 py-1 rounded border">Source B: {c.source_b}</span>
                  </div>
                  <p className="text-sm text-destructive">{c.impact}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {missingEvidence && missingEvidence.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <XCircle className="h-5 w-5 text-amber-500" />
              Missing Documents Needed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5 space-y-1">
              {missingEvidence.map((missing, idx) => (
                <li key={idx} className="text-sm">{missing}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
