'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyzePatterns, getHeatmap, getTrends } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  Fish,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

// 🔥 DEMO MODE
const DEMO_MODE = true;

// Generate impressive heatmap data - FULL and active looking
const generateHeatmapData = () => {
  const data: number[][] = [];
  for (let day = 0; day < 7; day++) {
    const row: number[] = [];
    for (let hour = 0; hour < 24; hour++) {
      // More aggressive fill - always some activity
      let base = 30 + Math.random() * 40; // Base activity everywhere
      
      // Business hours boost
      if (hour >= 8 && hour <= 20) base += 60 + Math.random() * 100;
      
      // Peak hours
      if (hour >= 10 && hour <= 12) base += 50 + Math.random() * 50;
      if (hour >= 14 && hour <= 18) base += 70 + Math.random() * 60;
      
      // Weekday boost
      if (day >= 0 && day <= 4) base *= 1.2;
      
      // Some random spikes
      if (Math.random() > 0.85) base += 100;
      
      row.push(Math.floor(base));
    }
    data.push(row);
  }
  return data;
};

const DEMO_HEATMAP = {
  heatmap: {
    data: generateHeatmapData(),
    rows: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    columns: Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`),
  },
  total_transactions: 284729,
  insights: {
    peak_day: 'Tuesday',
    peak_hour: '14:00 - 16:00 UTC',
    busiest_day: 'Wednesday',
    best_posting_times: [
      { day: 'Tuesday', hour: '14:00 UTC' },
      { day: 'Wednesday', hour: '15:00 UTC' },
      { day: 'Thursday', hour: '10:00 UTC' },
    ],
  },
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
      { address: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', net_flow_avax: 847293.47, receive_count: 892, send_count: 23 },
      { address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', net_flow_avax: 392847.23, receive_count: 456, send_count: 12 },
      { address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', net_flow_avax: 284729.89, receive_count: 234, send_count: 8 },
      { address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', net_flow_avax: 192847.45, receive_count: 189, send_count: 15 },
      { address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', net_flow_avax: 147293.12, receive_count: 145, send_count: 7 },
    ],
    distributors: [
      { address: '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6', net_flow_avax: -523847.12, send_count: 1247, receive_count: 34 },
      { address: '0xD6DF932A45C0f255f85145f286eA0b292B21C90B', net_flow_avax: -284729.45, send_count: 892, receive_count: 23 },
      { address: '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39', net_flow_avax: -192847.78, send_count: 567, receive_count: 12 },
      { address: '0xB0B195aEFA3650A6908f15CdaC7D92F8a5791B0B', net_flow_avax: -147293.34, send_count: 445, receive_count: 8 },
      { address: '0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7', net_flow_avax: -98472.56, send_count: 334, receive_count: 5 },
    ],
    high_frequency: [
      { address: '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39', tx_count: 8472, volume_avax: 1284729.34 },
      { address: '0xfa68FB4628DFF1028CFEc22b4162FCcd0d45efb6', tx_count: 6234, volume_avax: 982374.12 },
      { address: '0x831753DD7087CaC61aB5644b308642cc1c33Dc13', tx_count: 4892, volume_avax: 784293.45 },
      { address: '0x1a13F4Ca1d028320A707D99520AbFefca3998b7F', tx_count: 3847, volume_avax: 623847.89 },
      { address: '0xE111178A87A3BFf0c8d18DECBa5798827539Ae99', tx_count: 2934, volume_avax: 498274.23 },
    ],
    new_whales: [
      { address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', volume_avax: 927384.23, tx_count: 234 },
      { address: '0x2953399124F0cBB46d2CbACD8A89cF0599974963', volume_avax: 784293.45, tx_count: 189 },
      { address: '0xA374094527e1673A86dE625aa59517c5dE346d32', volume_avax: 623847.12, tx_count: 156 },
      { address: '0x45dDa9cb7c25131DF268515131f647d726f50608', volume_avax: 498274.89, tx_count: 123 },
      { address: '0xDf7837DE1F2Fa4631D716CF2502f8b230F1dcc32', volume_avax: 384729.34, tx_count: 98 },
    ],
  },
};

const DEMO_TRENDS = {
  trends: [
    { metric: 'Daily Active Wallets', current: 12847, previous: 9823, change_percent: 30.8, direction: 'up' },
    { metric: 'Transaction Volume', current: 2847293, previous: 2134892, change_percent: 33.4, direction: 'up' },
    { metric: 'New Wallets', current: 3847, previous: 2934, change_percent: 31.1, direction: 'up' },
    { metric: 'Avg Transaction Size', current: 847.23, previous: 923.45, change_percent: -8.3, direction: 'down' },
  ],
};

export default function PatternsPage() {
  const [days, setDays] = useState('7');

  const { data: apiPatterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns', days],
    queryFn: () => analyzePatterns(parseInt(days)),
    staleTime: 5 * 60 * 1000,
  });

  const { data: apiHeatmap, isLoading: heatmapLoading } = useQuery({
    queryKey: ['heatmap', 30],
    queryFn: () => getHeatmap(30),
    staleTime: 10 * 60 * 1000,
  });

  const { data: apiTrends } = useQuery({
    queryKey: ['trends', days],
    queryFn: () => getTrends(parseInt(days)),
    staleTime: 5 * 60 * 1000,
  });

  // Use demo or real data
  const patterns = DEMO_MODE ? DEMO_PATTERNS : apiPatterns;
  const heatmap = DEMO_MODE ? DEMO_HEATMAP : apiHeatmap;
  const trends = DEMO_MODE ? DEMO_TRENDS : apiTrends;

  const getHeatmapColor = (value: number, max: number) => {
    if (!value || value === 0) return 'bg-[#1a1a1a]';
    const intensity = value / Math.max(max, 1);
    if (intensity > 0.8) return 'bg-white';
    if (intensity > 0.6) return 'bg-white/80';
    if (intensity > 0.4) return 'bg-white/50';
    if (intensity > 0.2) return 'bg-white/30';
    return 'bg-white/15';
  };

  const heatmapData = heatmap?.heatmap?.data || [];
  const maxHeatmapValue = Math.max(...(heatmapData.flat() || [1]), 1);

  // Only show loading on initial load
  const isInitialLoading = !DEMO_MODE && ((patternsLoading && !apiPatterns) || (heatmapLoading && !apiHeatmap));

  // Loading State
  if (isInitialLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <svg width="120" height="40" viewBox="0 0 120 40" className="overflow-visible">
          <path d="M10 20 Q30 5, 50 20 T90 20 T110 20" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground/20" />
          <path d="M10 20 Q30 5, 50 20 T90 20 T110 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="text-foreground animate-dash" />
        </svg>
        <p className="text-sm text-muted-foreground">Analyzing patterns...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Behavioral Patterns</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Activity trends and user behaviors</p>
        </div>
        <Select value={days} onValueChange={setDays}>
          <SelectTrigger className="w-[130px] h-8 text-xs">
            <SelectValue placeholder="Time period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="14">Last 14 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Accumulators</p>
            </div>
            <p className="text-2xl font-semibold">{patterns?.summary?.accumulators_count || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Distributors</p>
            </div>
            <p className="text-2xl font-semibold">{patterns?.summary?.distributors_count || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs text-muted-foreground uppercase tracking-wide">High Frequency</p>
            </div>
            <p className="text-2xl font-semibold">{patterns?.summary?.high_frequency_count || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Fish className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs text-muted-foreground uppercase tracking-wide">New Whales</p>
            </div>
            <p className="text-2xl font-semibold">{patterns?.summary?.new_whales_count || 0}</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Heatmap - takes 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              Activity Heatmap (30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {heatmapData.length > 0 ? (
              <div className="space-y-3">
                <div className="overflow-x-auto">
                  <div className="min-w-[600px]">
                    {/* Hour Labels */}
                    <div className="flex mb-1.5 ml-12">
                      {(heatmap?.heatmap?.columns || []).filter((_, i) => i % 4 === 0).map((hour, i) => (
                        <div key={i} className="w-16 text-[10px] text-muted-foreground text-center">{hour}</div>
                      ))}
                    </div>
                    {/* Rows */}
                    {(heatmap?.heatmap?.rows || []).map((day, dayIndex) => (
                      <div key={day} className="flex items-center gap-0.5 mb-0.5">
                        <span className="w-10 text-[10px] text-muted-foreground text-right pr-2">{day?.slice(0, 3) || ''}</span>
                        <div className="flex gap-[1px]">
                          {(heatmapData[dayIndex] || []).map((value, hourIndex) => (
                            <div
                              key={hourIndex}
                              className={`w-[14px] h-[14px] rounded-[2px] ${getHeatmapColor(value, maxHeatmapValue)} transition-colors hover:ring-1 hover:ring-foreground cursor-pointer`}
                              title={`${day} ${heatmap?.heatmap?.columns?.[hourIndex] || ''}: ${value || 0} txs`}
                            />
                          ))}
                        </div>
                      </div>
                    ))}
                    {/* Legend */}
                    <div className="flex items-center gap-2 mt-4 ml-12">
                      <span className="text-[10px] text-muted-foreground">Less</span>
                      <div className="flex gap-0.5">
                        <div className="w-3 h-3 bg-[#1a1a1a] rounded-[2px]" />
                        <div className="w-3 h-3 bg-white/15 rounded-[2px]" />
                        <div className="w-3 h-3 bg-white/30 rounded-[2px]" />
                        <div className="w-3 h-3 bg-white/60 rounded-[2px]" />
                        <div className="w-3 h-3 bg-white rounded-[2px]" />
                      </div>
                      <span className="text-[10px] text-muted-foreground">More</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
                No activity data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Insights Panel */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {heatmap?.insights ? (
              <>
                <div className="p-3 bg-secondary/30 rounded-md">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Peak Time</p>
                  <p className="text-lg font-semibold mt-1">{heatmap.insights.peak_day || 'N/A'}</p>
                  <p className="text-sm text-muted-foreground">{heatmap.insights.peak_hour || ''}</p>
                </div>
                <div className="p-3 bg-secondary/30 rounded-md">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Busiest Day</p>
                  <p className="text-lg font-semibold mt-1">{heatmap.insights.busiest_day || 'N/A'}</p>
                  <p className="text-xs text-muted-foreground">{(heatmap.total_transactions || 0).toLocaleString()} total txs</p>
                </div>
                <div className="p-3 bg-secondary/30 rounded-md">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Best Post Times</p>
                  {(heatmap.insights.best_posting_times || []).slice(0, 3).map((time, i) => (
                    <p key={i} className="text-xs">
                      <span className="text-foreground">{time.day?.slice(0, 3) || ''}</span>
                      <span className="text-muted-foreground"> @ </span>
                      <span className="text-foreground font-medium">{time.hour || ''}</span>
                    </p>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No insights available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trends */}
      {(trends?.trends || []).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              Trends ({days} days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {(trends?.trends || []).map((trend) => (
                <div key={trend.metric} className="p-3 bg-secondary/30 rounded-md">
                  <div className="flex items-start justify-between">
                    <p className="text-xs text-muted-foreground">{trend.metric}</p>
                    <div className="flex items-center gap-0.5 text-xs text-muted-foreground">
                      {trend.direction === 'up' ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                      {Math.abs(trend.change_percent || 0).toFixed(1)}%
                    </div>
                  </div>
                  <p className="text-xl font-semibold mt-1">
                    {typeof trend.current === 'number' ? trend.current.toLocaleString() : trend.current}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Behavior Lists */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Accumulators */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              Top Accumulators
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(patterns?.patterns?.accumulators || []).length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-4">No accumulators detected</p>
            ) : (
              <div className="space-y-1.5">
                {(patterns?.patterns?.accumulators || []).slice(0, 5).map((acc, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-secondary/20 rounded-md">
                    <code className="text-xs text-muted-foreground font-mono">
                      {acc.address ? `${acc.address.slice(0, 8)}...${acc.address.slice(-4)}` : 'N/A'}
                    </code>
                    <span className="text-xs font-medium text-foreground">+{(acc.net_flow_avax || 0).toLocaleString()} AVAX</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Distributors */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
              Top Distributors
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(patterns?.patterns?.distributors || []).length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-4">No distributors detected</p>
            ) : (
              <div className="space-y-1.5">
                {(patterns?.patterns?.distributors || []).slice(0, 5).map((dist, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-secondary/20 rounded-md">
                    <code className="text-xs text-muted-foreground font-mono">
                      {dist.address ? `${dist.address.slice(0, 8)}...${dist.address.slice(-4)}` : 'N/A'}
                    </code>
                    <span className="text-xs font-medium text-foreground">-{Math.abs(dist.net_flow_avax || 0).toLocaleString()} AVAX</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* High Frequency */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-muted-foreground" />
              High Frequency Traders
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(patterns?.patterns?.high_frequency || []).length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-4">No high frequency traders</p>
            ) : (
              <div className="space-y-1.5">
                {(patterns?.patterns?.high_frequency || []).slice(0, 5).map((hf, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-secondary/20 rounded-md">
                    <code className="text-xs text-muted-foreground font-mono">
                      {hf.address ? `${hf.address.slice(0, 8)}...${hf.address.slice(-4)}` : 'N/A'}
                    </code>
                    <span className="text-xs font-medium text-foreground">{(hf.tx_count || 0).toLocaleString()} txs</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* New Whales */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Fish className="h-4 w-4 text-muted-foreground" />
              New Whales
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(patterns?.patterns?.new_whales || []).length === 0 ? (
              <p className="text-muted-foreground text-sm text-center py-4">No new whales detected</p>
            ) : (
              <div className="space-y-1.5">
                {(patterns?.patterns?.new_whales || []).slice(0, 5).map((whale, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-secondary/20 rounded-md">
                    <code className="text-xs text-muted-foreground font-mono">
                      {whale.address ? `${whale.address.slice(0, 8)}...${whale.address.slice(-4)}` : 'N/A'}
                    </code>
                    <span className="text-xs font-medium text-foreground">{(whale.volume_avax || 0).toLocaleString()} AVAX</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
