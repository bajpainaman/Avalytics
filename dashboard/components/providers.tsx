'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { getStats, getCohorts, analyzePatterns, getHeatmap } from '@/lib/api';

// Create a client with aggressive caching
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Data stays fresh for 5 minutes - no refetch during this time
        staleTime: 5 * 60 * 1000,
        // Keep unused data in cache for 30 minutes
        gcTime: 30 * 60 * 1000,
        // Don't refetch on window focus (annoying)
        refetchOnWindowFocus: false,
        // Don't refetch on reconnect
        refetchOnReconnect: false,
        // Retry failed requests once
        retry: 1,
        // Show stale data while revalidating in background
        refetchOnMount: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(getQueryClient);

  // Prefetch common data on mount
  useEffect(() => {
    // Prefetch dashboard stats immediately
    queryClient.prefetchQuery({
      queryKey: ['stats'],
      queryFn: getStats,
      staleTime: 5 * 60 * 1000,
    });

    // Prefetch patterns in background
    queryClient.prefetchQuery({
      queryKey: ['patterns', '7'],
      queryFn: () => analyzePatterns(7),
      staleTime: 5 * 60 * 1000,
    });

    // Prefetch heatmap
    queryClient.prefetchQuery({
      queryKey: ['heatmap', 30],
      queryFn: () => getHeatmap(30),
      staleTime: 10 * 60 * 1000,
    });

    // Prefetch cohorts after a short delay
    setTimeout(() => {
      queryClient.prefetchQuery({
        queryKey: ['cohorts'],
        queryFn: getCohorts,
        staleTime: 5 * 60 * 1000,
      });
    }, 1000);
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
