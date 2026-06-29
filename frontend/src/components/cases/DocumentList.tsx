import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Trash2, Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { documentsApi } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface Document {
  id: string;
  filename: string;
  size: number;
  type: string;
  status: string;
  created_at: string;
}

interface DocumentListProps {
  caseId: string;
}

export function DocumentList({ caseId }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const { toast } = useToast();

  const loadDocuments = async () => {
    try {
      const response = await documentsApi.list(caseId);
      setDocuments(response.data.documents || []);
    } catch {
      // Error handled by interceptor on non-404 errors
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000);
    return () => clearInterval(interval);
  }, [caseId]);

  const deleteDocument = async (docId: string) => {
    if (!confirm('Delete this document?')) return;

    setDeletingId(docId);
    try {
      await documentsApi.delete(docId);
      toast({ title: 'Document deleted', variant: 'success' });
      loadDocuments();
    } catch {
      // Error handled by interceptor
    } finally {
      setDeletingId(null);
    }
  };

  const downloadDocument = (docId: string) => {
    const url = documentsApi.download(docId);
    window.open(url, '_blank');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'destructive';
      case 'uploaded': return 'outline';
      default: return 'outline';
    }
  };

  if (loading && documents.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 flex items-center justify-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm text-muted-foreground">Loading documents...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents ({documents.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {documents.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No documents uploaded</p>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {(doc.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <Badge variant={getStatusColor(doc.status) as any}>
                    {doc.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-1 ml-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => downloadDocument(doc.id)}
                    title="Download"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteDocument(doc.id)}
                    disabled={deletingId === doc.id}
                    title="Delete"
                  >
                    {deletingId === doc.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4 text-destructive" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
