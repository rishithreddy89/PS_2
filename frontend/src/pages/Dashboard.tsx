import { useCases, useRecommendations, useMemories } from '@/hooks/useApi';
import { CaseCard } from '@/components/CaseCard';
import { RecommendationCard } from '@/components/RecommendationCard';
import { MemoryTimeline } from '@/components/MemoryTimeline';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { sortRecommendations } from '@/lib/utils';

export function Dashboard() {
  const navigate = useNavigate();
  const { data: cases, isLoading: casesLoading } = useCases();
  const { data: recommendations, isLoading: recsLoading } = useRecommendations();
  const { data: memories, isLoading: memsLoading } = useMemories();

  // Ensure cases is an array
  const casesArray = Array.isArray(cases) ? cases : [];
  const recsArray = Array.isArray(recommendations) ? recommendations : [];
  const memsArray = Array.isArray(memories) ? memories : [];

  const stats = [
    { label: 'Active Cases', value: casesArray.filter(c => c.status === 'open' || c.status === 'ACTIVE').length, icon: TrendingUp, color: 'text-blue-400' },
    { label: 'Pending Recommendations', value: recsArray.filter(r => r.status === 'pending' || r.status === 'PENDING').length, icon: AlertCircle, color: 'text-yellow-400' },
    { label: 'Approved Actions', value: recsArray.filter(r => r.status === 'approved' || r.status === 'APPROVED').length, icon: CheckCircle, color: 'text-green-400' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button onClick={() => navigate('/cases/new')}>
          <Plus className="h-4 w-4 mr-2" />
          New Case
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Cases</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {casesLoading ? (
                <p className="text-sm text-muted-foreground text-center py-8">Loading...</p>
              ) : casesArray.length > 0 ? (
                casesArray.slice(0, 3).map(case_ => <CaseCard key={case_.id} case_={case_} />)
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">No cases found</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Recommendations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recsLoading ? (
                <p className="text-sm text-muted-foreground text-center py-8">Loading...</p>
              ) : recsArray.length > 0 ? (
                sortRecommendations(recsArray).map(rec => <RecommendationCard key={rec.id} recommendation={rec} />)
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">No recommendations</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          {!memsLoading && memsArray.length > 0 && <MemoryTimeline memories={memsArray.slice(0, 10)} />}
        </div>
      </div>
    </div>
  );
}
