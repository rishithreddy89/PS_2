import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Recommendation, EvidenceCitation } from '@/types';
import { CheckCircle, XCircle, Edit, ChevronDown, CheckSquare, ShieldAlert, FileText, Scale, GitMerge } from 'lucide-react';
import { useState } from 'react';
import { useCreateFeedback } from '@/hooks/useApi';
import { useToast } from '@/hooks/use-toast';

interface Props {
  recommendation: Recommendation;
  onModifyClick?: () => void;
  onReviewClick?: () => void;
}

const priorityColors = {
  CRITICAL: 'destructive',
  HIGH: 'warning',
  MEDIUM: 'default',
  LOW: 'outline',
} as const;

const formatDisplayValue = (value: unknown, fallback = 'Not available'): string => {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }

  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map((item) => formatDisplayValue(item, fallback)).join(', ');
  }

  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return String(
      record.reason ??
      record.reason_it_applies ??
      record.description ??
      record.title ??
      record.statute ??
      record.case_name ??
      record.argument ??
      record.strategy ??
      record.status ??
      JSON.stringify(record)
    );
  }

  return fallback;
};

export function RecommendationCard({ recommendation, onModifyClick, onReviewClick }: Props) {
  const [expanded, setExpanded] = useState(false);
  const createFeedback = useCreateFeedback();
  const { toast } = useToast();

  const handleApprove = () => {
    createFeedback.mutate(
      { recommendation_id: recommendation.id, feedback_type: 'APPROVAL', content: 'Approved' },
      {
        onSuccess: () => {
          toast({
            title: 'Approved',
            description: 'Recommendation has been approved successfully.',
          });
        },
      }
    );
  };

  const handleReject = () => {
    createFeedback.mutate(
      { recommendation_id: recommendation.id, feedback_type: 'REJECTION', content: 'Rejected' },
      {
        onSuccess: () => {
          toast({
            title: 'Rejected',
            description: 'Recommendation has been marked as rejected.',
            variant: 'destructive',
          });
        },
      }
    );
  };

  return (
    <Card className="border-l-4 border-l-primary/60 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={(priorityColors as any)[recommendation.priority.toUpperCase()] || 'default'} title={recommendation.priority_explanation}>
                {recommendation.priority.toUpperCase()}
              </Badge>
              <Badge variant="outline" title={recommendation.confidence_explanation}>
                {Math.round((recommendation.confidence_score || 0.8) * 100)}% Confident
              </Badge>
              {recommendation.evidence_completeness_score && (
                <Badge variant="outline" className="text-muted-foreground">
                  Evidence Score: {recommendation.evidence_completeness_score}
                </Badge>
              )}
              {recommendation.status && (
                <Badge variant={
                  recommendation.status === 'APPROVED' ? 'success' :
                  recommendation.status === 'REJECTED' ? 'destructive' :
                  recommendation.status === 'IMPLEMENTED' ? 'default' : 'outline'
                }>
                  {recommendation.status}
                </Badge>
              )}
            </div>
            <CardTitle className="text-lg leading-tight">{recommendation.title}</CardTitle>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 hover:bg-muted rounded-full transition-colors"
            aria-label={expanded ? 'Collapse recommendation details' : 'Expand recommendation details'}
            title={expanded ? 'Collapse recommendation details' : 'Expand recommendation details'}
          >
            <ChevronDown className={`h-5 w-5 text-muted-foreground transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-foreground mb-4">{recommendation.description}</p>
        
        {expanded && (
          <div className="space-y-6 text-sm mt-4 border-t pt-4">
            
            {/* EXECUTIVE SUMMARY */}
            <div className="space-y-2">
              <h3 className="font-semibold text-foreground">Executive Summary</h3>
              {recommendation.executive_summary ? (
                <p className="text-muted-foreground">{recommendation.executive_summary}</p>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* REASONING */}
            <div className="space-y-2">
              <h3 className="font-semibold text-foreground">Detailed Reasoning</h3>
              {recommendation.reasoning ? (
                <p className="text-muted-foreground">{recommendation.reasoning}</p>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* JUSTIFICATION SECTION */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-primary font-semibold">
                <Scale className="h-4 w-4" />
                <h3>Legal Justification</h3>
              </div>
              {recommendation.justification ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-muted/30 p-3 rounded-md">
                    <strong className="text-foreground block mb-1">Why is this appropriate?</strong>
                    <p className="text-muted-foreground">{recommendation.justification.why_appropriate || 'Not available'}</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-md">
                    <strong className="text-foreground block mb-1">Why act now?</strong>
                    <p className="text-muted-foreground">{recommendation.justification.why_now || 'Not available'}</p>
                  </div>
                  {recommendation.justification.weakening_facts && recommendation.justification.weakening_facts.length > 0 && (
                    <div className="bg-destructive/5 border border-destructive/10 p-3 rounded-md md:col-span-2">
                      <strong className="text-destructive/90 block mb-1">Weakening Facts:</strong>
                      <ul className="list-disc list-inside text-destructive/80 space-y-1">
                        {recommendation.justification.weakening_facts.map((fact, idx) => (
                          <li key={idx}>{formatDisplayValue(fact)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* EVIDENCE TRACEABILITY */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-500 font-semibold">
                <FileText className="h-4 w-4" />
                <h3>Traceable Evidence</h3>
              </div>
              {recommendation.supporting_evidence && recommendation.supporting_evidence.length > 0 ? (
                <div className="grid grid-cols-1 gap-2">
                  {recommendation.supporting_evidence.map((ev: any, idx: number) => {
                    if (typeof ev === 'string') {
                      return (
                        <div key={idx} className="bg-emerald-50/50 dark:bg-emerald-950/20 p-2 rounded border border-emerald-100 dark:border-emerald-900">
                          <p className="text-emerald-800 dark:text-emerald-300">{ev}</p>
                        </div>
                      );
                    }
                    if (!ev || typeof ev !== 'object') {
                      return (
                        <div key={idx} className="bg-emerald-50/50 dark:bg-emerald-950/20 p-2 rounded border border-emerald-100 dark:border-emerald-900">
                          <p className="text-emerald-800 dark:text-emerald-300">{formatDisplayValue(ev)}</p>
                        </div>
                      );
                    }

                    const evidence = ev as EvidenceCitation;
                    const evidenceTitle = evidence.document || formatDisplayValue(ev, 'Evidence item');
                    const evidenceQuote = evidence.quote || formatDisplayValue(ev, 'Not available');

                    return (
                      <div key={idx} className="bg-emerald-50/50 dark:bg-emerald-950/20 p-3 rounded border border-emerald-100 dark:border-emerald-900 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-emerald-900 dark:text-emerald-200">{evidenceTitle}</span>
                          <Badge variant="outline" className="text-xs bg-white dark:bg-black/20 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800">
                            Strength: {evidence.strength || 'Unknown'}
                          </Badge>
                        </div>
                        <p className="italic text-emerald-800 dark:text-emerald-300 border-l-2 border-emerald-300 dark:border-emerald-700 pl-2">
                          "{evidenceQuote}"
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* MISSING EVIDENCE */}
            <div className="space-y-2">
              <h3 className="font-semibold text-amber-600 dark:text-amber-500">Missing Evidence</h3>
              {recommendation.missing_evidence && recommendation.missing_evidence.length > 0 ? (
                <ul className="list-disc list-inside text-amber-700 dark:text-amber-400">
                  {recommendation.missing_evidence.map((ev, i) => <li key={i}>{formatDisplayValue(ev)}</li>)}
                </ul>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* APPLICABLE LAWS */}
            <div className="space-y-2">
              <h3 className="font-semibold text-foreground">Applicable Laws</h3>
              {recommendation.detailed_applicable_laws && recommendation.detailed_applicable_laws.length > 0 ? (
                <div className="space-y-3">
                  {recommendation.detailed_applicable_laws.map((law, idx) => (
                    <div key={idx} className="bg-muted/20 p-3 rounded-md border border-border">
                      <strong className="block text-primary">{law.statute}</strong>
                      <p className="text-sm text-muted-foreground mt-1">{law.why_it_applies}</p>
                      <div className="mt-2 flex gap-2">
                        <Badge variant="outline" className="text-xs">Jurisdiction: {law.jurisdiction}</Badge>
                        <Badge variant="outline" className="text-xs">Confidence: {law.confidence}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : recommendation.applicable_laws && recommendation.applicable_laws.length > 0 ? (
                <ul className="list-disc list-inside text-muted-foreground">
                  {recommendation.applicable_laws.map((law, i) => <li key={i}>{formatDisplayValue(law)}</li>)}
                </ul>
              ) : recommendation.meta_data?.applicable_laws && recommendation.meta_data.applicable_laws.length > 0 ? (
                <ul className="list-disc list-inside text-muted-foreground">
                  {recommendation.meta_data.applicable_laws.map((law: unknown, i: number) => <li key={i}>{formatDisplayValue(law)}</li>)}
                </ul>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* RELEVANT PRECEDENTS */}
            <div className="space-y-2">
              <h3 className="font-semibold text-foreground">Relevant Precedents</h3>
              {recommendation.detailed_precedents && recommendation.detailed_precedents.length > 0 ? (
                <div className="space-y-3">
                  {recommendation.detailed_precedents.map((prec, idx) => (
                    <div key={idx} className="bg-muted/20 p-3 rounded-md border border-border">
                      <strong className="block text-primary">{prec.case_name} ({prec.year}) - {prec.court}</strong>
                      <p className="text-sm text-muted-foreground mt-1">{prec.reason_it_applies}</p>
                      <div className="mt-2">
                        <Badge variant="outline" className="text-xs">Similarity: {prec.similarity_score}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : recommendation.relevant_precedents && recommendation.relevant_precedents.length > 0 ? (
                <ul className="list-disc list-inside text-muted-foreground">
                  {recommendation.relevant_precedents.map((prec, i) => <li key={i}>{formatDisplayValue(prec)}</li>)}
                </ul>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* LEGAL RISKS */}
            <div className="space-y-2">
              <h3 className="font-semibold text-destructive">Legal Risks</h3>
              {recommendation.legal_risks && recommendation.legal_risks.length > 0 ? (
                <ul className="list-disc list-inside text-destructive/80">
                  {recommendation.legal_risks.map((risk, i) => <li key={i}>{formatDisplayValue(risk)}</li>)}
                </ul>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* COUNTERARGUMENTS */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-destructive font-semibold">
                <ShieldAlert className="h-4 w-4" />
                <h3>Opposing Counsel Arguments</h3>
              </div>
              {recommendation.counterarguments && recommendation.counterarguments.length > 0 ? (
                <div className="space-y-2">
                  {recommendation.counterarguments.map((arg, idx) => (
                    <div key={idx} className="bg-destructive/5 border border-destructive/10 p-3 rounded-md">
                      <div className="flex justify-between items-start mb-2">
                        <strong className="text-destructive/90">{arg.argument}</strong>
                        <Badge variant="outline" className="text-xs text-destructive/80 border-destructive/30">
                          Success Likelihood: {arg.likelihood_of_success}
                        </Badge>
                      </div>
                      {arg.supporting_evidence && arg.supporting_evidence.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-semibold text-muted-foreground uppercase">Their Evidence:</span>
                          <ul className="list-disc list-inside text-muted-foreground text-xs mt-1">
                            {arg.supporting_evidence.map((ev, i) => <li key={i}>{formatDisplayValue(ev)}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* ALTERNATIVE STRATEGIES */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-semibold">
                <GitMerge className="h-4 w-4" />
                <h3>Alternative Strategies</h3>
              </div>
              {recommendation.alternative_strategies && recommendation.alternative_strategies.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {recommendation.alternative_strategies.map((alt, idx) => (
                    <div key={idx} className="border border-blue-100 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20 p-3 rounded-md">
                      <strong className="block text-blue-800 dark:text-blue-300 mb-1">{alt.strategy}</strong>
                      <p className="text-muted-foreground text-xs mb-2">When to choose: {alt.when_to_choose}</p>
                      
                      {alt.advantages && alt.advantages.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-500 uppercase">Advantages:</span>
                          <ul className="list-disc list-inside text-emerald-700/80 dark:text-emerald-400/80 text-xs mt-1">
                            {alt.advantages.map((adv, i) => <li key={i}>{formatDisplayValue(adv)}</li>)}
                          </ul>
                        </div>
                      )}
                      
                      {alt.disadvantages && alt.disadvantages.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-semibold text-destructive/80 uppercase">Disadvantages:</span>
                          <ul className="list-disc list-inside text-destructive/70 text-xs mt-1">
                            {alt.disadvantages.map((dis, i) => <li key={i}>{formatDisplayValue(dis)}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
              )}
            </div>

            {/* NEXT BEST ACTIONS & EXPECTED OUTCOME */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="font-semibold text-foreground">Next Best Actions</h3>
                {recommendation.next_best_actions && recommendation.next_best_actions.length > 0 ? (
                  <ul className="list-decimal list-inside text-muted-foreground">
                    {recommendation.next_best_actions.map((action, i) => <li key={i}>{formatDisplayValue(action)}</li>)}
                  </ul>
                ) : (
                  <p className="text-muted-foreground italic">Not available from uploaded evidence</p>
                )}
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-foreground">Expected Outcome & Urgency</h3>
                <div className="bg-emerald-500/10 p-3 rounded-md space-y-2">
                  <div>
                    <strong className="text-emerald-700 dark:text-emerald-400">Outcome:</strong>
                    <p className="text-emerald-600 dark:text-emerald-500 mt-1">
                      {recommendation.expected_outcome || recommendation.meta_data?.expected_outcome || 'Not available from uploaded evidence'}
                    </p>
                  </div>
                  <div>
                    <strong className="text-emerald-700 dark:text-emerald-400">Urgency:</strong>
                    <p className="text-emerald-600 dark:text-emerald-500 mt-1">
                      {recommendation.urgency || 'Not available'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        )}
        
        <div className="flex gap-2 mt-4 pt-4 border-t border-border/50">
          <Button 
            size="sm" 
            onClick={handleApprove} 
            disabled={createFeedback.isPending || recommendation.status === 'APPROVED' || recommendation.status === 'REJECTED'}
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Approve
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleReject} 
            disabled={createFeedback.isPending || recommendation.status === 'APPROVED' || recommendation.status === 'REJECTED'}
          >
            <XCircle className="h-4 w-4 mr-1" />
            Reject
          </Button>
          <Button size="sm" variant="ghost" onClick={onModifyClick}>
            <Edit className="h-4 w-4 mr-1" />
            Modify
          </Button>
          {onReviewClick && (
            <Button size="sm" variant="outline" onClick={onReviewClick} className="ml-auto">
              <CheckSquare className="h-4 w-4 mr-1" />
              Review
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
