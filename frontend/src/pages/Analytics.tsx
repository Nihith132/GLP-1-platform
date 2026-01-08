import { useState, useEffect } from 'react';
import { analyticsService, PlatformAnalytics } from '@/services/analyticsService';
import { Loading } from '../components/ui/Loading';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Database, TrendingUp, Package } from 'lucide-react';

export function Analytics() {
  const [analytics, setAnalytics] = useState<PlatformAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await analyticsService.getPlatformAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Loading size="lg" text="Loading analytics..." />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center space-y-4">
          <p className="text-lg text-muted-foreground">{error || 'No analytics data available'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Analytics</h1>
        <p className="text-muted-foreground mt-2">
          Platform insights and statistics
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Drugs</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_drugs}</div>
            <p className="text-xs text-muted-foreground">Unique drug products</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Manufacturers</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_manufacturers}</div>
            <p className="text-xs text-muted-foreground">Pharmaceutical companies</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Drug Types</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_drug_types}</div>
            <p className="text-xs text-muted-foreground">Generic drug classes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Labels</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.active_labels}</div>
            <p className="text-xs text-muted-foreground">Current versions</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Manufacturers Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Top Manufacturers</CardTitle>
            <p className="text-sm text-muted-foreground">Drug distribution by pharmaceutical company</p>
          </CardHeader>
          <CardContent>
            {analytics.manufacturers.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.manufacturers}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px]">
                <p className="text-sm text-muted-foreground">No manufacturer data available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Drug Types Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Drug Types Distribution</CardTitle>
            <p className="text-sm text-muted-foreground">Drugs by generic name/class</p>
          </CardHeader>
          <CardContent>
            {analytics.drug_types.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.drug_types}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px]">
                <p className="text-sm text-muted-foreground">No drug type data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Last Updated Info */}
      {analytics.last_updated && (
        <div className="text-sm text-muted-foreground text-center">
          Last updated: {new Date(analytics.last_updated).toLocaleString()}
        </div>
      )}
    </div>
  );
}
