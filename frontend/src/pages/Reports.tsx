import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportService } from '@/services/reportService';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Loading } from '../components/ui/Loading';
import { FileText, Calendar, Trash2, FolderOpen } from 'lucide-react';
import type { Report } from '@/types';

export function Reports() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setIsLoading(true);
      const data = await reportService.getAllReports();
      setReports(data);
    } catch (err) {
      console.error('Error loading reports:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadReport = async (reportId: string | number) => {
    try {
      // Fetch full report with all components
      // Don't convert to Number - backend uses UUID strings
      const report = await reportService.getReportById(reportId);
      
      // Store report data in sessionStorage for restoration
      sessionStorage.setItem('pendingReportLoad', JSON.stringify(report));
      
      // ⭐ Route based on report type
      if (report.report_type === 'comparison') {
        // Comparison report: Navigate to comparison workspace
        const workspaceState = (report as any).workspace_state;
        const sourceDrugId = workspaceState?.source_drug_id || workspaceState?.sourceDrugId;
        const competitorIds = workspaceState?.competitor_drug_ids || workspaceState?.competitorDrugIds || [];
        
        console.log('🔍 Loading comparison report:', {
          sourceDrugId,
          competitorIds,
          workspaceState
        });
        
        if (sourceDrugId && competitorIds.length > 0) {
          const competitorsParam = competitorIds.join(',');
          navigate(`/comparison/${sourceDrugId}/${competitorsParam}?loadReport=${reportId}`);
        } else {
          // Better error message
          const errorDetails = [];
          if (!sourceDrugId) errorDetails.push('source drug ID missing');
          if (!competitorIds || competitorIds.length === 0) errorDetails.push('competitor drug IDs missing');
          
          alert(`Unable to load comparison report: ${errorDetails.join(', ')}. This report may be from an older version. Please delete it and create a new comparison report.`);
        }
      } else {
        // Analysis report: Navigate to analysis workspace (existing logic)
        const drugId = (report as any).workspace_state?.drug_id || (report as any).workspace_state?.drugId;
        if (drugId) {
          navigate(`/analysis/${drugId}?loadReport=${reportId}`);
        } else {
          alert('Unable to load report: Drug ID not found');
        }
      }
    } catch (error) {
      console.error('Failed to load report:', error);
      alert('Failed to load report. Please try again.');
    }
  };

  const handleDelete = async (id: number | string) => {
    if (!confirm('Are you sure you want to delete this report?')) return;

    try {
      await reportService.deleteReport(id);
      setReports(reports.filter((r) => r.id !== id));
    } catch (err) {
      console.error('Error deleting report:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Loading size="lg" text="Loading reports..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reports</h1>
          <p className="text-muted-foreground mt-2">
            View and manage generated reports
          </p>
        </div>
      </div>

      {reports.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              No reports yet
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {reports.map((report) => {
            const workspaceState = (report as any).workspace_state;
            
            // ⭐ Display drug names based on report type
            let drugDisplayName: string;
            if (report.report_type === 'comparison') {
              const sourceName = workspaceState?.source_drug_name || workspaceState?.sourceDrugName || 'Unknown';
              const competitorNames = workspaceState?.competitor_drug_names || workspaceState?.competitorDrugNames || [];
              if (competitorNames.length > 0) {
                drugDisplayName = `${sourceName} vs ${competitorNames.join(', ')}`;
              } else {
                drugDisplayName = `${sourceName} (Comparison)`;
              }
            } else {
              drugDisplayName = workspaceState?.drug_name || workspaceState?.drugName || 'Unknown Drug';
            }
            
            return (
              <Card key={report.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{report.title}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">{drugDisplayName}</p>
                      <div className="flex items-center gap-2 mt-2">
                        {/* ⭐ Different badge styling for comparison vs analysis */}
                        <Badge variant={report.report_type === 'comparison' ? 'default' : 'secondary'}>
                          {report.report_type}
                        </Badge>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(report.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      className="flex-1"
                      onClick={() => handleLoadReport(report.id)}
                    >
                      <FolderOpen className="h-4 w-4 mr-2" />
                      Load Report
                    </Button>
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => handleDelete(report.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
