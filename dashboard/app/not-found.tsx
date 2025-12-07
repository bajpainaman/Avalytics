import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
      <h2 className="text-4xl font-bold">404</h2>
      <p className="text-slate-400">Page not found</p>
      <Link href="/">
        <Button variant="outline">
          <Home className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </Link>
    </div>
  );
}
