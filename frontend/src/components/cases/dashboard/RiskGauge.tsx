import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RiskScores } from '@/types';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

export function RiskGauge({ scores }: { scores?: RiskScores }) {
  if (!scores) return null;

  const getRiskColor = (score: number, invert = false) => {
    const s = invert ? 100 - score : score;
    if (s > 75) return 'text-destructive';
    if (s > 40) return 'text-amber-500';
    return 'text-emerald-500';
  };

  const ScoreBar = ({ label, score, invert = false }: { label: string, score: number, invert?: boolean }) => (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-muted-foreground">{label}</span>
        <span className={`font-bold ${getRiskColor(score, invert)}`}>{score}%</span>
      </div>
      <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${
            invert ? (score < 25 ? 'bg-destructive' : score < 60 ? 'bg-amber-500' : 'bg-emerald-500') 
                   : (score > 75 ? 'bg-destructive' : score > 40 ? 'bg-amber-500' : 'bg-emerald-500')
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );

  const getOverallRisk = () => {
    const avg = (scores.litigation_risk + (100 - scores.evidence_strength) + scores.urgency) / 3;
    if (avg > 70) return { icon: ShieldAlert, text: "High Risk", color: "text-destructive" };
    if (avg > 40) return { icon: Shield, text: "Moderate Risk", color: "text-amber-500" };
    return { icon: ShieldCheck, text: "Low Risk", color: "text-emerald-500" };
  };

  const overall = getOverallRisk();
  const Icon = overall.icon;

  return (
    <Card className="h-full border-t-4 border-t-primary">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Risk Assessment</CardTitle>
        <div className={`flex items-center gap-1 font-bold ${overall.color}`}>
          <Icon className="h-5 w-5" />
          <span>{overall.text}</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground mb-4">{scores.explanation}</p>
        
        <ScoreBar label="Litigation Risk" score={scores.litigation_risk} />
        <ScoreBar label="Evidence Strength" score={scores.evidence_strength} invert={true} />
        <ScoreBar label="Employer Defense" score={scores.employer_defense} invert={true} />
        <ScoreBar label="Urgency" score={scores.urgency} />
        <ScoreBar label="Settlement Probability" score={scores.settlement_probability} invert={true} />
      </CardContent>
    </Card>
  );
}
