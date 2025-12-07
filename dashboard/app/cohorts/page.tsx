'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCohorts, getCohortWallets } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Users, TrendingUp, ArrowRightLeft, Target, ChevronRight, Loader2 } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const COLORS = ['#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899'];

export default function CohortsPage() {
  const [selectedCohort, setSelectedCohort] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['cohorts'],
    queryFn: getCohorts,
  });

  const { data: cohortWallets, isLoading: walletsLoading } = useQuery({
    queryKey: ['cohortWallets', selectedCohort],
    queryFn: () => (selectedCohort ? getCohortWallets(selectedCohort, 50) : null),
    enabled: !!selectedCohort,
  });

  const cohorts = data?.cohorts || [];

  const chartData = cohorts.map((c, i) => ({
    name: (c.cohort_name || 'Unknown').replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    wallets: c.wallet_count || 0,
    volume: c.avg_volume_avax || 0,
    color: COLORS[i % COLORS.length],
  }));

  const getCohortIcon = (name: string) => {
    if (!name) return '👥';
    if (name.includes('whale') || name.includes('high')) return '🐋';
    if (name.includes('active') || name.includes('frequency')) return '⚡';
    if (name.includes('new') || name.includes('dormant')) return '🌱';
    if (name.includes('dex') || name.includes('trader')) return '📊';
    return '👥';
  };

  const getCohortColor = (name: string) => {
    if (!name) return 'from-orange-500/20 to-red-500/20 border-orange-500/30';
    if (name.includes('whale') || name.includes('high')) return 'from-blue-500/20 to-blue-600/20 border-blue-500/30';
    if (name.includes('active')) return 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30';
    if (name.includes('new')) return 'from-green-500/20 to-green-600/20 border-green-500/30';
    return 'from-orange-500/20 to-red-500/20 border-orange-500/30';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-12 w-12 animate-spin text-orange-400" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400">Failed to load cohorts. Check API connection.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Cohort Analysis</h1>
        <p className="text-slate-400 mt-1">
          {data?.total_cohorts || 0} cohorts detected via ML clustering
        </p>
      </div>

      {/* Cohort Cards */}
      {cohorts.length === 0 ? (
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-12 text-center">
            <Users className="h-12 w-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-400 mb-2">No Cohorts Found</h3>
            <p className="text-sm text-slate-500">
              Run the cohort detection to analyze wallet clusters.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cohorts.map((cohort) => (
              <Card
                key={cohort.cohort_name}
                className={`bg-gradient-to-br ${getCohortColor(cohort.cohort_name)} border cursor-pointer transition-all hover:scale-[1.02]`}
                onClick={() => setSelectedCohort(cohort.cohort_name)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-2xl">{getCohortIcon(cohort.cohort_name)}</span>
                        <h3 className="font-semibold text-lg capitalize">
                          {(cohort.cohort_name || 'Unknown').replace(/_/g, ' ')}
                        </h3>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div className="flex items-center gap-2 text-slate-300">
                          <Users className="h-4 w-4" />
                          <span>{(cohort.wallet_count || 0).toLocaleString()} wallets</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-300">
                          <TrendingUp className="h-4 w-4" />
                          <span>{(cohort.avg_volume_avax || 0).toFixed(2)} AVAX avg</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-300">
                          <ArrowRightLeft className="h-4 w-4" />
                          <span>{(cohort.avg_txs || 0).toFixed(0)} txs avg</span>
                        </div>
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-slate-400" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Distribution Chart */}
          {chartData.length > 0 && (
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle>Cohort Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis
                        dataKey="name"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                        tickLine={{ stroke: '#334155' }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis
                        tick={{ fill: '#94a3b8' }}
                        tickLine={{ stroke: '#334155' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          border: '1px solid #334155',
                          borderRadius: '8px',
                        }}
                        labelStyle={{ color: '#f8fafc' }}
                      />
                      <Bar dataKey="wallets" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Marketing Suggestions */}
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-orange-400" />
                Marketing Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {cohorts.slice(0, 4).map((cohort) => (
                  <div key={cohort.cohort_name} className="p-4 bg-slate-800/50 rounded-lg">
                    <h4 className="font-medium capitalize mb-2">
                      {(cohort.cohort_name || 'Unknown').replace(/_/g, ' ')}
                    </h4>
                    <p className="text-sm text-slate-400">
                      {cohort.cohort_name?.includes('whale') && 'High-value targets for partnerships and exclusive offers.'}
                      {cohort.cohort_name?.includes('active') && 'Engaged users - perfect for community building and referrals.'}
                      {cohort.cohort_name?.includes('new') && 'New users needing onboarding content and tutorials.'}
                      {cohort.cohort_name?.includes('dormant') && 'Re-engagement campaigns with incentives to return.'}
                      {!cohort.cohort_name?.match(/whale|active|new|dormant/) && 'Potential targets for general marketing campaigns.'}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Cohort Detail Modal */}
      <Dialog open={!!selectedCohort} onOpenChange={() => setSelectedCohort(null)}>
        <DialogContent className="bg-slate-900 border-slate-800 max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 capitalize">
              {selectedCohort && getCohortIcon(selectedCohort)}
              {(selectedCohort || '').replace(/_/g, ' ')} Cohort
            </DialogTitle>
          </DialogHeader>
          
          {walletsLoading ? (
            <div className="py-8 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
            </div>
          ) : cohortWallets?.wallets && cohortWallets.wallets.length > 0 ? (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                {cohortWallets.wallets.length} wallets in this cohort
              </p>
              
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead className="text-slate-400">Address</TableHead>
                    <TableHead className="text-slate-400 text-right">Txs</TableHead>
                    <TableHead className="text-slate-400 text-right">Volume</TableHead>
                    <TableHead className="text-slate-400">Labels</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cohortWallets.wallets.map((wallet) => (
                    <TableRow key={wallet.wallet_address} className="border-slate-800">
                      <TableCell className="font-mono text-sm">
                        {wallet.wallet_address ? `${wallet.wallet_address.slice(0, 10)}...${wallet.wallet_address.slice(-6)}` : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right">{wallet.total_txs || 0}</TableCell>
                      <TableCell className="text-right">{(wallet.volume_avax || 0).toFixed(4)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {wallet.is_whale && <Badge className="bg-blue-600 text-xs">Whale</Badge>}
                          {wallet.is_bot && <Badge className="bg-purple-600 text-xs">Bot</Badge>}
                          {wallet.is_dex_user && <Badge className="bg-green-600 text-xs">DEX</Badge>}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-slate-400">No wallets found in this cohort</div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
