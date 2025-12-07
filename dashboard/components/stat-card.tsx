import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
}

export function StatCard({ title, value, subtitle, icon: Icon, trend, className }: StatCardProps) {
  return (
    <Card className={cn('bg-slate-900 border-slate-800', className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm text-slate-400">{title}</p>
            <p className="text-3xl font-bold text-white">{value}</p>
            {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
            {trend && (
              <p
                className={cn(
                  'text-xs font-medium',
                  trend.value >= 0 ? 'text-green-400' : 'text-red-400'
                )}
              >
                {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
              </p>
            )}
          </div>
          <div className="p-3 bg-gradient-to-br from-red-500/20 to-orange-500/20 rounded-lg">
            <Icon className="h-6 w-6 text-orange-400" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
