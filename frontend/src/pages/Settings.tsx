import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useSettings, useUpdateSettings, useTestConnection } from '@/hooks/useApi';
import { useToast } from '@/hooks/use-toast';
import { Loader2, CheckCircle, XCircle, Sun, Moon } from 'lucide-react';

export function Settings() {
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();
  const testConnection = useTestConnection();
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    openrouter_api_key: '',
    openrouter_model: 'qwen/qwen-2.5-7b-instruct',
    temperature: 0.2,
    max_tokens: 2000,
    embedding_model: 'all-MiniLM-L6-v2',
    top_k_results: 5,
    llm_provider: 'openrouter',
  });

  const [isDark, setIsDark] = useState(
    document.documentElement.classList.contains('dark')
  );

  const [connectionResults, setConnectionResults] = useState<any>(null);

  useEffect(() => {
    if (settings) {
      setFormData({
        openrouter_api_key: settings.openrouter_api_key || '',
        openrouter_model: settings.openrouter_model || 'qwen/qwen-2.5-7b-instruct',
        temperature: settings.temperature ?? 0.2,
        max_tokens: settings.max_tokens ?? 2000,
        embedding_model: settings.embedding_model || 'all-MiniLM-L6-v2',
        top_k_results: settings.top_k_results ?? 5,
        llm_provider: settings.llm_provider || 'openrouter',
      });
    }
  }, [settings]);

  const handleChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      toast({ title: 'Settings saved', description: 'Your settings have been updated successfully.', variant: 'success' });
    } catch {
      // Error is already handled by API interceptor
    }
  };

  const handleTestConnection = async () => {
    try {
      const result = await testConnection.mutateAsync();
      setConnectionResults(result.data);
      toast({ title: 'Connection test complete', variant: 'success' });
    } catch {
      // Error is already handled by API interceptor
    }
  };

  const toggleDarkMode = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    if (newDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', newDark ? 'dark' : 'light');
  };

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>LLM Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="llm_provider">LLM Provider</Label>
              <Select value={formData.llm_provider} onValueChange={(v) => handleChange('llm_provider', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openrouter">OpenRouter</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="openrouter_api_key">API Key</Label>
              <Input
                id="openrouter_api_key"
                type="password"
                value={formData.openrouter_api_key}
                onChange={(e) => handleChange('openrouter_api_key', e.target.value)}
                placeholder="Enter API key"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="openrouter_model">Model</Label>
              <Select value={formData.openrouter_model} onValueChange={(v) => handleChange('openrouter_model', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="qwen/qwen-2.5-7b-instruct">GPT-OSS 20B (Free)</SelectItem>
                  <SelectItem value="meta-llama/llama-3-8b-instruct:free">Llama 3 8B (Free)</SelectItem>
                  <SelectItem value="anthropic/claude-3-haiku">Claude 3 Haiku</SelectItem>
                  <SelectItem value="openai/gpt-4o">GPT-4o</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="temperature">Temperature</Label>
              <Input
                id="temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                value={formData.temperature}
                onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_tokens">Max Tokens</Label>
              <Input
                id="max_tokens"
                type="number"
                min="100"
                max="8000"
                step="100"
                value={formData.max_tokens}
                onChange={(e) => handleChange('max_tokens', parseInt(e.target.value))}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="embedding_model">Embedding Model</Label>
              <Select value={formData.embedding_model} onValueChange={(v) => handleChange('embedding_model', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (384d)</SelectItem>
                  <SelectItem value="all-mpnet-base-v2">all-mpnet-base-v2 (768d)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="top_k_results">Top K Results</Label>
              <Input
                id="top_k_results"
                type="number"
                min="1"
                max="20"
                value={formData.top_k_results}
                onChange={(e) => handleChange('top_k_results', parseInt(e.target.value))}
              />
            </div>
          </div>

          <Button onClick={handleSave} disabled={updateSettings.isPending}>
            {updateSettings.isPending ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</>
            ) : 'Save Settings'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Dark Mode</p>
              <p className="text-sm text-muted-foreground">
                {isDark ? 'Currently enabled' : 'Currently disabled'}
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={toggleDarkMode}>
              {isDark ? <Sun className="h-4 w-4 mr-2" /> : <Moon className="h-4 w-4 mr-2" />}
              {isDark ? 'Light Mode' : 'Dark Mode'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connection Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={handleTestConnection} disabled={testConnection.isPending}>
            {testConnection.isPending ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Testing...</>
            ) : 'Test Connection'}
          </Button>

          {connectionResults && (
            <div className="space-y-3">
              {Object.entries(connectionResults).map(([key, value]: [string, any]) => (
                <div key={key} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-2">
                    {value.status === 'connected' || value.status === 'healthy' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500" />
                    )}
                    <span className="font-medium capitalize">{key}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={value.status === 'connected' || value.status === 'healthy' ? 'success' : 'destructive'}>
                      {value.status}
                    </Badge>
                    {value.provider && (
                      <Badge variant="outline">{value.provider}</Badge>
                    )}
                    {value.version && (
                      <Badge variant="outline">v{value.version}</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
