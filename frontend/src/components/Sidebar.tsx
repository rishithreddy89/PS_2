import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Briefcase, 
  Brain, 
  MemoryStick, 
  Settings,
  Menu,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: Briefcase, label: 'Cases', path: '/cases' },
  { icon: Brain, label: 'Planner', path: '/planner' },
  { icon: MemoryStick, label: 'Memory', path: '/memory' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar() {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <div className={cn(
      "fixed left-0 top-0 h-screen bg-card border-r border-border transition-all",
      sidebarCollapsed ? "w-16" : "w-64"
    )}>
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!sidebarCollapsed && <h1 className="text-xl font-bold">LexMind AI</h1>}
        <button onClick={toggleSidebar} className="p-2 hover:bg-accent rounded-md">
          <Menu className="h-5 w-5" />
        </button>
      </div>
      
      <nav className="p-2 space-y-1">
        {navItems.map(({ icon: Icon, label, path }) => (
          <Link
            key={path}
            to={path}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
              location.pathname === path
                ? "bg-accent text-accent-foreground"
                : "hover:bg-accent/50"
            )}
          >
            <Icon className="h-5 w-5 flex-shrink-0" />
            {!sidebarCollapsed && <span>{label}</span>}
          </Link>
        ))}
      </nav>
    </div>
  );
}
