import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, Edit } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ReviewModalProps {
  recommendation: any;
  caseData?: any;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialDecision?: string;
}

export function ReviewModal({ recommendation, caseData, open, onClose, onSuccess, initialDecision = '' }: ReviewModalProps) {
  const [decision, setDecision] = useState<string>(initialDecision);
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const [editedTitle, setEditedTitle] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [editedReasoning, setEditedReasoning] = useState('');
  const [editedPriority, setEditedPriority] = useState('');

  useEffect(() => {
    if (recommendation) {
      setEditedTitle(recommendation.title || '');
      setEditedDescription(recommendation.description || recommendation.recommended_action || '');
      setEditedReasoning(recommendation.reasoning || '');
      setEditedPriority(recommendation.priority || 'MEDIUM');
    }
  }, [recommendation, open]);

  useEffect(() => {
    if (open) {
      setDecision(initialDecision);
    }
  }, [open, initialDecision]);

  const submitReview = async () => {
    if (!decision) {
      toast({
        title: 'Error',
        description: 'Please select a decision',
        variant: 'destructive',
      });
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/review/recommendations/${recommendation.id}/review`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            decision,
            comments,
            reviewer_id: 'current-user',
            modified_content: decision === 'modified' ? {
              title: editedTitle,
              description: editedDescription,
              reasoning: editedReasoning,
              priority: editedPriority,
            } : undefined
          }),
        }
      );

      if (!response.ok) throw new Error('Review submission failed');

      toast({
        title: 'Success',
        description: 'Review submitted successfully',
      });

      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to submit review',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (!recommendation) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle>Review Recommendation</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">{recommendation.title}</h3>
            <div className="flex gap-2 mb-3">
              <Badge>{recommendation.action_type || recommendation.recommendation_type || 'Next Best Action'}</Badge>
              <Badge variant="outline">
                Confidence: {((recommendation.confidence_score || 0.8) * 100).toFixed(0)}%
              </Badge>
              <Badge variant="outline">{recommendation.priority}</Badge>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium mb-1">Recommended Action / Description</p>
            <p className="text-sm text-muted-foreground">{recommendation.description || recommendation.recommended_action}</p>
          </div>

          <div>
            <p className="text-sm font-medium mb-1">Reasoning</p>
            <p className="text-sm text-muted-foreground">{recommendation.reasoning}</p>
          </div>

          {/* CASE-LEVEL METRICS */}
          {caseData && caseData.meta_data && (
            <div className="space-y-6 border-t pt-6 mt-6">
              <h3 className="text-lg font-bold text-foreground">Case-Level Context & Analysis</h3>
              
              {/* EXECUTIVE OPINION */}
              {caseData.meta_data.executive_opinion && (
                <div className="space-y-3 bg-muted/20 p-4 rounded-lg border border-border">
                  <h4 className="font-semibold text-primary">Executive Opinion</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong className="block text-muted-foreground">Overall Assessment</strong>
                      <p>{caseData.meta_data.executive_opinion.overall_assessment}</p>
                    </div>
                    <div>
                      <strong className="block text-muted-foreground">Case Strength</strong>
                      <p>{caseData.meta_data.executive_opinion.case_strength}</p>
                    </div>
                    <div className="md:col-span-2">
                      <strong className="block text-muted-foreground">Primary Recommendation</strong>
                      <p>{caseData.meta_data.executive_opinion.primary_recommendation}</p>
                    </div>
                    <div>
                      <strong className="block text-muted-foreground">Strongest Evidence</strong>
                      <p>{caseData.meta_data.executive_opinion.strongest_evidence}</p>
                    </div>
                    <div>
                      <strong className="block text-muted-foreground">Weakest Evidence</strong>
                      <p>{caseData.meta_data.executive_opinion.weakest_evidence}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* LITIGATION RISK */}
              {caseData.meta_data.litigation_risk && (
                <div className="space-y-3 bg-destructive/5 p-4 rounded-lg border border-destructive/20">
                  <h4 className="font-semibold text-destructive">Litigation Risk</h4>
                  <p className="text-sm text-destructive/90 mb-3">{caseData.meta_data.litigation_risk.explanation}</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                    <div className="bg-background/50 p-2 rounded border border-destructive/10">
                      <strong className="block text-xs text-muted-foreground uppercase">Success Prob.</strong>
                      <span className="font-medium text-destructive">{caseData.meta_data.litigation_risk.probability_of_success}</span>
                    </div>
                    <div className="bg-background/50 p-2 rounded border border-destructive/10">
                      <strong className="block text-xs text-muted-foreground uppercase">Settlement Prob.</strong>
                      <span className="font-medium text-destructive">{caseData.meta_data.litigation_risk.settlement_probability}</span>
                    </div>
                    <div className="bg-background/50 p-2 rounded border border-destructive/10">
                      <strong className="block text-xs text-muted-foreground uppercase">Discovery Risk</strong>
                      <span className="font-medium text-destructive">{caseData.meta_data.litigation_risk.discovery_risk}</span>
                    </div>
                    <div className="bg-background/50 p-2 rounded border border-destructive/10">
                      <strong className="block text-xs text-muted-foreground uppercase">Evidence Risk</strong>
                      <span className="font-medium text-destructive">{caseData.meta_data.litigation_risk.evidence_risk}</span>
                    </div>
                    <div className="bg-background/50 p-2 rounded border border-destructive/10">
                      <strong className="block text-xs text-muted-foreground uppercase">Appeal Risk</strong>
                      <span className="font-medium text-destructive">{caseData.meta_data.litigation_risk.appeal_risk}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* ACTION PLAN */}
              {caseData.meta_data.action_plan && caseData.meta_data.action_plan.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground">Strategic Action Plan</h4>
                  <div className="space-y-2">
                    {caseData.meta_data.action_plan.map((step: any, idx: number) => (
                      <div key={idx} className="flex gap-4 p-3 rounded-lg border border-border bg-card">
                        <div className="font-bold text-primary w-24 shrink-0">{step.timing}</div>
                        <div className="text-sm text-muted-foreground">{step.action}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* CONTRADICTION ANALYSIS */}
              {caseData.meta_data.contradiction_analysis && caseData.meta_data.contradiction_analysis.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-amber-600 dark:text-amber-500">Contradiction Analysis</h4>
                  <div className="grid gap-3">
                    {caseData.meta_data.contradiction_analysis.map((contra: any, idx: number) => (
                      <div key={idx} className="bg-amber-500/10 p-3 rounded-md border border-amber-500/20 text-sm">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                          <div>
                            <strong className="block text-amber-700/80 dark:text-amber-400/80 text-xs uppercase">Employer Claim</strong>
                            <p className="text-amber-900 dark:text-amber-200">{contra.employer_claim}</p>
                          </div>
                          <div>
                            <strong className="block text-amber-700/80 dark:text-amber-400/80 text-xs uppercase">Evidence</strong>
                            <p className="text-amber-900 dark:text-amber-200">{contra.evidence}</p>
                          </div>
                        </div>
                        <div className="pt-2 border-t border-amber-500/20">
                          <strong className="text-amber-700/80 dark:text-amber-400/80 text-xs uppercase">Legal Significance: </strong>
                          <span className="text-amber-900 dark:text-amber-200">{contra.legal_significance}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* FULL EVIDENCE LIST */}
              {caseData.meta_data.evidence_matrix && caseData.meta_data.evidence_matrix.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground">Full Evidence Matrix</h4>
                  <div className="max-h-60 overflow-y-auto rounded-md border border-border">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs uppercase bg-muted/50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 font-medium">Fact</th>
                          <th className="px-4 py-2 font-medium">Status</th>
                          <th className="px-4 py-2 font-medium">Importance</th>
                          <th className="px-4 py-2 font-medium">Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {caseData.meta_data.evidence_matrix.map((ev: any, idx: number) => (
                          <tr key={idx} className="border-b last:border-0 border-border bg-card hover:bg-muted/30">
                            <td className="px-4 py-2">{ev.fact}</td>
                            <td className="px-4 py-2">
                              <Badge variant="outline" className="text-[10px]">{ev.status}</Badge>
                            </td>
                            <td className="px-4 py-2">
                              <Badge variant="outline" className="text-[10px]">{ev.importance}</Badge>
                            </td>
                            <td className="px-4 py-2 text-xs text-muted-foreground">{ev.source}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* PLANNER EXECUTION SUMMARY */}
              {caseData.meta_data.planner_execution && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground">Execution Summary</h4>
                  <div className="bg-muted p-3 rounded-md text-sm font-mono overflow-x-auto">
                    <pre>{JSON.stringify(caseData.meta_data.planner_execution, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="border-t pt-6">
            <p className="text-sm font-medium mb-3">Your Decision</p>
            <div className="flex gap-2">
              <Button
                variant={decision === 'approved' ? 'default' : 'outline'}
                onClick={() => setDecision('approved')}
                className="flex-1"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </Button>
              <Button
                variant={decision === 'rejected' ? 'default' : 'outline'}
                onClick={() => setDecision('rejected')}
                className="flex-1"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
              <Button
                variant={decision === 'modified' ? 'default' : 'outline'}
                onClick={() => setDecision('modified')}
                className="flex-1"
              >
                <Edit className="h-4 w-4 mr-2" />
                Modify
              </Button>
            </div>
          </div>

          {decision === 'modified' && (
            <div className="border border-orange-500/20 bg-orange-500/5 rounded-lg p-4 space-y-4">
              <h4 className="font-semibold text-sm text-orange-600">Modify Recommendation Details</h4>
              <div>
                <label className="text-xs font-medium block mb-1">Title</label>
                <input
                  type="text"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs font-medium block mb-1">Description / Recommended Action</label>
                <Textarea
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  rows={3}
                />
              </div>
              <div>
                <label className="text-xs font-medium block mb-1">Reasoning</label>
                <Textarea
                  value={editedReasoning}
                  onChange={(e) => setEditedReasoning(e.target.value)}
                  rows={3}
                />
              </div>
              <div>
                <label className="text-xs font-medium block mb-1">Priority</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={editedPriority}
                  onChange={(e) => setEditedPriority(e.target.value)}
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>
          )}

          <div>
            <p className="text-sm font-medium mb-2">Comments</p>
            <Textarea
              placeholder="Add your comments here..."
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={4}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={submitReview} disabled={!decision || submitting}>
              {submitting ? 'Submitting...' : 'Submit Review'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
