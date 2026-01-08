import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { reportService } from '@/services/reportService';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Loading } from '../components/ui/Loading';
import { ArrowLeft } from 'lucide-react';
import type { Report } from '@/types';

export function ReportDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadReport(parseInt(id));
    }
  }, [id]);

  const loadReport = async (reportId: number) => {
    try {
      setIsLoading(true);
      const data = await reportService.getReportById(reportId);
      setReport(data);
    } catch (err) {
      console.error('Error loading report:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Loading size="lg" text="Loading report..." />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Report not found</p>
        <Button onClick={() => navigate('/reports')} className="mt-4">
          Back to Reports
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/reports')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{report.title}</h1>
          <p className="text-muted-foreground mt-2">
            Created on {new Date(report.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Report Content</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap text-sm">
              {JSON.stringify(report.data, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {report.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{report.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
