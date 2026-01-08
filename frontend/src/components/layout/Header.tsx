import { DarkModeToggle } from './DarkModeToggle';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';

export function Header() {
  const { isSidebarCollapsed } = useAppStore();

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-16 bg-background border-b border-border transition-all duration-300 flex items-center justify-between px-6',
        isSidebarCollapsed ? 'left-16' : 'left-64'
      )}
    >
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Regulatory Intelligence</h2>
      </div>

      <div className="flex items-center gap-4">
        <DarkModeToggle />
      </div>
    </header>
  );
}
