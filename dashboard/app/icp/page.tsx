'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generateICP, searchWallets, generateICPCampaignPost, ICPResponse, ICPCampaignPost } from '@/lib/api';
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
  Twitter,
  ExternalLink,
  Copy,
} from 'lucide-react';

export default function ICPPage() {
  const [formData, setFormData] = useState({
    protocol_name: '',
    protocol_description: '',
    target_audience: '',
  });
  const [icpResult, setIcpResult] = useState<ICPResponse | null>(null);
  const [nlQuery, setNlQuery] = useState('');
  const [campaignPost, setCampaignPost] = useState<ICPCampaignPost | null>(null);
  const [copied, setCopied] = useState(false);

  const generateMutation = useMutation({
    mutationFn: generateICP,
    onSuccess: (data) => {
      setIcpResult(data);
      setCampaignPost(null); // Reset campaign post when new ICP generated
    },
  });

  const searchMutation = useMutation({
    mutationFn: searchWallets,
  });

  const campaignMutation = useMutation({
    mutationFn: generateICPCampaignPost,
    onSuccess: (data) => {
      setCampaignPost(data);
    },
  });

  const handleGenerate = () => {
    if (!formData.protocol_name || !formData.protocol_description) return;
    generateMutation.mutate(formData);
  };

  const handleNLSearch = () => {
    if (!nlQuery.trim()) return;
    searchMutation.mutate(nlQuery);
  };

  const handleGenerateCampaign = () => {
    if (!icpResult) return;
    campaignMutation.mutate({
      protocol_name: formData.protocol_name,
      icp_name: icpResult.icp?.name || 'Target Audience',
      icp_description: icpResult.icp?.description || '',
      outreach_strategy: icpResult.icp?.outreach_strategy || '',
      matching_wallets: icpResult.matching_wallets || 0,
      required_behaviors: icpResult.icp?.criteria?.required_behaviors || [],
      post_type: 'launch',
    });
  };

  const handleCopyCampaign = () => {
    if (campaignPost?.content) {
      navigator.clipboard.writeText(campaignPost.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePostToX = () => {
    if (campaignPost?.intent_url) {
      window.open(campaignPost.intent_url, '_blank');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">ICP Generator</h1>
        <p className="text-muted-foreground mt-1">
          AI-powered Ideal Customer Profile generation for your protocol
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="space-y-6">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-muted-foreground" />
                Define Your Protocol
              </CardTitle>
              <CardDescription>
                Tell us about your protocol and we&apos;ll generate an ideal customer profile
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">
                  Protocol Name *
                </label>
                <Input
                  placeholder="e.g., DeFi Lending Protocol"
                  value={formData.protocol_name}
                  onChange={(e) => setFormData({ ...formData, protocol_name: e.target.value })}
                  className="bg-secondary border-border"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">
                  Description *
                </label>
                <Textarea
                  placeholder="Describe what your protocol does, its key features, and value proposition..."
                  value={formData.protocol_description}
                  onChange={(e) => setFormData({ ...formData, protocol_description: e.target.value })}
                  className="bg-secondary border-border min-h-[120px]"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">
                  Target Audience (optional)
                </label>
                <Input
                  placeholder="e.g., DeFi power users, yield farmers, institutional traders"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  className="bg-secondary border-border"
                />
              </div>

              <Button
                onClick={handleGenerate}
                disabled={generateMutation.isPending || !formData.protocol_name || !formData.protocol_description}
                className="w-full"
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
                <div className="flex items-center gap-2 p-3 bg-secondary border border-border rounded-lg text-sm text-muted-foreground">
                  <AlertCircle className="h-4 w-4" />
                  Failed to generate ICP. Check if API is running and OpenAI key is set.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Natural Language Search */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-muted-foreground" />
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
                className="bg-secondary border-border"
              />
              <Button
                onClick={handleNLSearch}
                disabled={searchMutation.isPending || !nlQuery.trim()}
                variant="outline"
                className="w-full border-border hover:bg-secondary"
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
                <div className="flex items-center gap-2 p-3 bg-secondary border border-border rounded-lg text-sm text-muted-foreground">
                  <AlertCircle className="h-4 w-4" />
                  Search failed. Check API connection.
                </div>
              )}

              {/* Search Results */}
              {searchMutation.data && (
                <div className="mt-4 p-4 bg-secondary/50 rounded-lg space-y-3">
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
                    <div key={wallet.wallet_address} className="flex items-center justify-between p-2 bg-secondary rounded">
                      <code className="text-xs">
                        {wallet.wallet_address ? `${wallet.wallet_address.slice(0, 10)}...${wallet.wallet_address.slice(-6)}` : 'N/A'}
                      </code>
                      <span className="text-sm text-muted-foreground">{(wallet.volume_avax || 0).toFixed(2)} AVAX</span>
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
              <Card className="bg-card border-border">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-muted-foreground" />
                      {icpResult.icp?.name || 'Generated ICP'}
                    </CardTitle>
                    <Badge variant="secondary">
                      <Users className="h-3 w-3 mr-1" />
                      {icpResult.matching_wallets || 0} matches
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-foreground">{icpResult.icp?.description || 'No description available'}</p>
                </CardContent>
              </Card>

              {/* Criteria */}
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Check className="h-5 w-5 text-foreground" />
                    Targeting Criteria
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Min Transactions</p>
                      <p className="text-xl font-bold">{icpResult.icp?.criteria?.min_transaction_count || 0}</p>
                    </div>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Min Volume (USD)</p>
                      <p className="text-xl font-bold">${(icpResult.icp?.criteria?.min_volume_usd || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Wallet Age</p>
                      <p className="text-xl font-bold">{icpResult.icp?.criteria?.wallet_age_days || 0} days</p>
                    </div>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Matches Found</p>
                      <p className="text-xl font-bold">{(icpResult.matching_wallets || 0).toLocaleString()}</p>
                    </div>
                  </div>

                  <Separator className="bg-secondary" />

                  {/* Required Behaviors */}
                  {(icpResult.icp?.criteria?.required_behaviors || []).length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                        <Check className="h-4 w-4 text-foreground" />
                        Required Behaviors
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {icpResult.icp.criteria.required_behaviors.map((behavior, i) => (
                          <Badge key={i} variant="secondary">
                            {behavior}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Excluded Behaviors */}
                  {(icpResult.icp?.criteria?.excluded_behaviors || []).length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                        <X className="h-4 w-4 text-muted-foreground" />
                        Excluded Behaviors
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {icpResult.icp.criteria.excluded_behaviors.map((behavior, i) => (
                          <Badge key={i} variant="outline">
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
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Megaphone className="h-5 w-5 text-muted-foreground" />
                      Outreach Strategy
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground whitespace-pre-line">{icpResult.icp.outreach_strategy}</p>
                  </CardContent>
                </Card>
              )}

              {/* X Campaign Post Generator */}
              <Card className="bg-gradient-to-br from-[#1DA1F2]/10 to-slate-900 border-[#1DA1F2]/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Twitter className="h-5 w-5 text-[#1DA1F2]" />
                    Create X Campaign
                  </CardTitle>
                  <CardDescription>
                    Generate a marketing post targeting your ICP audience
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!campaignPost ? (
                    <Button
                      onClick={handleGenerateCampaign}
                      disabled={campaignMutation.isPending}
                      className="w-full bg-[#1DA1F2] hover:bg-[#1a8cd8]"
                    >
                      {campaignMutation.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Generating Campaign Post...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4 mr-2" />
                          Generate X Campaign Post
                        </>
                      )}
                    </Button>
                  ) : (
                    <div className="space-y-4">
                      {/* Tweet Preview */}
                      <div className="p-4 bg-secondary rounded-lg border border-border">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center font-bold flex-shrink-0">
                            A
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-bold">Avalytics</span>
                              <span className="text-muted-foreground/60">@avalytics</span>
                            </div>
                            <p className="mt-2 whitespace-pre-wrap text-slate-200 break-words">
                              {campaignPost.content}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>{campaignPost.character_count}/280 characters</span>
                        <Badge variant="secondary">
                          Ready to post
                        </Badge>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2">
                        <Button
                          onClick={handlePostToX}
                          className="flex-1 bg-[#1DA1F2] hover:bg-[#1a8cd8]"
                        >
                          <Twitter className="h-4 w-4 mr-2" />
                          Post to X
                          <ExternalLink className="h-3 w-3 ml-2" />
                        </Button>
                        <Button
                          onClick={handleCopyCampaign}
                          variant="outline"
                          className="border-border hover:bg-secondary"
                        >
                          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </Button>
                        <Button
                          onClick={handleGenerateCampaign}
                          variant="outline"
                          className="border-border hover:bg-secondary"
                          disabled={campaignMutation.isPending}
                        >
                          <Sparkles className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}

                  {campaignMutation.isError && (
                    <div className="flex items-center gap-2 p-3 bg-secondary border border-border rounded-lg text-sm text-muted-foreground">
                      <AlertCircle className="h-4 w-4" />
                      Failed to generate campaign post. Check if OpenAI key is set.
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Tips */}
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-muted-foreground" />
                    Next Steps
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    <li className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <span className="text-foreground">
                        Export matching wallets from the Wallets page using filters
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <span className="text-foreground">
                        Create targeted social posts using the Social page
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <span className="text-foreground">
                        Check activity patterns to find the best time to post
                      </span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="bg-card border-border">
              <CardContent className="p-12 text-center">
                <Target className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">No ICP Generated Yet</h3>
                <p className="text-sm text-muted-foreground/60">
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
