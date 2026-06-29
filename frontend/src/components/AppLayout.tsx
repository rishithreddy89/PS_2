import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/Sidebar';
import { Navbar } from '@/components/Navbar';
import { Toaster } from '@/components/ui/Toaster';
import { useAppStore } from '@/store';
import { cn } from '@/lib/utils';

export function AppLayout() {
  const { sidebarCollapsed } = useAppStore();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <Navbar />
      <main className={cn(
        "pt-16 transition-all",
        sidebarCollapsed ? "ml-16" : "ml-64"
      )}>
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
