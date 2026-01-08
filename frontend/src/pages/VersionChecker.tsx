import { useState, useEffect } from 'react';
import { drugService } from '@/services/drugService';
import { watchdogService, type WatchdogProgress } from '@/services/watchdogService';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Loading } from '../components/ui/Loading';
import { CheckCircle2, XCircle, AlertCircle, Building2, Calendar, Play, Loader2, RefreshCw } from 'lucide-react';
import type { Drug } from '@/types';

interface DrugProgress extends WatchdogProgress {
  drugName: string;
}

export function VersionChecker() {
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [selectedDrugs, setSelectedDrugs] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState<Map<number, DrugProgress>>(new Map());

  useEffect(() => {
    loadDrugs();
  }, []);

  const loadDrugs = async () => {
    try {
      setIsLoading(true);
      const data = await drugService.getAllDrugs();
      setDrugs(data);
    } catch (err) {
      console.error('Error loading drugs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDrugSelection = (drugId: number) => {
    setSelectedDrugs((prev) =>
      prev.includes(drugId)
        ? prev.filter((id) => id !== drugId)
        : [...prev, drugId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedDrugs.length === drugs.length) {
      setSelectedDrugs([]);
    } else {
      setSelectedDrugs(drugs.map((d) => d.id));
    }
  };

  const runVersionCheckWorkflow = async () => {
    if (selectedDrugs.length === 0) {
      alert('Please select at least one drug label to check');
      return;
    }

    try {
      setIsRunning(true);
      setIsConnecting(true);

      const initialProgress = new Map<number, DrugProgress>();
      selectedDrugs.forEach((drugId) => {
        const drug = drugs.find((d) => d.id === drugId);
        initialProgress.set(drugId, {
          drug_id: drugId,
          drugName: drug?.name || 'Unknown',
          status: 'queued',
          progress: 0,
          message: 'Triggering GitHub Actions workflow...',
          timestamp: new Date().toISOString()
        });
      });
      setPipelineProgress(initialProgress);

      console.log('🚀 Triggering GitHub Actions workflow for drugs:', selectedDrugs);
      const result = await watchdogService.triggerManualCheck(selectedDrugs);
      console.log('✅ GitHub Actions triggered:', result);

      // Update progress to show workflow is running on GitHub
      const triggeredProgress = new Map(initialProgress);
      selectedDrugs.forEach((drugId) => {
        const existing = triggeredProgress.get(drugId);
        if (existing) {
          triggeredProgress.set(drugId, {
            ...existing,
            progress: 50,
            status: 'running',
            message: 'GitHub Actions workflow running... Check GitHub for real-time progress'
          });
        }
      });
      setPipelineProgress(triggeredProgress);

      // Store workflow URL for later reference
      const workflowUrl = result.workflow_url;

      // Show success message with link to GitHub Actions
      if (workflowUrl) {
        const drugNames = selectedDrugs
          .map(id => drugs.find(d => d.id === id)?.name)
          .filter(Boolean)
          .join(', ');
        
        alert(
          `✅ GitHub Actions workflow triggered successfully!\n\n` +
          `Drugs: ${drugNames}\n\n` +
          `The automation is now running on GitHub Actions.\n` +
          `You can monitor progress and see results at:\n${workflowUrl}\n\n` +
          `Results will be reflected in:\n` +
          `• Dashboard (version updates)\n` +
          `• S3 bucket (downloaded labels)\n` +
          `• Database (updated drug_labels table)`
        );
      }

      setIsRunning(false);
      setIsConnecting(false);

    } catch (err: any) {
      console.error('❌ Error running automation:', err);
      
      // Better error message extraction
      let errorMessage = 'Failed to trigger GitHub Actions workflow';
      if (err.message) {
        errorMessage = err.message;
      } else if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' 
          ? err.response.data.detail 
          : JSON.stringify(err.response.data.detail);
      }
      
      alert(`Error: ${errorMessage}`);
      setIsRunning(false);
      setIsConnecting(false);
      
      // Clear any queued progress
      setPipelineProgress(new Map());
    }
  };

  const clearResults = () => {
    setPipelineProgress(new Map());
    setIsRunning(false);
  };

  const getProgressColor = (status: string, hasUpdate?: boolean) => {
    if (status === 'error') return 'bg-red-500';
    if (status === 'completed' && hasUpdate) return 'bg-amber-500';
    if (status === 'completed') return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusIcon = (status: string, hasUpdate?: boolean) => {
    if (status === 'error') return <XCircle className="w-5 h-5 text-red-500" />;
    if (status === 'running') return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    if (status === 'completed' && hasUpdate) return <AlertCircle className="w-5 h-5 text-amber-500" />;
    if (status === 'completed') return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />;
  };

  if (isLoading) {
    return <Loading />;
  }

  const progressArray = Array.from(pipelineProgress.values());
  const completedCount = progressArray.filter(p => p.status === 'completed').length;
  const updatesFound = progressArray.filter(p => p.status === 'completed' && p.data?.has_update).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Version Checker</h1>
        <p className="text-muted-foreground mt-1">
          Trigger GitHub Actions automation workflow for selected drug labels
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Total Labels</div>
          <div className="text-2xl font-bold mt-1">{drugs.length}</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Selected</div>
          <div className="text-2xl font-bold mt-1">{selectedDrugs.length}</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Checked</div>
          <div className="text-2xl font-bold mt-1">{completedCount}</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Updates Found</div>
          <div className="text-2xl font-bold mt-1 text-amber-600">{updatesFound}</div>
        </div>
      </div>

      <div className="flex items-center justify-between bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-3">
          <Button onClick={toggleSelectAll} variant="outline" size="sm">
            {selectedDrugs.length === drugs.length ? 'Deselect All' : 'Select All'}
          </Button>
          <span className="text-sm text-muted-foreground">
            {selectedDrugs.length} of {drugs.length} selected
          </span>
        </div>

        <div className="flex items-center gap-2">
          {progressArray.length > 0 && (
            <Button onClick={clearResults} variant="outline" size="sm" disabled={isRunning}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Clear Results
            </Button>
          )}
          <Button
            onClick={runVersionCheckWorkflow}
            disabled={selectedDrugs.length === 0 || isRunning}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isConnecting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Connecting...
              </>
            ) : isRunning ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Running ({completedCount}/{selectedDrugs.length})
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Workflow ({selectedDrugs.length})
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        {drugs.map((drug) => {
          const isSelected = selectedDrugs.includes(drug.id);
          const progress = pipelineProgress.get(drug.id);

          return (
            <div
              key={drug.id}
              className={`bg-card border rounded-lg p-4 transition-all ${
                isSelected ? 'border-blue-500 ring-1 ring-blue-500' : 'border-border'
              }`}
            >
              <div className="flex items-start gap-4">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleDrugSelection(drug.id)}
                  disabled={isRunning}
                  className="mt-1 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h3 className="font-semibold text-foreground">{drug.name}</h3>
                      <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Building2 className="w-4 h-4" />
                          {drug.manufacturer}
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Version {drug.version}
                        </div>
                        {drug.last_updated && (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            Published: {new Date(drug.last_updated).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric'
                            })}
                          </div>
                        )}
                        <Badge variant="secondary">{drug.generic_name}</Badge>
                      </div>
                    </div>

                    {progress && (
                      <div className="flex-shrink-0">
                        {getStatusIcon(progress.status, progress.data?.has_update)}
                      </div>
                    )}
                  </div>

                  {progress && (
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{progress.message}</span>
                        <span className="font-medium">{progress.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${getProgressColor(
                            progress.status,
                            progress.data?.has_update
                          )}`}
                          style={{ width: `${progress.progress}%` }}
                        />
                      </div>

                      {progress.status === 'completed' && progress.data?.has_update && (
                        <div className="mt-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
                          <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200 font-medium">
                            <AlertCircle className="w-4 h-4" />
                            New Version Available: {progress.data.new_version}
                          </div>
                          {progress.data.changes && (
                            <div className="mt-2 text-sm text-amber-700 dark:text-amber-300">
                              <strong>Changes:</strong>
                              <div className="mt-1 whitespace-pre-wrap">{progress.data.changes}</div>
                            </div>
                          )}
                        </div>
                      )}

                      {progress.status === 'error' && (
                        <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                          <div className="flex items-center gap-2 text-red-800 dark:text-red-200 font-medium">
                            <XCircle className="w-4 h-4" />
                            Error occurred during check
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {drugs.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No drug labels found</p>
        </div>
      )}
    </div>
  );
}
