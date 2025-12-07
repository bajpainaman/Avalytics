'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getPostTemplates, generatePost, GeneratedPost } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  MessageSquare,
  Sparkles,
  Twitter,
  Copy,
  Check,
  Loader2,
  ExternalLink,
  BarChart3,
  AlertTriangle,
  Zap,
  PenLine,
  AlertCircle,
} from 'lucide-react';

const templateIcons: Record<string, React.ReactNode> = {
  stats: <BarChart3 className="h-5 w-5" />,
  whale_alert: <AlertTriangle className="h-5 w-5" />,
  trends: <Zap className="h-5 w-5" />,
  custom: <PenLine className="h-5 w-5" />,
};

export default function SocialPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('stats');
  const [customPrompt, setCustomPrompt] = useState('');
  const [generatedPost, setGeneratedPost] = useState<GeneratedPost | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: templates } = useQuery({
    queryKey: ['postTemplates'],
    queryFn: getPostTemplates,
  });

  const generateMutation = useMutation({
    mutationFn: () => generatePost(selectedTemplate),
    onSuccess: (data) => {
      setGeneratedPost(data);
    },
  });

  const handleCopy = () => {
    if (generatedPost?.ready?.content) {
      navigator.clipboard.writeText(generatedPost.ready.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePostToX = () => {
    if (generatedPost?.ready?.intent_url) {
      window.open(generatedPost.ready.intent_url, '_blank');
    }
  };

  const charCount = generatedPost?.ready?.character_count || 0;
  const isOverLimit = charCount > 280;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Social Posts</h1>
        <p className="text-slate-400 mt-1">
          Generate AI-powered posts for X using real analytics data
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Template Selection & Generation */}
        <div className="space-y-6">
          {/* Template Selection */}
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle>Choose Template</CardTitle>
              <CardDescription>
                Select a template type for your post
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {(templates?.templates || [
                  { id: 'stats', name: 'Weekly Stats', description: 'Share network statistics' },
                  { id: 'whale_alert', name: 'Whale Alert', description: 'Large wallet movements' },
                  { id: 'trends', name: 'Trends Analysis', description: 'Week-over-week trends' },
                  { id: 'custom', name: 'Custom Post', description: 'Your own prompt' },
                ]).map((template) => (
                  <button
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`p-4 rounded-lg border text-left transition-all ${
                      selectedTemplate === template.id
                        ? 'bg-gradient-to-br from-orange-500/20 to-red-500/20 border-orange-500/50'
                        : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className={selectedTemplate === template.id ? 'text-orange-400' : 'text-slate-400'}>
                        {templateIcons[template.id] || <MessageSquare className="h-5 w-5" />}
                      </span>
                      <span className="font-medium">{template.name}</span>
                    </div>
                    <p className="text-xs text-slate-400">{template.description}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Custom Prompt (if custom selected) */}
          {selectedTemplate === 'custom' && (
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle>Custom Prompt</CardTitle>
                <CardDescription>
                  Tell the AI what kind of post you want
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="e.g., Create a thread about why on-chain analytics matters for crypto marketing..."
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  className="bg-slate-800 border-slate-700 min-h-[100px]"
                />
              </CardContent>
            </Card>
          )}

          {/* Generate Button */}
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending || (selectedTemplate === 'custom' && !customPrompt.trim())}
            className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 h-12 text-lg"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5 mr-2" />
                Generate Post
              </>
            )}
          </Button>

          {generateMutation.isError && (
            <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-sm text-red-400">
              <AlertCircle className="h-4 w-4" />
              Failed to generate post. Check if API is running and OpenAI key is set.
            </div>
          )}

          {/* Data Notice */}
          <div className="flex items-start gap-2 p-3 bg-slate-800/50 rounded-lg text-sm text-slate-400">
            <BarChart3 className="h-4 w-4 mt-0.5 text-orange-400 flex-shrink-0" />
            <p>
              Posts are generated using real data from your Avalytics database, including
              wallet counts, transaction volumes, and behavioral patterns.
            </p>
          </div>
        </div>

        {/* Right: Preview & Actions */}
        <div className="space-y-6">
          {/* Preview Card */}
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Twitter className="h-5 w-5 text-[#1DA1F2]" />
                  Post Preview
                </CardTitle>
                {generatedPost && (
                  <Badge 
                    variant="outline" 
                    className={isOverLimit ? 'border-red-500 text-red-400' : 'border-slate-600'}
                  >
                    {charCount}/280
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {generateMutation.isPending ? (
                <div className="h-48 flex items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
                </div>
              ) : generatedPost?.ready?.content ? (
                <div className="space-y-4">
                  {/* Tweet Preview */}
                  <div className="p-4 bg-slate-800 rounded-lg border border-slate-700">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center font-bold flex-shrink-0">
                        A
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-bold">Avalytics</span>
                          <span className="text-slate-500">@avalytics</span>
                        </div>
                        <p className="mt-2 whitespace-pre-wrap text-slate-200 break-words">
                          {generatedPost.ready.content}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Thread indicator */}
                  {generatedPost.generated?.is_thread && (
                    <Badge variant="outline" className="border-blue-500/50 text-blue-400">
                      Thread: {generatedPost.generated.tweets?.length || 1} tweets
                    </Badge>
                  )}

                  {/* Warning if over limit */}
                  {isOverLimit && (
                    <div className="flex items-center gap-2 p-2 bg-red-500/20 border border-red-500/50 rounded-lg text-sm text-red-400">
                      <AlertTriangle className="h-4 w-4" />
                      Post exceeds 280 characters. It may be truncated.
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-48 flex flex-col items-center justify-center text-slate-500">
                  <MessageSquare className="h-12 w-12 mb-3 text-slate-600" />
                  <p>Your generated post will appear here</p>
                  <p className="text-sm mt-1">Select a template and click Generate</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Action Buttons */}
          {generatedPost?.ready?.content && (
            <div className="space-y-3">
              <Button
                onClick={handlePostToX}
                className="w-full bg-[#1DA1F2] hover:bg-[#1a8cd8] h-12 text-lg"
              >
                <Twitter className="h-5 w-5 mr-2" />
                Post to X
                <ExternalLink className="h-4 w-4 ml-2" />
              </Button>

              <Button
                onClick={handleCopy}
                variant="outline"
                className="w-full border-slate-700 hover:bg-slate-800"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 mr-2 text-green-400" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-2" />
                    Copy to Clipboard
                  </>
                )}
              </Button>

              <Button
                onClick={() => generateMutation.mutate()}
                variant="ghost"
                className="w-full text-slate-400 hover:text-white"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                Regenerate
              </Button>
            </div>
          )}

          {/* Thread Preview (if thread) */}
          {generatedPost?.generated?.is_thread && (generatedPost.generated.tweets?.length || 0) > 1 && (
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle>Full Thread</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(generatedPost.generated.tweets || []).map((tweet, i) => (
                    <div key={i} className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="border-slate-600 text-xs">
                          {i + 1}/{generatedPost.generated.tweets?.length || 1}
                        </Badge>
                        <span className="text-xs text-slate-500">
                          {tweet?.length || 0} chars
                        </span>
                      </div>
                      <p className="text-sm text-slate-300 whitespace-pre-wrap">{tweet}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Tips */}
          <Card className="bg-slate-800/30 border-slate-800">
            <CardContent className="p-4">
              <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-orange-400" />
                Pro Tips
              </h4>
              <ul className="text-xs text-slate-400 space-y-1">
                <li>• Check the Patterns page for best posting times</li>
                <li>• Whale alerts create urgency and FOMO</li>
                <li>• Stats posts are great for establishing authority</li>
                <li>• Use custom prompts for unique campaign content</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
