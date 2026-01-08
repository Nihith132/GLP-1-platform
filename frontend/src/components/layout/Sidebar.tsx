import { Link, useLocation } from 'react-router-dom';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  BarChart3,
  GitCompare,
  FileText,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Comparison', href: '/comparison', icon: GitCompare },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Version Checker', href: '/version-checker', icon: CheckCircle2 },
];

export function Sidebar() {
  const location = useLocation();
  const { isSidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <div
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-card border-r border-border transition-all duration-300',
        isSidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!isSidebarCollapsed && (
          <h1 className="text-xl font-bold text-primary">GLP-1 Platform</h1>
        )}
        <button
          onClick={toggleSidebar}
          className="ml-auto p-2 rounded-md hover:bg-accent transition-colors"
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="mt-4 px-2 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
              title={isSidebarCollapsed ? item.name : undefined}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!isSidebarCollapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
