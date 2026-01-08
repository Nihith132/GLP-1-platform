import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';

export function Layout() {
  const { isSidebarCollapsed } = useAppStore();

  return (
    <div className="min-h-screen relative">
      {/* Gradient Mesh Background */}
      <div className="fixed inset-0 gradient-mesh pointer-events-none" />
      
      {/* Content */}
      <div className="relative">
        <Sidebar />
        <Header />
        <main
          className={cn(
            'pt-16 transition-all duration-300 ease-out',
            isSidebarCollapsed ? 'ml-16' : 'ml-64'
          )}
        >
          <div className="p-6 max-w-[1920px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
