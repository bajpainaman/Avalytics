'use client';

import { useQuery } from '@tanstack/react-query';
import { getStats, getChainStats, analyzePatterns } from '@/lib/api';
import { StatCard } from '@/components/stat-card';
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
  Loader2,
} from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  });

  const { data: chainStats, isLoading: chainLoading } = useQuery({
    queryKey: ['chainStats'],
    queryFn: getChainStats,
  });

  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns', 7],
    queryFn: () => analyzePatterns(7),
  });

  const formatNumber = (num: number | undefined | null) => {
    if (num === undefined || num === null) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const isLoading = statsLoading || chainLoading || patternsLoading;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-slate-400 mt-1">Avalanche C-Chain Analytics Overview</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchStats()}
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {chainStats?.synced && (
            <Badge variant="outline" className="border-green-500/50 text-green-400">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
              Chain Synced
            </Badge>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Wallets"
          value={statsLoading ? '...' : formatNumber(stats?.total_wallets)}
          subtitle="Unique addresses tracked"
          icon={Wallet}
        />
        <StatCard
          title="Transactions"
          value={statsLoading ? '...' : formatNumber(stats?.total_transactions)}
          subtitle={`${formatNumber(stats?.blocks_indexed)} blocks indexed`}
          icon={ArrowRightLeft}
        />
        <StatCard
          title="Total Volume"
          value={statsLoading ? '...' : `${formatNumber(stats?.total_volume_avax)} AVAX`}
          subtitle="Cumulative volume"
          icon={Coins}
        />
        <StatCard
          title="Whale Wallets"
          value={statsLoading ? '...' : String(stats?.whale_count || 0)}
          subtitle={`${stats?.bot_count || 0} bots detected`}
          icon={Fish}
        />
      </div>

      {/* Pattern Summary & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pattern Summary */}
        <Card className="lg:col-span-2 bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-orange-400" />
              7-Day Behavior Patterns
            </CardTitle>
          </CardHeader>
          <CardContent>
            {patternsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-4 w-4 text-green-400" />
                      <span className="text-sm text-slate-400">Accumulators</span>
                    </div>
                    <p className="text-2xl font-bold text-green-400">
                      {patterns?.summary?.accumulators_count || 0}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingDown className="h-4 w-4 text-red-400" />
                      <span className="text-sm text-slate-400">Distributors</span>
                    </div>
                    <p className="text-2xl font-bold text-red-400">
                      {patterns?.summary?.distributors_count || 0}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-4 w-4 text-yellow-400" />
                      <span className="text-sm text-slate-400">High Frequency</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-400">
                      {patterns?.summary?.high_frequency_count || 0}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Fish className="h-4 w-4 text-blue-400" />
                      <span className="text-sm text-slate-400">New Whales</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-400">
                      {patterns?.summary?.new_whales_count || 0}
                    </p>
                  </div>
                </div>

                {/* Top Accumulators */}
                {patterns?.patterns?.accumulators && patterns.patterns.accumulators.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-slate-400 mb-3">Top Accumulators</h4>
                    <div className="space-y-2">
                      {patterns.patterns.accumulators.slice(0, 3).map((acc, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg">
                          <code className="text-sm text-slate-300">
                            {acc.address?.slice(0, 10)}...{acc.address?.slice(-6)}
                          </code>
                          <span className="text-green-400 font-medium">
                            +{(acc.net_flow_avax || 0).toFixed(2)} AVAX
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
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/icp" className="block">
              <Button
                variant="outline"
                className="w-full justify-start border-slate-700 hover:bg-slate-800 hover:border-orange-500/50"
              >
                <Target className="h-4 w-4 mr-3 text-orange-400" />
                Generate ICP Profile
              </Button>
            </Link>
            <Link href="/social" className="block">
              <Button
                variant="outline"
                className="w-full justify-start border-slate-700 hover:bg-slate-800 hover:border-orange-500/50"
              >
                <MessageSquare className="h-4 w-4 mr-3 text-orange-400" />
                Create Social Post
              </Button>
            </Link>
            <Link href="/wallets" className="block">
              <Button
                variant="outline"
                className="w-full justify-start border-slate-700 hover:bg-slate-800 hover:border-orange-500/50"
              >
                <Wallet className="h-4 w-4 mr-3 text-orange-400" />
                Explore Wallets
              </Button>
            </Link>
            <Link href="/patterns" className="block">
              <Button
                variant="outline"
                className="w-full justify-start border-slate-700 hover:bg-slate-800 hover:border-orange-500/50"
              >
                <Activity className="h-4 w-4 mr-3 text-orange-400" />
                View Activity Heatmap
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Chain Info */}
      {!chainLoading && chainStats && (
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-orange-400" />
              Chain Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-400">Chain ID</p>
                <p className="text-lg font-semibold">{chainStats.chain_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Latest Block</p>
                <p className="text-lg font-semibold">{formatNumber(chainStats.latest_block)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Gas Price</p>
                <p className="text-lg font-semibold">
                  {chainStats.gas_price_gwei ? chainStats.gas_price_gwei.toFixed(2) : '0'} Gwei
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Status</p>
                <Badge variant="outline" className={chainStats.synced ? 'border-green-500 text-green-400' : 'border-yellow-500 text-yellow-400'}>
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
