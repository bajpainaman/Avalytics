'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Wallet,
  Users,
  Activity,
  Target,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Wallets', href: '/wallets', icon: Wallet },
  { name: 'Cohorts', href: '/cohorts', icon: Users },
  { name: 'Patterns', href: '/patterns', icon: Activity },
  { name: 'ICP Generator', href: '/icp', icon: Target },
  { name: 'Social Posts', href: '/social', icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={cn(
        'flex flex-col h-screen bg-card border-r border-border transition-all duration-200',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-14 px-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-foreground rounded-md flex items-center justify-center">
              <BarChart3 className="h-4 w-4 text-background" />
            </div>
            <span className="text-[15px] font-semibold tracking-tight">Avalytics</span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 bg-foreground rounded-md flex items-center justify-center mx-auto">
            <BarChart3 className="h-4 w-4 text-background" />
          </div>
        )}
      </div>

      {/* Collapse Button */}
      <div className="px-3 py-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "w-full justify-start text-muted-foreground hover:text-foreground hover:bg-secondary",
            collapsed && "justify-center px-0"
          )}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          {!collapsed && <span className="ml-2 text-xs">Collapse</span>}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-secondary text-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              )}
            >
              <item.icon className="h-4 w-4 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-border">
        <div className={cn('flex items-center gap-3 px-2 py-1.5 rounded-md bg-secondary/50', collapsed && 'justify-center px-0')}>
          <div className="w-1.5 h-1.5 bg-foreground/50 rounded-full" />
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">Avalanche C-Chain</p>
              <p className="text-[10px] text-muted-foreground">Connected</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
