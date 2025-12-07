'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyzePatterns, getHeatmap, getTrends } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
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
  Loader2,
} from 'lucide-react';

export default function PatternsPage() {
  const [days, setDays] = useState('7');

  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns', days],
    queryFn: () => analyzePatterns(parseInt(days)),
  });

  const { data: heatmap, isLoading: heatmapLoading } = useQuery({
    queryKey: ['heatmap', 30],
    queryFn: () => getHeatmap(30),
  });

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['trends', days],
    queryFn: () => getTrends(parseInt(days)),
  });

  const getHeatmapColor = (value: number, max: number) => {
    if (!value || value === 0) return 'bg-slate-800';
    const intensity = value / Math.max(max, 1);
    if (intensity > 0.75) return 'bg-orange-500';
    if (intensity > 0.5) return 'bg-orange-600/70';
    if (intensity > 0.25) return 'bg-orange-700/50';
    return 'bg-orange-800/30';
  };

  const heatmapData = heatmap?.heatmap?.data || [];
  const maxHeatmapValue = Math.max(...(heatmapData.flat() || [1]), 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Behavioral Patterns</h1>
          <p className="text-slate-400 mt-1">Analyze user activity and trends</p>
        </div>
        <Select value={days} onValueChange={setDays}>
          <SelectTrigger className="w-[150px] bg-slate-800 border-slate-700">
            <SelectValue placeholder="Time period" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="14">Last 14 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="heatmap" className="space-y-6">
        <TabsList className="bg-slate-800">
          <TabsTrigger value="heatmap">Activity Heatmap</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="behaviors">Behaviors</TabsTrigger>
        </TabsList>

        {/* Heatmap Tab */}
        <TabsContent value="heatmap" className="space-y-6">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-orange-400" />
                Activity Heatmap (Last 30 Days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {heatmapLoading ? (
                <div className="h-64 flex items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
                </div>
              ) : heatmapData.length > 0 ? (
                <div className="space-y-4">
                  {/* Heatmap Grid */}
                  <div className="overflow-x-auto">
                    <div className="min-w-[700px]">
                      {/* Hour Labels */}
                      <div className="flex mb-2 ml-16">
                        {(heatmap?.heatmap?.columns || []).filter((_, i) => i % 4 === 0).map((hour, i) => (
                          <div key={i} className="w-16 text-xs text-slate-500 text-center">
                            {hour}
                          </div>
                        ))}
                      </div>

                      {/* Rows */}
                      {(heatmap?.heatmap?.rows || []).map((day, dayIndex) => (
                        <div key={day} className="flex items-center gap-1 mb-1">
                          <span className="w-14 text-sm text-slate-400 text-right pr-2">{day?.slice(0, 3) || ''}</span>
                          <div className="flex gap-[2px]">
                            {(heatmapData[dayIndex] || []).map((value, hourIndex) => (
                              <div
                                key={hourIndex}
                                className={`w-[18px] h-[18px] rounded-sm ${getHeatmapColor(value, maxHeatmapValue)} transition-colors hover:ring-2 hover:ring-orange-400 cursor-pointer`}
                                title={`${day} ${heatmap?.heatmap?.columns?.[hourIndex] || ''}: ${value || 0} txs`}
                              />
                            ))}
                          </div>
                        </div>
                      ))}

                      {/* Legend */}
                      <div className="flex items-center gap-2 mt-6 ml-16">
                        <span className="text-xs text-slate-500">Less</span>
                        <div className="flex gap-1">
                          <div className="w-4 h-4 bg-slate-800 rounded-sm" />
                          <div className="w-4 h-4 bg-orange-800/30 rounded-sm" />
                          <div className="w-4 h-4 bg-orange-700/50 rounded-sm" />
                          <div className="w-4 h-4 bg-orange-600/70 rounded-sm" />
                          <div className="w-4 h-4 bg-orange-500 rounded-sm" />
                        </div>
                        <span className="text-xs text-slate-500">More</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-slate-400">
                  No activity data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Insights */}
          {heatmap?.insights && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="h-5 w-5 text-orange-400" />
                    <span className="text-sm text-slate-400">Peak Time</span>
                  </div>
                  <p className="text-2xl font-bold">{heatmap.insights.peak_day || 'N/A'}</p>
                  <p className="text-lg text-slate-300">{heatmap.insights.peak_hour || 'N/A'}</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="h-5 w-5 text-yellow-400" />
                    <span className="text-sm text-slate-400">Busiest Day</span>
                  </div>
                  <p className="text-2xl font-bold">{heatmap.insights.busiest_day || 'N/A'}</p>
                  <p className="text-sm text-slate-400">{(heatmap.total_transactions || 0).toLocaleString()} total txs</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="h-5 w-5 text-green-400" />
                    <span className="text-sm text-slate-400">Best Post Times</span>
                  </div>
                  <div className="space-y-1">
                    {(heatmap.insights.best_posting_times || []).slice(0, 3).map((time, i) => (
                      <p key={i} className="text-sm">
                        <span className="text-slate-300">{time.day?.slice(0, 3) || ''}</span>
                        <span className="text-slate-500"> @ </span>
                        <span className="text-orange-400">{time.hour || ''}</span>
                      </p>
                    ))}
                    {(!heatmap.insights.best_posting_times || heatmap.insights.best_posting_times.length === 0) && (
                      <p className="text-sm text-slate-500">No data</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-6">
          {trendsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
            </div>
          ) : (trends?.trends || []).length === 0 ? (
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-12 text-center">
                <TrendingUp className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-400 mb-2">No Trend Data</h3>
                <p className="text-sm text-slate-500">
                  Need more historical data to calculate trends. Keep indexing!
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(trends?.trends || []).map((trend) => (
                  <Card key={trend.metric} className="bg-slate-900 border-slate-800">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm text-slate-400">{trend.metric}</p>
                          <p className="text-3xl font-bold mt-1">
                            {typeof trend.current === 'number' ? trend.current.toLocaleString() : trend.current}
                          </p>
                          <p className="text-sm text-slate-500 mt-1">
                            vs {typeof trend.previous === 'number' ? trend.previous.toLocaleString() : trend.previous} last period
                          </p>
                        </div>
                        <div className={`flex items-center gap-1 px-2 py-1 rounded ${
                          trend.direction === 'up' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {trend.direction === 'up' ? (
                            <ArrowUpRight className="h-4 w-4" />
                          ) : (
                            <ArrowDownRight className="h-4 w-4" />
                          )}
                          <span className="font-medium">{Math.abs(trend.change_percent || 0)}%</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Insights */}
              {trends?.insights && trends.insights.length > 0 && (
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle>Key Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {trends.insights.map((insight, i) => (
                        <p key={i} className="text-slate-300">{insight}</p>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Summary */}
              {trends?.summary && (
                <div className="flex flex-wrap gap-4">
                  <Badge variant="outline" className="border-slate-600 px-4 py-2">
                    <Fish className="h-4 w-4 mr-2" />
                    {trends.summary.active_whales || 0} Active Whales
                  </Badge>
                  <Badge variant="outline" className="border-green-500/50 text-green-400 px-4 py-2">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    {trends.summary.total_trends_up || 0} Metrics Up
                  </Badge>
                  <Badge variant="outline" className="border-red-500/50 text-red-400 px-4 py-2">
                    <TrendingDown className="h-4 w-4 mr-2" />
                    {trends.summary.total_trends_down || 0} Metrics Down
                  </Badge>
                </div>
              )}
            </>
          )}
        </TabsContent>

        {/* Behaviors Tab */}
        <TabsContent value="behaviors" className="space-y-6">
          {patternsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Accumulators */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-400" />
                    Accumulators
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(patterns?.patterns?.accumulators || []).length === 0 ? (
                    <div className="text-slate-500 text-center py-4">No accumulators detected</div>
                  ) : (
                    <div className="space-y-2">
                      {(patterns?.patterns?.accumulators || []).slice(0, 5).map((acc, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                          <code className="text-sm text-slate-300">
                            {acc.address ? `${acc.address.slice(0, 8)}...${acc.address.slice(-4)}` : 'N/A'}
                          </code>
                          <div className="text-right">
                            <span className="text-green-400 font-medium">
                              +{(acc.net_flow_avax || 0).toFixed(2)} AVAX
                            </span>
                            <p className="text-xs text-slate-500">
                              {acc.receive_count || 0} in / {acc.send_count || 0} out
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Distributors */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-red-400" />
                    Distributors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(patterns?.patterns?.distributors || []).length === 0 ? (
                    <div className="text-slate-500 text-center py-4">No distributors detected</div>
                  ) : (
                    <div className="space-y-2">
                      {(patterns?.patterns?.distributors || []).slice(0, 5).map((dist, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                          <code className="text-sm text-slate-300">
                            {dist.address ? `${dist.address.slice(0, 8)}...${dist.address.slice(-4)}` : 'N/A'}
                          </code>
                          <div className="text-right">
                            <span className="text-red-400 font-medium">
                              -{(dist.net_flow_avax || 0).toFixed(2)} AVAX
                            </span>
                            <p className="text-xs text-slate-500">
                              {dist.send_count || 0} out / {dist.receive_count || 0} in
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* High Frequency */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-yellow-400" />
                    High Frequency Traders
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(patterns?.patterns?.high_frequency || []).length === 0 ? (
                    <div className="text-slate-500 text-center py-4">No high frequency traders detected</div>
                  ) : (
                    <div className="space-y-2">
                      {(patterns?.patterns?.high_frequency || []).slice(0, 5).map((hf, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                          <code className="text-sm text-slate-300">
                            {hf.address ? `${hf.address.slice(0, 8)}...${hf.address.slice(-4)}` : 'N/A'}
                          </code>
                          <div className="text-right">
                            <span className="text-yellow-400 font-medium">{hf.tx_count || 0} txs</span>
                            <p className="text-xs text-slate-500">{(hf.volume_avax || 0).toFixed(2)} AVAX</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* New Whales */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Fish className="h-5 w-5 text-blue-400" />
                    New Whales
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(patterns?.patterns?.new_whales || []).length === 0 ? (
                    <div className="text-slate-500 text-center py-4">No new whales detected</div>
                  ) : (
                    <div className="space-y-2">
                      {(patterns?.patterns?.new_whales || []).slice(0, 5).map((whale, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                          <code className="text-sm text-slate-300">
                            {whale.address ? `${whale.address.slice(0, 8)}...${whale.address.slice(-4)}` : 'N/A'}
                          </code>
                          <div className="text-right">
                            <span className="text-blue-400 font-medium">{(whale.volume_avax || 0).toFixed(2)} AVAX</span>
                            <p className="text-xs text-slate-500">{whale.tx_count || 0} txs</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
