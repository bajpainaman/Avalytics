'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generateICP, searchWallets, ICPResponse } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Target,
  Sparkles,
  Users,
  Check,
  X,
  Search,
  Loader2,
  ChevronRight,
  Lightbulb,
  Megaphone,
  AlertCircle,
} from 'lucide-react';

export default function ICPPage() {
  const [formData, setFormData] = useState({
    protocol_name: '',
    protocol_description: '',
    target_audience: '',
  });
  const [icpResult, setIcpResult] = useState<ICPResponse | null>(null);
  const [nlQuery, setNlQuery] = useState('');

  const generateMutation = useMutation({
    mutationFn: generateICP,
    onSuccess: (data) => {
      setIcpResult(data);
    },
  });

  const searchMutation = useMutation({
    mutationFn: searchWallets,
  });

  const handleGenerate = () => {
    if (!formData.protocol_name || !formData.protocol_description) return;
    generateMutation.mutate(formData);
  };

  const handleNLSearch = () => {
    if (!nlQuery.trim()) return;
    searchMutation.mutate(nlQuery);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">ICP Generator</h1>
        <p className="text-slate-400 mt-1">
          AI-powered Ideal Customer Profile generation for your protocol
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="space-y-6">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-orange-400" />
                Define Your Protocol
              </CardTitle>
              <CardDescription>
                Tell us about your protocol and we&apos;ll generate an ideal customer profile
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Protocol Name *
                </label>
                <Input
                  placeholder="e.g., DeFi Lending Protocol"
                  value={formData.protocol_name}
                  onChange={(e) => setFormData({ ...formData, protocol_name: e.target.value })}
                  className="bg-slate-800 border-slate-700"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Description *
                </label>
                <Textarea
                  placeholder="Describe what your protocol does, its key features, and value proposition..."
                  value={formData.protocol_description}
                  onChange={(e) => setFormData({ ...formData, protocol_description: e.target.value })}
                  className="bg-slate-800 border-slate-700 min-h-[120px]"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300 mb-2 block">
                  Target Audience (optional)
                </label>
                <Input
                  placeholder="e.g., DeFi power users, yield farmers, institutional traders"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  className="bg-slate-800 border-slate-700"
                />
              </div>

              <Button
                onClick={handleGenerate}
                disabled={generateMutation.isPending || !formData.protocol_name || !formData.protocol_description}
                className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
              >
                {generateMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate ICP
                  </>
                )}
              </Button>

              {generateMutation.isError && (
                <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-sm text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  Failed to generate ICP. Check if API is running and OpenAI key is set.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Natural Language Search */}
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-orange-400" />
                Natural Language Search
              </CardTitle>
              <CardDescription>
                Search for wallets using plain English
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="e.g., Find me whale wallets that have been active in the last week and traded more than 100 AVAX"
                value={nlQuery}
                onChange={(e) => setNlQuery(e.target.value)}
                className="bg-slate-800 border-slate-700"
              />
              <Button
                onClick={handleNLSearch}
                disabled={searchMutation.isPending || !nlQuery.trim()}
                variant="outline"
                className="w-full border-slate-700 hover:bg-slate-800"
              >
                {searchMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Search Wallets
                  </>
                )}
              </Button>

              {searchMutation.isError && (
                <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-sm text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  Search failed. Check API connection.
                </div>
              )}

              {/* Search Results */}
              {searchMutation.data && (
                <div className="mt-4 p-4 bg-slate-800/50 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">
                      Found {searchMutation.data.total_matches || 0} matching wallets
                    </p>
                    {searchMutation.data.interpretation?.intent && (
                      <Badge variant="outline" className="border-slate-600">
                        {searchMutation.data.interpretation.intent}
                      </Badge>
                    )}
                  </div>
                  {(searchMutation.data.results || []).slice(0, 5).map((wallet) => (
                    <div key={wallet.wallet_address} className="flex items-center justify-between p-2 bg-slate-800 rounded">
                      <code className="text-xs">
                        {wallet.wallet_address ? `${wallet.wallet_address.slice(0, 10)}...${wallet.wallet_address.slice(-6)}` : 'N/A'}
                      </code>
                      <span className="text-sm text-slate-400">{(wallet.volume_avax || 0).toFixed(2)} AVAX</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Results */}
        <div className="space-y-6">
          {icpResult ? (
            <>
              {/* ICP Overview */}
              <Card className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border-orange-500/30">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-orange-400" />
                      {icpResult.icp?.name || 'Generated ICP'}
                    </CardTitle>
                    <Badge className="bg-orange-500">
                      <Users className="h-3 w-3 mr-1" />
                      {icpResult.matching_wallets || 0} matches
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-300">{icpResult.icp?.description || 'No description available'}</p>
                </CardContent>
              </Card>

              {/* Criteria */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Check className="h-5 w-5 text-green-400" />
                    Targeting Criteria
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Min Transactions</p>
                      <p className="text-xl font-bold">{icpResult.icp?.criteria?.min_transaction_count || 0}</p>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Min Volume (USD)</p>
                      <p className="text-xl font-bold">${(icpResult.icp?.criteria?.min_volume_usd || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Wallet Age</p>
                      <p className="text-xl font-bold">{icpResult.icp?.criteria?.wallet_age_days || 0} days</p>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Matches Found</p>
                      <p className="text-xl font-bold text-green-400">{icpResult.matching_wallets || 0}</p>
                    </div>
                  </div>

                  <Separator className="bg-slate-800" />

                  {/* Required Behaviors */}
                  {(icpResult.icp?.criteria?.required_behaviors || []).length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-400" />
                        Required Behaviors
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {icpResult.icp.criteria.required_behaviors.map((behavior, i) => (
                          <Badge key={i} variant="outline" className="border-green-500/50 text-green-400">
                            {behavior}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Excluded Behaviors */}
                  {(icpResult.icp?.criteria?.excluded_behaviors || []).length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                        <X className="h-4 w-4 text-red-400" />
                        Excluded Behaviors
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {icpResult.icp.criteria.excluded_behaviors.map((behavior, i) => (
                          <Badge key={i} variant="outline" className="border-red-500/50 text-red-400">
                            {behavior}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Outreach Strategy */}
              {icpResult.icp?.outreach_strategy && (
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Megaphone className="h-5 w-5 text-orange-400" />
                      Outreach Strategy
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-300 whitespace-pre-line">{icpResult.icp.outreach_strategy}</p>
                  </CardContent>
                </Card>
              )}

              {/* Quick Tips */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-400" />
                    Next Steps
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    <li className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 text-orange-400 mt-0.5" />
                      <span className="text-slate-300">
                        Export matching wallets from the Wallets page using filters
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 text-orange-400 mt-0.5" />
                      <span className="text-slate-300">
                        Create targeted social posts using the Social page
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 text-orange-400 mt-0.5" />
                      <span className="text-slate-300">
                        Check activity patterns to find the best time to post
                      </span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-12 text-center">
                <Target className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-400 mb-2">No ICP Generated Yet</h3>
                <p className="text-sm text-slate-500">
                  Fill out the form and click Generate to create your ideal customer profile
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
