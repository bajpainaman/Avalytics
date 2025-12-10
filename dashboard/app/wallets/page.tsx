'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { getWallet, getWalletTransactions } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Search,
  Filter,
  Download,
  Fish,
  Bot,
  ArrowRightLeft,
  ExternalLink,
  Loader2,
  RefreshCw,
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'demo-key-123';

interface WalletProfile {
  wallet_address: string;
  total_txs: number;
  volume_avax: number;
  is_whale: boolean;
  is_bot: boolean;
  is_dex_user: boolean;
  first_seen: string;
  last_seen: string;
}

interface WalletsResponse {
  wallets: WalletProfile[];
  total: number;
  page: number;
  limit: number;
}

async function fetchWallets(
  page: number,
  limit: number,
  filters: { whale?: boolean; bot?: boolean; dex_user?: boolean }
): Promise<WalletsResponse> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (filters?.whale) params.append('whale', 'true');
  if (filters?.bot) params.append('bot', 'true');
  if (filters?.dex_user) params.append('dex_user', 'true');
  
  const response = await fetch(`${API_BASE}/api/v1/wallets?${params}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
  });
  
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export default function WalletsPage() {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<{ whale?: boolean; bot?: boolean; dex_user?: boolean }>({});
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const ITEMS_PER_PAGE = 50;

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['wallets', filters],
    queryFn: ({ pageParam = 1 }) => fetchWallets(pageParam, ITEMS_PER_PAGE, filters),
    getNextPageParam: (lastPage) => {
      const totalPages = Math.ceil(lastPage.total / ITEMS_PER_PAGE);
      if (lastPage.page < totalPages) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    initialPageParam: 1,
    staleTime: 5 * 60 * 1000, // 5 min cache
    gcTime: 30 * 60 * 1000, // Keep in cache 30 min
  });

  const { data: walletDetail } = useQuery({
    queryKey: ['wallet', selectedWallet],
    queryFn: () => (selectedWallet ? getWallet(selectedWallet) : null),
    enabled: !!selectedWallet,
  });

  const { data: transactions } = useQuery({
    queryKey: ['walletTxs', selectedWallet],
    queryFn: () => (selectedWallet ? getWalletTransactions(selectedWallet, 10) : null),
    enabled: !!selectedWallet,
  });

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage]
  );

  useEffect(() => {
    const element = loadMoreRef.current;
    if (!element) return;

    observerRef.current = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: '100px',
      threshold: 0,
    });

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [handleObserver]);

  const toggleFilter = (key: 'whale' | 'bot' | 'dex_user') => {
    setFilters((prev) => ({
      ...prev,
      [key]: prev[key] ? undefined : true,
    }));
  };

  const allWallets = data?.pages.flatMap((page) => page.wallets) || [];
  const totalWallets = data?.pages[0]?.total || 0;

  const filteredWallets = allWallets.filter((w) =>
    search ? w.wallet_address?.toLowerCase().includes(search.toLowerCase()) : true
  );

  const exportCSV = () => {
    if (!allWallets.length) return;
    
    const csv = [
      ['Address', 'Transactions', 'Volume (AVAX)', 'Whale', 'Bot', 'DEX User', 'First Seen', 'Last Seen'],
      ...allWallets.map((w) => [
        w.wallet_address,
        w.total_txs,
        (w.volume_avax || 0).toFixed(4),
        w.is_whale,
        w.is_bot,
        w.is_dex_user,
        w.first_seen,
        w.last_seen,
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wallets-${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Wallet Explorer</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            {totalWallets.toLocaleString()} wallets tracked • Showing {filteredWallets.length.toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="h-8 text-xs"
          >
            <RefreshCw className="h-3 w-3 mr-1.5" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportCSV}
            disabled={!allWallets.length}
            className="h-8 text-xs"
          >
            <Download className="h-3 w-3 mr-1.5" />
            Export ({allWallets.length})
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by address..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 bg-secondary/50"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Button
                variant={filters.whale ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleFilter('whale')}
                className={`h-8 text-xs ${filters.whale ? 'bg-primary' : ''}`}
              >
                <Fish className="h-3 w-3 mr-1.5" />
                Whales
              </Button>
              <Button
                variant={filters.bot ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleFilter('bot')}
                className={`h-8 text-xs ${filters.bot ? 'bg-primary' : ''}`}
              >
                <Bot className="h-3 w-3 mr-1.5" />
                Bots
              </Button>
              <Button
                variant={filters.dex_user ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleFilter('dex_user')}
                className={`h-8 text-xs ${filters.dex_user ? 'bg-primary' : ''}`}
              >
                <ArrowRightLeft className="h-3 w-3 mr-1.5" />
                DEX Users
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="max-h-[600px] overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-card z-10">
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Address</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide text-right">Transactions</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide text-right">Volume (AVAX)</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Labels</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">First Seen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading && !data ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-96">
                      <div className="flex flex-col items-center justify-center h-full gap-6">
                        {/* Animated Line Loader */}
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
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Loading wallets</p>
                          <p className="text-xs text-muted-foreground/60 mt-1">Fetching on-chain data...</p>
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12 text-destructive">
                      Failed to load wallets. Check API connection.
                    </TableCell>
                  </TableRow>
                ) : filteredWallets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                      No wallets found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredWallets.map((wallet) => (
                    <TableRow
                      key={wallet.wallet_address}
                      className="border-border hover:bg-secondary/50 cursor-pointer"
                      onClick={() => setSelectedWallet(wallet.wallet_address)}
                    >
                      <TableCell className="font-mono text-xs">
                        {wallet.wallet_address ? `${wallet.wallet_address.slice(0, 10)}...${wallet.wallet_address.slice(-6)}` : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right text-sm">{(wallet.total_txs || 0).toLocaleString()}</TableCell>
                      <TableCell className="text-right text-sm">{(wallet.volume_avax || 0).toFixed(4)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {wallet.is_whale && (
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 text-blue-400">
                              Whale
                            </Badge>
                          )}
                          {wallet.is_bot && (
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 text-purple-400">
                              Bot
                            </Badge>
                          )}
                          {wallet.is_dex_user && (
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 text-green-400">
                              DEX
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {wallet.first_seen ? new Date(wallet.first_seen).toLocaleDateString() : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          
          {/* Infinite Scroll Trigger */}
          <div ref={loadMoreRef} className="py-4 text-center border-t border-border">
            {isFetchingNextPage ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-muted-foreground text-sm">Loading more...</span>
              </div>
            ) : hasNextPage ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fetchNextPage()}
                className="text-muted-foreground text-xs"
              >
                Load More
              </Button>
            ) : allWallets.length > 0 ? (
              <p className="text-muted-foreground text-xs">All {totalWallets.toLocaleString()} wallets loaded</p>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* Wallet Detail Modal */}
      <Dialog open={!!selectedWallet} onOpenChange={() => setSelectedWallet(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base font-medium">
              Wallet Details
              <a
                href={`https://snowtrace.io/address/${selectedWallet}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </DialogTitle>
          </DialogHeader>
          {walletDetail?.wallet ? (
            <div className="space-y-4">
              <div className="p-3 bg-secondary/50 rounded-md">
                <p className="font-mono text-xs break-all text-muted-foreground">{selectedWallet}</p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-secondary/30 rounded-md">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Transactions</p>
                  <p className="text-xl font-semibold mt-1">{walletDetail.wallet.total_txs || 0}</p>
                </div>
                <div className="p-3 bg-secondary/30 rounded-md">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Volume</p>
                  <p className="text-xl font-semibold mt-1">{(walletDetail.wallet.volume_avax || 0).toFixed(4)}</p>
                </div>
                <div className="p-3 bg-secondary/30 rounded-md">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Labels</p>
                  <div className="flex gap-1 mt-2">
                    {walletDetail.wallet.is_whale && <Badge variant="secondary" className="text-blue-400">Whale</Badge>}
                    {walletDetail.wallet.is_bot && <Badge variant="secondary" className="text-purple-400">Bot</Badge>}
                    {walletDetail.wallet.is_dex_user && <Badge variant="secondary" className="text-green-400">DEX</Badge>}
                    {!walletDetail.wallet.is_whale && !walletDetail.wallet.is_bot && !walletDetail.wallet.is_dex_user && (
                      <Badge variant="secondary">Normal</Badge>
                    )}
                  </div>
                </div>
              </div>

              {transactions?.transactions && transactions.transactions.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Recent Transactions</h4>
                  <div className="space-y-1.5 max-h-40 overflow-y-auto">
                    {transactions.transactions.slice(0, 5).map((tx, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-secondary/20 rounded-md text-xs">
                        <span className="font-mono text-muted-foreground">
                          {tx.hash ? `${tx.hash.slice(0, 14)}...` : 'N/A'}
                        </span>
                        <span className="font-medium">{(parseInt(tx.value || '0') / 1e18).toFixed(4)} AVAX</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
