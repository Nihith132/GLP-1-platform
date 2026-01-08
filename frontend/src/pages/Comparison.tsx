import { useState, useEffect } from 'react';
import { drugService } from '@/services/drugService';
import { comparisonService } from '@/services/comparisonService';
import { useDrugStore } from '@/store/drugStore';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Loading } from '../components/ui/Loading';
import { GitCompare, Plus, X } from 'lucide-react';
import type { Drug, ComparisonResult } from '@/types';

export function Comparison() {
  const { drugs, setDrugs, selectedDrugs, toggleDrugSelection, clearSelectedDrugs } = useDrugStore();
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDrugs, setIsLoadingDrugs] = useState(true);

  useEffect(() => {
    loadDrugs();
  }, []);

  const loadDrugs = async () => {
    try {
      const data = await drugService.getAllDrugs();
      setDrugs(data);
    } catch (err) {
      console.error('Error loading drugs:', err);
    } finally {
      setIsLoadingDrugs(false);
    }
  };

  const handleCompare = async () => {
    if (selectedDrugs.length !== 2) return;

    try {
      setIsLoading(true);
      const result = await comparisonService.compareDrugs(
        selectedDrugs[0],
        selectedDrugs[1]
      );
      setComparison(result);
    } catch (err) {
      console.error('Error comparing drugs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoadingDrugs) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Loading size="lg" text="Loading drugs..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Drug Comparison</h1>
        <p className="text-muted-foreground mt-2">
          Compare two drug labels side by side
        </p>
      </div>

      {/* Selection Section */}
      <Card>
        <CardHeader>
          <CardTitle>Select Drugs to Compare</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant={selectedDrugs.length >= 1 ? 'success' : 'secondary'}>
                {selectedDrugs.length >= 1 ? '✓' : '1'}
              </Badge>
              <span className="text-sm font-medium">
                {selectedDrugs.length >= 1
                  ? drugs.find((d) => d.id === selectedDrugs[0])?.name
                  : 'Select first drug'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={selectedDrugs.length >= 2 ? 'success' : 'secondary'}>
                {selectedDrugs.length >= 2 ? '✓' : '2'}
              </Badge>
              <span className="text-sm font-medium">
                {selectedDrugs.length >= 2
                  ? drugs.find((d) => d.id === selectedDrugs[1])?.name
                  : 'Select second drug'}
              </span>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleCompare}
                disabled={selectedDrugs.length !== 2 || isLoading}
              >
                <GitCompare className="h-4 w-4 mr-2" />
                Compare
              </Button>
              <Button
                variant="outline"
                onClick={clearSelectedDrugs}
                disabled={selectedDrugs.length === 0}
              >
                <X className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Drug List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {drugs.map((drug) => (
          <Card
            key={drug.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedDrugs.includes(drug.id) ? 'ring-2 ring-primary' : ''
            }`}
            onClick={() => {
              if (selectedDrugs.length < 2 || selectedDrugs.includes(drug.id)) {
                toggleDrugSelection(drug.id);
              }
            }}
          >
            <CardHeader>
              <CardTitle className="text-lg">{drug.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                <div>Version: {drug.version}</div>
                <div>
                  Last Updated:{' '}
                  {new Date(drug.last_updated).toLocaleDateString()}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Comparison Results */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loading size="lg" text="Comparing drugs..." />
        </div>
      )}

      {comparison && !isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>Comparison Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold">
                  {comparison.drug1_name} vs {comparison.drug2_name}
                </span>
                <Badge variant="secondary">
                  Similarity: {(comparison.similarity_score * 100).toFixed(1)}%
                </Badge>
              </div>

              <div className="space-y-4">
                {comparison.differences.map((diff, idx) => (
                  <Card key={idx} className="bg-muted/50">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{diff.section_name}</CardTitle>
                        <Badge
                          variant={
                            diff.diff_type === 'unchanged'
                              ? 'secondary'
                              : diff.diff_type === 'modified'
                              ? 'warning'
                              : 'default'
                          }
                        >
                          {diff.diff_type}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm font-medium mb-2">
                            {comparison.drug1_name}
                          </div>
                          <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {diff.drug1_content.substring(0, 200)}...
                          </div>
                        </div>
                        <div>
                          <div className="text-sm font-medium mb-2">
                            {comparison.drug2_name}
                          </div>
                          <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {diff.drug2_content.substring(0, 200)}...
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
