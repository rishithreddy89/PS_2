import { useState, useEffect, useRef } from 'react';
import { Bell, User, Search, X, Briefcase, FileText, Lightbulb, Settings, Loader2 } from 'lucide-react';
import { Input } from './ui/input';
import { useAppStore } from '@/store';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';
import { searchApi } from '@/services/api';

export function Navbar() {
  const { sidebarCollapsed } = useAppStore();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setShowProfile(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (searchQuery.length < 2) {
      setSearchResults(null);
      setShowResults(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await searchApi.search(searchQuery);
        setSearchResults(response.data);
        setShowResults(true);
      } catch {
        // Error handled by interceptor
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const handleResultClick = (type: string, id: string, caseId?: string) => {
    setShowResults(false);
    setSearchQuery('');
    switch (type) {
      case 'case':
        navigate(`/cases/${id}`);
        break;
      case 'document':
        navigate(`/cases/${caseId}`);
        break;
      case 'recommendation':
        navigate(`/cases/${caseId}`);
        break;
    }
  };

  const resultCount = searchResults?.total || 0;

  return (
    <div className={cn(
      "fixed top-0 right-0 h-16 bg-card border-b border-border flex items-center justify-between px-6 transition-all z-40",
      sidebarCollapsed ? "left-16" : "left-64"
    )}>
      {/* Search */}
      <div className="flex-1 max-w-xl" ref={searchRef}>
        <div className="relative">
          {isSearching ? (
            <Loader2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground animate-spin" />
          ) : (
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          )}
          <Input
            placeholder="Search cases, documents, recommendations..."
            className="pl-10 pr-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchResults && setShowResults(true)}
          />
          {searchQuery && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => { setSearchQuery(''); setShowResults(false); }}
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {/* Search Results Dropdown */}
          {showResults && searchResults && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg max-h-96 overflow-auto z-50">
              {resultCount === 0 ? (
                <div className="p-4 text-sm text-muted-foreground text-center">
                  No results found for "{searchQuery}"
                </div>
              ) : (
                <div className="py-2">
                  {searchResults.cases?.length > 0 && (
                    <div>
                      <p className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase">Cases</p>
                      {searchResults.cases.map((r: any) => (
                        <button
                          key={r.id}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent text-left"
                          onClick={() => handleResultClick('case', r.id)}
                        >
                          <Briefcase className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm truncate">{r.title}</p>
                            <p className="text-xs text-muted-foreground">{r.case_number}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {searchResults.documents?.length > 0 && (
                    <div>
                      <p className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase">Documents</p>
                      {searchResults.documents.map((r: any) => (
                        <button
                          key={r.id}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent text-left"
                          onClick={() => handleResultClick('document', r.id, r.case_id)}
                        >
                          <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm truncate">{r.title}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {searchResults.recommendations?.length > 0 && (
                    <div>
                      <p className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase">Recommendations</p>
                      {searchResults.recommendations.map((r: any) => (
                        <button
                          key={r.id}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent text-left"
                          onClick={() => handleResultClick('recommendation', r.id, r.case_id)}
                        >
                          <Lightbulb className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm truncate">{r.title}</p>
                            <p className="text-xs text-muted-foreground">{r.status}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            className="p-2 hover:bg-accent rounded-md relative"
            onClick={() => { setShowNotifications(!showNotifications); setShowProfile(false); }}
          >
            <Bell className="h-5 w-5" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 top-full mt-1 w-80 bg-card border border-border rounded-lg shadow-lg z-50">
              <div className="p-3 border-b border-border">
                <p className="font-medium text-sm">Notifications</p>
              </div>
              <div className="p-4 text-sm text-muted-foreground text-center">
                No new notifications
              </div>
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative" ref={profileRef}>
          <button
            className="p-2 hover:bg-accent rounded-md"
            onClick={() => { setShowProfile(!showProfile); setShowNotifications(false); }}
          >
            <User className="h-5 w-5" />
          </button>

          {showProfile && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg shadow-lg z-50 py-1">
              <button
                className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
                onClick={() => { navigate('/settings'); setShowProfile(false); }}
              >
                <Settings className="h-4 w-4" />
                Settings
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
