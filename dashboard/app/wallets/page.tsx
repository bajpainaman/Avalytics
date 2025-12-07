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

// Fetch function for infinite query
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

  // Intersection Observer for infinite scroll
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

  // Flatten all pages into single array
  const allWallets = data?.pages.flatMap((page) => page.wallets) || [];
  const totalWallets = data?.pages[0]?.total || 0;

  // Filter by search
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Wallet Explorer</h1>
          <p className="text-slate-400 mt-1">
            {totalWallets.toLocaleString()} wallets tracked • Showing {filteredWallets.length.toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            className="border-slate-700 hover:bg-slate-800"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={exportCSV}
            disabled={!allWallets.length}
            className="border-slate-700 hover:bg-slate-800"
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV ({allWallets.length})
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search by address..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-slate-800 border-slate-700"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-500" />
              <Button
                variant={filters.whale ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleFilter('whale')}
                className={filters.whale ? 'bg-blue-600' : 'border-slate-700'}
              >
                <Fish className="h-4 w-4 mr-1" />
                Whales
              </Button>
              <Button
                variant={filters.bot ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleFilter('bot')}
                className={filters.bot ? 'bg-purple-600' : 'border-slate-700'}
              >
                <Bot className="h-4 w-4 mr-1" />
                Bots
              </Button>
              <Button
                variant={filters.dex_user ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleFilter('dex_user')}
                className={filters.dex_user ? 'bg-green-600' : 'border-slate-700'}
              >
                <ArrowRightLeft className="h-4 w-4 mr-1" />
                DEX Users
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="p-0">
          <div className="max-h-[600px] overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-900 z-10">
                <TableRow className="border-slate-800 hover:bg-transparent">
                  <TableHead className="text-slate-400">Address</TableHead>
                  <TableHead className="text-slate-400 text-right">Transactions</TableHead>
                  <TableHead className="text-slate-400 text-right">Volume (AVAX)</TableHead>
                  <TableHead className="text-slate-400">Labels</TableHead>
                  <TableHead className="text-slate-400">First Seen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-orange-400" />
                      <p className="text-slate-400 mt-2">Loading wallets...</p>
                    </TableCell>
                  </TableRow>
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-red-400">
                      Failed to load wallets. Check API connection.
                    </TableCell>
                  </TableRow>
                ) : filteredWallets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-slate-500">
                      No wallets found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredWallets.map((wallet) => (
                    <TableRow
                      key={wallet.wallet_address}
                      className="border-slate-800 hover:bg-slate-800/50 cursor-pointer"
                      onClick={() => setSelectedWallet(wallet.wallet_address)}
                    >
                      <TableCell className="font-mono text-sm">
                        {wallet.wallet_address ? `${wallet.wallet_address.slice(0, 10)}...${wallet.wallet_address.slice(-6)}` : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right">{(wallet.total_txs || 0).toLocaleString()}</TableCell>
                      <TableCell className="text-right">{(wallet.volume_avax || 0).toFixed(4)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {wallet.is_whale && (
                            <Badge variant="outline" className="border-blue-500/50 text-blue-400 text-xs">
                              Whale
                            </Badge>
                          )}
                          {wallet.is_bot && (
                            <Badge variant="outline" className="border-purple-500/50 text-purple-400 text-xs">
                              Bot
                            </Badge>
                          )}
                          {wallet.is_dex_user && (
                            <Badge variant="outline" className="border-green-500/50 text-green-400 text-xs">
                              DEX
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {wallet.first_seen ? new Date(wallet.first_seen).toLocaleDateString() : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          
          {/* Infinite Scroll Trigger */}
          <div ref={loadMoreRef} className="py-4 text-center">
            {isFetchingNextPage ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
                <span className="text-slate-400">Loading more wallets...</span>
              </div>
            ) : hasNextPage ? (
              <Button
                variant="ghost"
                onClick={() => fetchNextPage()}
                className="text-slate-400 hover:text-white"
              >
                Load More
              </Button>
            ) : allWallets.length > 0 ? (
              <p className="text-slate-500 text-sm">All {totalWallets.toLocaleString()} wallets loaded</p>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* Wallet Detail Modal */}
      <Dialog open={!!selectedWallet} onOpenChange={() => setSelectedWallet(null)}>
        <DialogContent className="bg-slate-900 border-slate-800 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              Wallet Details
              <a
                href={`https://snowtrace.io/address/${selectedWallet}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-orange-400 hover:text-orange-300"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </DialogTitle>
          </DialogHeader>
          {walletDetail?.wallet ? (
            <div className="space-y-4">
              <div className="p-3 bg-slate-800 rounded-lg">
                <p className="font-mono text-sm break-all">{selectedWallet}</p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-sm text-slate-400">Transactions</p>
                  <p className="text-xl font-bold">{walletDetail.wallet.total_txs || 0}</p>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-sm text-slate-400">Volume</p>
                  <p className="text-xl font-bold">{(walletDetail.wallet.volume_avax || 0).toFixed(4)} AVAX</p>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-sm text-slate-400">Labels</p>
                  <div className="flex gap-1 mt-1">
                    {walletDetail.wallet.is_whale && <Badge className="bg-blue-600">Whale</Badge>}
                    {walletDetail.wallet.is_bot && <Badge className="bg-purple-600">Bot</Badge>}
                    {walletDetail.wallet.is_dex_user && <Badge className="bg-green-600">DEX</Badge>}
                    {!walletDetail.wallet.is_whale && !walletDetail.wallet.is_bot && !walletDetail.wallet.is_dex_user && (
                      <Badge variant="outline" className="border-slate-600">Normal</Badge>
                    )}
                  </div>
                </div>
              </div>

              {transactions?.transactions && transactions.transactions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-2">Recent Transactions</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {transactions.transactions.slice(0, 5).map((tx, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-slate-800/30 rounded text-sm">
                        <span className="font-mono text-slate-400">
                          {tx.hash ? `${tx.hash.slice(0, 10)}...` : 'N/A'}
                        </span>
                        <span>{(parseInt(tx.value || '0') / 1e18).toFixed(4)} AVAX</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
