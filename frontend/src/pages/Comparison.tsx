import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { drugService } from '@/services/drugService';
import { useDrugStore } from '@/store/drugStore';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Loading } from '../components/ui/Loading';
import { GitCompare, X } from 'lucide-react';

export function Comparison() {
  const navigate = useNavigate();
  const { drugs, setDrugs, selectedDrugs, toggleDrugSelection, clearSelectedDrugs } = useDrugStore();
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

  const handleCompare = () => {
    if (selectedDrugs.length !== 2) {
      alert('Please select exactly 2 drugs to compare');
      return;
    }

    // First drug = Source, Second drug = Competitor
    const sourceDrugId = selectedDrugs[0];
    const competitorDrugId = selectedDrugs[1];
    
    // Navigate to ComparisonWorkspace
    navigate(`/comparison/${sourceDrugId}/${competitorDrugId}`);
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
          <p className="text-sm text-muted-foreground mt-2">
            Select exactly 2 drugs. The first drug will be the <strong>source</strong>, and the second will be the <strong>competitor</strong>.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant={selectedDrugs.length >= 1 ? 'default' : 'secondary'}>
                {selectedDrugs.length >= 1 ? '✓' : '1'}
              </Badge>
              <span className="text-sm font-medium">
                {selectedDrugs.length >= 1
                  ? `${drugs.find((d) => d.id === selectedDrugs[0])?.name} (Source)`
                  : 'Select first drug (Source)'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={selectedDrugs.length >= 2 ? 'default' : 'secondary'}>
                {selectedDrugs.length >= 2 ? '✓' : '2'}
              </Badge>
              <span className="text-sm font-medium">
                {selectedDrugs.length >= 2
                  ? `${drugs.find((d) => d.id === selectedDrugs[1])?.name} (Competitor)`
                  : 'Select second drug (Competitor)'}
              </span>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleCompare}
                disabled={selectedDrugs.length !== 2}
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
        {drugs.map((drug) => {
          const selectionIndex = selectedDrugs.indexOf(drug.id);
          const isSelected = selectionIndex !== -1;
          const selectionLabel = selectionIndex === 0 ? 'Source' : selectionIndex === 1 ? 'Competitor' : '';
          
          return (
            <Card
              key={drug.id}
              className={`cursor-pointer transition-all hover:shadow-md ${
                isSelected ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => {
                if (selectedDrugs.length < 2 || isSelected) {
                  toggleDrugSelection(drug.id);
                }
              }}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{drug.name}</CardTitle>
                  {isSelected && (
                    <Badge variant="default" className="ml-2">
                      {selectionLabel}
                    </Badge>
                  )}
                </div>
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
          );
        })}
      </div>
    </div>
  );
}
