'use client';

import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="bg-slate-950 text-white">
        <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
          <h2 className="text-2xl font-bold text-red-500">Something went wrong!</h2>
          <p className="text-slate-400">{error.message}</p>
          <Button onClick={() => reset()}>Try again</Button>
        </div>
      </body>
    </html>
  );
}
