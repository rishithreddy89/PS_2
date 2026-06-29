import { useParams } from 'react-router-dom';
import { useCase, useRecommendations, useUpdateCase, useDeleteCase } from '@/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RecommendationCard } from '@/components/RecommendationCard';
import { formatDate } from '@/lib/utils';
import { ArrowLeft, Upload, Play, CheckSquare, Trash2, Edit, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useState } from 'react';
import { DocumentUpload } from '@/components/cases/DocumentUpload';
import { AnalysisProgress } from '@/components/cases/AnalysisProgress';
import { ReviewModal } from '@/components/cases/ReviewModal';
import { DocumentList } from '@/components/cases/DocumentList';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { RiskGauge } from '@/components/cases/dashboard/RiskGauge';
import { TimelineView } from '@/components/cases/dashboard/TimelineView';
import { EvidenceMatrix } from '@/components/cases/dashboard/EvidenceMatrix';
import { sortRecommendations } from '@/lib/utils';

export function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data: case_, isLoading, refetch } = useCase(id!);
  const { data: recommendations, refetch: refetchRecommendations } = useRecommendations(id);
  const updateCase = useUpdateCase();
  const deleteCase = useDeleteCase();
  
  const [uploadOpen, setUploadOpen] = useState(false);
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState<any>(null);
  const [initialDecision, setInitialDecision] = useState<string>('');

  // Edit form state
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    case_type: '',
    jurisdiction: '',
    client_name: '',
  });

  const handleReviewClick = (rec: any, decision: string = '') => {
    setSelectedRecommendation(rec);
    setInitialDecision(decision);
    setReviewOpen(true);
  };

  const handleEditOpen = () => {
    if (case_) {
      setEditForm({
        title: case_.title || '',
        description: case_.description || '',
        case_type: case_.case_type || '',
        jurisdiction: case_.jurisdiction || '',
        client_name: (case_ as any).client_name || '',
      });
      setEditOpen(true);
    }
  };

  const handleEditSave = async () => {
    try {
      await updateCase.mutateAsync({ id: id!, data: editForm });
      toast({ title: 'Case updated', variant: 'success' });
      setEditOpen(false);
      refetch();
    } catch {
      // Error handled by interceptor
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this case? This action cannot be undone.')) return;
    try {
      await deleteCase.mutateAsync(id!);
      toast({ title: 'Case deleted', variant: 'success' });
      navigate('/cases');
    } catch {
      // Error handled by interceptor
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await updateCase.mutateAsync({ id: id!, data: { status: newStatus } });
      toast({ title: `Status updated to ${newStatus}`, variant: 'success' });
      refetch();
    } catch {
      // Error handled by interceptor
    }
  };

  const handlePriorityChange = async (newPriority: string) => {
    try {
      await updateCase.mutateAsync({ id: id!, data: { priority: newPriority } });
      toast({ title: `Priority updated to ${newPriority}`, variant: 'success' });
      refetch();
    } catch {
      // Error handled by interceptor
    }
  };

  if (isLoading) return <div className="p-6 flex items-center gap-2"><Loader2 className="h-5 w-5 animate-spin" /> Loading...</div>;
  if (!case_) return <div className="p-6">Case not found</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/cases')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Cases
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleEditOpen}>
            <Edit className="h-4 w-4 mr-2" /> Edit
          </Button>
          <Button variant="outline" size="sm" onClick={handleDelete} className="text-destructive hover:text-destructive">
            <Trash2 className="h-4 w-4 mr-2" /> Delete
          </Button>
        </div>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">{case_.title}</h1>
          <p className="text-muted-foreground">{case_.case_number}</p>
        </div>
        <div className="flex gap-2 items-center">
          <Select value={case_.priority} onValueChange={handlePriorityChange}>
            <SelectTrigger className="w-[120px] h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="urgent">Urgent</SelectItem>
              <SelectItem value="LOW">LOW</SelectItem>
              <SelectItem value="MEDIUM">MEDIUM</SelectItem>
              <SelectItem value="HIGH">HIGH</SelectItem>
              <SelectItem value="CRITICAL">CRITICAL</SelectItem>
            </SelectContent>
          </Select>
          <Select value={case_.status} onValueChange={handleStatusChange}>
            <SelectTrigger className="w-[120px] h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="ACTIVE">Active</SelectItem>
              <SelectItem value="ON_HOLD">On Hold</SelectItem>
              <SelectItem value="CLOSED">Closed</SelectItem>
              <SelectItem value="ARCHIVED">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Case Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Description</p>
                <p className="text-sm text-muted-foreground mt-1">{case_.description || 'No description'}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium">Type</p>
                  <p className="text-muted-foreground">{case_.case_type}</p>
                </div>
                <div>
                  <p className="font-medium">Jurisdiction</p>
                  <p className="text-muted-foreground">{case_.jurisdiction || 'N/A'}</p>
                </div>
                <div>
                  <p className="font-medium">Created</p>
                  <p className="text-muted-foreground">{formatDate(case_.created_at)}</p>
                </div>
                <div>
                  <p className="font-medium">Filing Date</p>
                  <p className="text-muted-foreground">{case_.filing_date ? formatDate(case_.filing_date) : 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {case_.meta_data?.evidence_matrix && (
            <EvidenceMatrix 
              evidence={case_.meta_data.evidence_matrix}
              contradictions={case_.meta_data.contradictions}
              missingEvidence={case_.meta_data.missing_evidence}
            />
          )}

          {case_.meta_data?.timeline && (
            <TimelineView events={case_.meta_data.timeline} />
          )}

          <DocumentList caseId={id!} />

          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recommendations && recommendations.length > 0 ? (
                sortRecommendations(recommendations).map((rec: any) => (
                  <div key={rec.id}>
                    <RecommendationCard 
                      recommendation={rec} 
                      onModifyClick={() => handleReviewClick(rec, 'modified')}
                      onReviewClick={() => handleReviewClick(rec)}
                    />
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">No recommendations yet. Upload documents and run analysis to generate.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {case_.meta_data?.risk_assessment && (
            <RiskGauge scores={case_.meta_data.risk_assessment} />
          )}

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button 
                className="w-full" 
                variant="outline"
                onClick={() => setUploadOpen(true)}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Document
              </Button>
              <Button 
                className="w-full" 
                variant="outline"
                onClick={() => setAnalysisOpen(true)}
              >
                <Play className="h-4 w-4 mr-2" />
                Generate Analysis
              </Button>
              <Button 
                className="w-full" 
                variant="outline"
                disabled={!recommendations || recommendations.length === 0}
                onClick={() => recommendations && handleReviewClick(recommendations[0])}
              >
                <CheckSquare className="h-4 w-4 mr-2" />
                Request Review
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <DocumentUpload 
        caseId={id!} 
        open={uploadOpen} 
        onClose={() => setUploadOpen(false)}
        onSuccess={() => refetch()}
      />

      <AnalysisProgress 
        caseId={id!}
        open={analysisOpen}
        onClose={() => setAnalysisOpen(false)}
        onComplete={() => {
          refetch();
          refetchRecommendations();
        }}
      />

      <ReviewModal 
        recommendation={selectedRecommendation}
        caseData={case_}
        open={reviewOpen}
        onClose={() => setReviewOpen(false)}
        initialDecision={initialDecision}
        onSuccess={() => {
          refetchRecommendations();
        }}
      />

      {/* Edit Case Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Case</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Title</Label>
              <Input
                value={editForm.title}
                onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={editForm.description}
                onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Case Type</Label>
                <Select value={editForm.case_type} onValueChange={(v) => setEditForm(prev => ({ ...prev, case_type: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="civil">Civil</SelectItem>
                    <SelectItem value="criminal">Criminal</SelectItem>
                    <SelectItem value="corporate">Corporate</SelectItem>
                    <SelectItem value="family">Family</SelectItem>
                    <SelectItem value="property">Property</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Jurisdiction</Label>
                <Input
                  value={editForm.jurisdiction}
                  onChange={(e) => setEditForm(prev => ({ ...prev, jurisdiction: e.target.value }))}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
              <Button onClick={handleEditSave} disabled={updateCase.isPending}>
                {updateCase.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
