'use client';

import { useQuery } from '@tanstack/react-query';
import { getStats, getChainStats, analyzePatterns } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Wallet,
  ArrowRightLeft,
  Coins,
  Fish,
  Activity,
  Zap,
  TrendingUp,
  TrendingDown,
  Target,
  MessageSquare,
  RefreshCw,
  ChevronRight,
  Boxes,
} from 'lucide-react';
import Link from 'next/link';

// 🔥 DEMO MODE - Impressive hardcoded data for presentations
const DEMO_MODE = true;

const DEMO_STATS = {
  total_wallets: 847293,
  total_transactions: 2847592,
  total_volume_avax: 15847293.47,
  whale_count: 1247,
  bot_count: 3892,
  blocks_indexed: 892847,
};

const DEMO_PATTERNS = {
  summary: {
    accumulators_count: 2847,
    distributors_count: 1923,
    high_frequency_count: 847,
    new_whales_count: 127,
  },
  patterns: {
    accumulators: [
      { address: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', net_flow_avax: 847293.47 },
      { address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', net_flow_avax: 392847.23 },
      { address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', net_flow_avax: 284729.89 },
    ],
    distributors: [
      { address: '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6', net_flow_avax: -523847.12 },
      { address: '0xD6DF932A45C0f255f85145f286eA0b292B21C90B', net_flow_avax: -284729.45 },
    ],
    high_frequency: [
      { address: '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39', tx_count: 8472, volume_avax: 1284729.34 },
    ],
    new_whales: [
      { address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', volume_avax: 927384.23, tx_count: 234 },
    ],
  },
};

export default function DashboardPage() {
  const { data: apiStats, isLoading: statsLoading, isFetching: statsFetching, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  });

  const { data: chainStats, isLoading: chainLoading } = useQuery({
    queryKey: ['chainStats'],
    queryFn: getChainStats,
    staleTime: 10 * 60 * 1000,
  });

  const { data: apiPatterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns', 7],
    queryFn: () => analyzePatterns(7),
    staleTime: 5 * 60 * 1000,
  });

  // Use demo data or real data
  const stats = DEMO_MODE ? DEMO_STATS : apiStats;
  const patterns = DEMO_MODE ? DEMO_PATTERNS : apiPatterns;

  const formatNumber = (num: number | undefined | null) => {
    if (num === undefined || num === null) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const isFetching = statsFetching;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Avalanche C-Chain Analytics Overview</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchStats()}
            className="h-8 text-xs"
          >
            <RefreshCw className={`h-3 w-3 mr-1.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {chainStats?.synced && (
            <Badge variant="secondary" className="h-8 px-3 text-xs font-normal">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2" />
              Synced
            </Badge>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Total Wallets</p>
                {statsLoading && !stats ? (
                  <div className="h-8 w-24 bg-secondary rounded animate-pulse" />
                ) : (
                  <p className="text-2xl font-semibold">{formatNumber(stats?.total_wallets)}</p>
                )}
                <p className="text-xs text-muted-foreground">Unique addresses</p>
              </div>
              <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                <Wallet className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Transactions</p>
                {statsLoading && !stats ? (
                  <div className="h-8 w-20 bg-secondary rounded animate-pulse" style={{ animationDelay: '100ms' }} />
                ) : (
                  <p className="text-2xl font-semibold">{formatNumber(stats?.total_transactions)}</p>
                )}
                <p className="text-xs text-muted-foreground">{formatNumber(stats?.blocks_indexed)} blocks</p>
              </div>
              <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                <ArrowRightLeft className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Total Volume</p>
                {statsLoading && !stats ? (
                  <div className="h-8 w-28 bg-secondary rounded animate-pulse" style={{ animationDelay: '200ms' }} />
                ) : (
                  <p className="text-2xl font-semibold">{formatNumber(stats?.total_volume_avax)}</p>
                )}
                <p className="text-xs text-muted-foreground">AVAX</p>
              </div>
              <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                <Coins className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Whale Wallets</p>
                {statsLoading && !stats ? (
                  <div className="h-8 w-16 bg-secondary rounded animate-pulse" style={{ animationDelay: '300ms' }} />
                ) : (
                  <p className="text-2xl font-semibold">{String(stats?.whale_count || 0)}</p>
                )}
                <p className="text-xs text-muted-foreground">{stats?.bot_count || 0} bots detected</p>
              </div>
              <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                <Fish className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pattern Summary & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Pattern Summary */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              7-Day Behavior Patterns
            </CardTitle>
          </CardHeader>
          <CardContent>
            {patternsLoading && !patterns ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="p-3 bg-secondary/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-3.5 w-3.5 bg-secondary rounded animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
                        <div className="h-3 w-16 bg-secondary rounded animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
                      </div>
                      <div className="h-6 w-12 bg-secondary rounded animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
                    </div>
                  ))}
                </div>
                <div className="space-y-2 mt-4">
                  <div className="h-3 w-24 bg-secondary rounded animate-pulse" />
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-2.5 bg-secondary/30 rounded-md">
                      <div className="h-4 w-32 bg-secondary rounded animate-pulse" style={{ animationDelay: `${i * 50}ms` }} />
                      <div className="h-4 w-20 bg-secondary rounded animate-pulse" style={{ animationDelay: `${i * 50}ms` }} />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1.5">
                      <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Accumulators</span>
                    </div>
                    <p className="text-xl font-semibold">
                      {(patterns?.summary?.accumulators_count || 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1.5">
                      <TrendingDown className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Distributors</span>
                    </div>
                    <p className="text-xl font-semibold">
                      {(patterns?.summary?.distributors_count || 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1.5">
                      <Zap className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">High Frequency</span>
                    </div>
                    <p className="text-xl font-semibold">
                      {(patterns?.summary?.high_frequency_count || 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1.5">
                      <Fish className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">New Whales</span>
                    </div>
                    <p className="text-xl font-semibold">
                      {(patterns?.summary?.new_whales_count || 0).toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Top Accumulators */}
                {patterns?.patterns?.accumulators && patterns.patterns.accumulators.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Top Accumulators</h4>
                    <div className="space-y-1.5">
                      {patterns.patterns.accumulators.slice(0, 3).map((acc, i) => (
                        <div key={i} className="flex items-center justify-between p-2.5 bg-secondary/30 rounded-md">
                          <code className="text-xs text-muted-foreground font-mono">
                            {acc.address?.slice(0, 10)}...{acc.address?.slice(-6)}
                          </code>
                          <span className="text-xs font-medium text-foreground">
                            +{(acc.net_flow_avax || 0).toLocaleString()} AVAX
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link href="/icp" className="block">
              <Button
                variant="ghost"
                className="w-full justify-between h-10 px-3 hover:bg-secondary"
              >
                <span className="flex items-center">
                  <Target className="h-4 w-4 mr-2.5 text-muted-foreground" />
                  <span className="text-sm">Generate ICP Profile</span>
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Button>
            </Link>
            <Link href="/social" className="block">
              <Button
                variant="ghost"
                className="w-full justify-between h-10 px-3 hover:bg-secondary"
              >
                <span className="flex items-center">
                  <MessageSquare className="h-4 w-4 mr-2.5 text-muted-foreground" />
                  <span className="text-sm">Create Social Post</span>
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Button>
            </Link>
            <Link href="/wallets" className="block">
              <Button
                variant="ghost"
                className="w-full justify-between h-10 px-3 hover:bg-secondary"
              >
                <span className="flex items-center">
                  <Wallet className="h-4 w-4 mr-2.5 text-muted-foreground" />
                  <span className="text-sm">Explore Wallets</span>
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Button>
            </Link>
            <Link href="/patterns" className="block">
              <Button
                variant="ghost"
                className="w-full justify-between h-10 px-3 hover:bg-secondary"
              >
                <span className="flex items-center">
                  <Activity className="h-4 w-4 mr-2.5 text-muted-foreground" />
                  <span className="text-sm">View Activity Heatmap</span>
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Chain Info */}
      {!chainLoading && chainStats && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Boxes className="h-4 w-4 text-muted-foreground" />
              Chain Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Chain ID</p>
                <p className="text-lg font-semibold mt-0.5">{chainStats.chain_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Latest Block</p>
                <p className="text-lg font-semibold mt-0.5">{formatNumber(chainStats.latest_block)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Gas Price</p>
                <p className="text-lg font-semibold mt-0.5">
                  {chainStats.gas_price_gwei ? chainStats.gas_price_gwei.toFixed(2) : '0'} Gwei
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Status</p>
                <Badge variant="secondary" className="mt-1">
                  {chainStats.synced ? 'Synced' : 'Syncing'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
