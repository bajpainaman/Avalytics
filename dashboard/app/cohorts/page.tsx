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
import { Users, Target, ChevronRight, BarChart3 } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// 🔥 DEMO MODE
const DEMO_MODE = true;

const DEMO_COHORTS = {
  total_cohorts: 8,
  cohorts: [
    { cohort_name: 'whale_traders', wallet_count: 1247, avg_volume_avax: 284729.45, avg_txs: 892, whale_count: 1247 },
    { cohort_name: 'high_frequency', wallet_count: 3892, avg_volume_avax: 47293.12, avg_txs: 2847, whale_count: 234 },
    { cohort_name: 'defi_power_users', wallet_count: 8472, avg_volume_avax: 18472.34, avg_txs: 456, whale_count: 567 },
    { cohort_name: 'nft_collectors', wallet_count: 12847, avg_volume_avax: 8472.89, avg_txs: 234, whale_count: 189 },
    { cohort_name: 'casual_users', wallet_count: 284729, avg_volume_avax: 847.23, avg_txs: 12, whale_count: 0 },
    { cohort_name: 'new_explorers', wallet_count: 192847, avg_volume_avax: 234.56, avg_txs: 3, whale_count: 0 },
    { cohort_name: 'dormant_holders', wallet_count: 147293, avg_volume_avax: 12847.89, avg_txs: 2, whale_count: 892 },
    { cohort_name: 'bot_traders', wallet_count: 3892, avg_volume_avax: 92847.12, avg_txs: 8472, whale_count: 45 },
  ],
};

// Demo wallets for each cohort
const generateDemoWallets = (cohortName: string) => {
  const baseWallets = [
    { wallet_address: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', total_txs: 892, volume_avax: 284729.45, is_whale: true, is_bot: false, is_dex_user: true },
    { wallet_address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', total_txs: 567, volume_avax: 192847.23, is_whale: true, is_bot: false, is_dex_user: true },
    { wallet_address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', total_txs: 445, volume_avax: 147293.89, is_whale: true, is_bot: false, is_dex_user: false },
    { wallet_address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', total_txs: 334, volume_avax: 98472.45, is_whale: false, is_bot: false, is_dex_user: true },
    { wallet_address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', total_txs: 223, volume_avax: 67293.12, is_whale: false, is_bot: false, is_dex_user: true },
    { wallet_address: '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6', total_txs: 178, volume_avax: 45827.78, is_whale: false, is_bot: true, is_dex_user: false },
    { wallet_address: '0xD6DF932A45C0f255f85145f286eA0b292B21C90B', total_txs: 145, volume_avax: 34729.34, is_whale: false, is_bot: false, is_dex_user: true },
    { wallet_address: '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39', total_txs: 112, volume_avax: 23847.56, is_whale: false, is_bot: true, is_dex_user: true },
  ];
  return { cohort: cohortName, wallets: baseWallets };
};

export default function CohortsPage() {
  const [selectedCohort, setSelectedCohort] = useState<string | null>(null);

  const { data: apiData, isLoading, isError } = useQuery({
    queryKey: ['cohorts'],
    queryFn: getCohorts,
    staleTime: 5 * 60 * 1000,
  });

  const { data: apiCohortWallets, isLoading: walletsLoading } = useQuery({
    queryKey: ['cohortWallets', selectedCohort],
    queryFn: () => (selectedCohort ? getCohortWallets(selectedCohort, 50) : null),
    enabled: !DEMO_MODE && !!selectedCohort,
    staleTime: 5 * 60 * 1000,
  });

  // Use demo wallets in demo mode
  const cohortWallets = DEMO_MODE && selectedCohort ? generateDemoWallets(selectedCohort) : apiCohortWallets;

  // Use demo or real data
  const data = DEMO_MODE ? DEMO_COHORTS : apiData;
  const cohorts = data?.cohorts || [];

  const chartData = cohorts.map((c) => ({
    name: (c.cohort_name || 'Unknown').replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    wallets: c.wallet_count || 0,
    volume: c.avg_volume_avax || 0,
  }));

  if (!DEMO_MODE && isLoading && !apiData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <svg width="120" height="40" viewBox="0 0 120 40" className="overflow-visible">
          <path
            d="M10 20 Q30 5, 50 20 T90 20 T110 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-foreground/20"
          />
          <path
            d="M10 20 Q30 5, 50 20 T90 20 T110 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            className="text-foreground animate-dash"
          />
        </svg>
        <p className="text-sm text-muted-foreground">Loading cohorts...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">Failed to load cohorts. Check API connection.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Cohort Analysis</h1>
        <p className="text-muted-foreground text-sm mt-0.5">
          {data?.total_cohorts || 0} cohorts detected via ML clustering
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cohorts.slice(0, 4).map((cohort) => (
          <Card key={cohort.cohort_name} className="cursor-pointer hover:bg-secondary/30 transition-colors" onClick={() => setSelectedCohort(cohort.cohort_name)}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide truncate">
                  {(cohort.cohort_name || 'Unknown').replace(/_/g, ' ')}
                </p>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="text-2xl font-semibold mt-1">{(cohort.wallet_count || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground mt-1">{(cohort.avg_volume_avax || 0).toFixed(2)} AVAX avg</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Cohort Cards */}
      {cohorts.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Users className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
            <h3 className="text-base font-medium text-muted-foreground mb-1">No Cohorts Found</h3>
            <p className="text-sm text-muted-foreground/60">
              Run the cohort detection to analyze wallet clusters.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Distribution Chart */}
          {chartData.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  Cohort Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={true} vertical={false} />
                      <XAxis type="number" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis 
                        type="category" 
                        dataKey="name" 
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} 
                        tickLine={false} 
                        axisLine={false}
                        width={100}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '6px',
                          fontSize: '12px',
                        }}
                        labelStyle={{ color: 'hsl(var(--foreground))' }}
                      />
                      <Bar dataKey="wallets" fill="hsl(var(--foreground))" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Marketing Insights */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Target className="h-4 w-4 text-muted-foreground" />
                Marketing Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {cohorts.slice(0, 4).map((cohort) => (
                <div 
                  key={cohort.cohort_name} 
                  className="p-3 bg-secondary/30 rounded-md cursor-pointer hover:bg-secondary/50 transition-colors"
                  onClick={() => setSelectedCohort(cohort.cohort_name)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium capitalize">
                      {(cohort.cohort_name || 'Unknown').replace(/_/g, ' ')}
                    </h4>
                    <Badge variant="secondary" className="text-[10px]">
                      {cohort.wallet_count} wallets
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {cohort.cohort_name?.includes('whale') && 'High-value targets for partnerships and exclusive offers.'}
                    {cohort.cohort_name?.includes('high') && 'Active traders - perfect for liquidity campaigns.'}
                    {cohort.cohort_name?.includes('active') && 'Engaged users - great for community building.'}
                    {cohort.cohort_name?.includes('new') && 'New users needing onboarding content.'}
                    {cohort.cohort_name?.includes('contract') && 'Power users exploring smart contracts.'}
                    {cohort.cohort_name?.includes('casual') && 'Casual users - target for engagement campaigns.'}
                    {cohort.cohort_name?.includes('frequent') && 'High frequency traders - ideal for trading features.'}
                    {!cohort.cohort_name?.match(/whale|active|new|contract|casual|frequent|high/) && 'Potential targets for marketing campaigns.'}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* All Cohorts Table */}
      {cohorts.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">All Cohorts</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Cohort</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide text-right">Wallets</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide text-right">Avg Volume</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide text-right">Avg Txs</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide text-right">Whales</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cohorts.map((cohort) => (
                  <TableRow 
                    key={cohort.cohort_name} 
                    className="border-border hover:bg-secondary/50 cursor-pointer"
                    onClick={() => setSelectedCohort(cohort.cohort_name)}
                  >
                    <TableCell className="font-medium capitalize text-sm">
                      {(cohort.cohort_name || 'Unknown').replace(/_/g, ' ')}
                    </TableCell>
                    <TableCell className="text-right text-sm">{(cohort.wallet_count || 0).toLocaleString()}</TableCell>
                    <TableCell className="text-right text-sm">{(cohort.avg_volume_avax || 0).toFixed(2)} AVAX</TableCell>
                    <TableCell className="text-right text-sm">{(cohort.avg_txs || 0).toFixed(0)}</TableCell>
                    <TableCell className="text-right text-sm">{cohort.whale_count || 0}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Cohort Detail Modal */}
      <Dialog open={!!selectedCohort} onOpenChange={() => setSelectedCohort(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-base font-medium capitalize">
              {(selectedCohort || '').replace(/_/g, ' ')} Cohort
            </DialogTitle>
          </DialogHeader>
          
          {walletsLoading ? (
            <div className="py-8 flex flex-col items-center justify-center gap-4">
              <svg width="80" height="30" viewBox="0 0 120 40" className="overflow-visible">
                <path d="M10 20 Q30 5, 50 20 T90 20 T110 20" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground/20" />
                <path d="M10 20 Q30 5, 50 20 T90 20 T110 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="text-foreground animate-dash" />
              </svg>
              <p className="text-xs text-muted-foreground">Loading wallets...</p>
            </div>
          ) : cohortWallets?.wallets && cohortWallets.wallets.length > 0 ? (
            <div className="space-y-4">
              <p className="text-xs text-muted-foreground">
                {cohortWallets.wallets.length} wallets in this cohort
              </p>
              
              <Table>
                <TableHeader>
                  <TableRow className="border-border">
                    <TableHead className="text-xs text-muted-foreground uppercase">Address</TableHead>
                    <TableHead className="text-xs text-muted-foreground uppercase text-right">Txs</TableHead>
                    <TableHead className="text-xs text-muted-foreground uppercase text-right">Volume</TableHead>
                    <TableHead className="text-xs text-muted-foreground uppercase">Labels</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cohortWallets.wallets.map((wallet) => (
                    <TableRow key={wallet.wallet_address} className="border-border">
                      <TableCell className="font-mono text-xs">
                        {wallet.wallet_address ? `${wallet.wallet_address.slice(0, 10)}...${wallet.wallet_address.slice(-6)}` : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right text-sm">{wallet.total_txs || 0}</TableCell>
                      <TableCell className="text-right text-sm">{(wallet.volume_avax || 0).toFixed(4)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {wallet.is_whale && <Badge variant="secondary" className="text-[10px]">Whale</Badge>}
                          {wallet.is_bot && <Badge variant="secondary" className="text-[10px]">Bot</Badge>}
                          {wallet.is_dex_user && <Badge variant="secondary" className="text-[10px]">DEX</Badge>}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-muted-foreground text-sm">No wallets found in this cohort</div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
