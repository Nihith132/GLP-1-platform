import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { drugService } from '@/services/drugService';
import { useDrugStore } from '@/store/drugStore';
import { SearchBar } from '../components/features/SearchBar';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { AlertCircle, GitCompare, Calendar, Building2, CheckCircle2, XCircle } from 'lucide-react';

type DrugSelection = {
  id: number;
  role: 'source' | 'competitor';
};

export function Dashboard() {
  const navigate = useNavigate();
  const { drugs, setDrugs } = useDrugStore();
  const [filteredDrugs, setFilteredDrugs] = useState(drugs);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedDrugs, setSelectedDrugs] = useState<DrugSelection[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadDrugs();
  }, []);

  useEffect(() => {
    setFilteredDrugs(drugs);
  }, [drugs]);

  // Dynamic search with debouncing
  useEffect(() => {
    if (searchQuery.length === 0) {
      setFilteredDrugs(drugs);
      return;
    }

    if (searchQuery.length < 3) {
      return; // Wait for at least 3 characters
    }

    const timer = setTimeout(() => {
      handleSearch(searchQuery);
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery, drugs]);

  const loadDrugs = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await drugService.getAllDrugs();
      setDrugs(data);
    } catch (err) {
      setError('Failed to load drugs. Please try again.');
      console.error('Error loading drugs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (query: string) => {
    const searchLower = query.toLowerCase().trim();
    
    // If empty, show all drugs
    if (!searchLower) {
      setFilteredDrugs(drugs);
      return;
    }
    
    // Calculate relevance score for each drug
    const drugsWithScores = drugs.map((drug) => {
      let score = 0;
      const drugName = drug.name.toLowerCase();
      const manufacturer = drug.manufacturer?.toLowerCase() || '';
      const genericName = (drug as any).generic_name?.toLowerCase() || '';
      
      // Exact match in drug name (highest priority)
      if (drugName === searchLower) {
        score += 100;
      } else if (drugName.includes(searchLower)) {
        score += 50;
      }
      
      // Exact match in generic name
      if (genericName === searchLower) {
        score += 90;
      } else if (genericName.includes(searchLower)) {
        score += 40;
      }
      
      // Match in manufacturer
      if (manufacturer.includes(searchLower)) {
        score += 20;
      }
      
      // Check for keyword matches
      const searchTerms = searchLower.split(' ').filter(term => term.length >= 3);
      
      // Obesity/weight loss related terms
      const obesityKeywords = ['obesity', 'weight', 'loss', 'glp-1', 'glp1', 'glp', 'diabetes', 'semaglutide', 'liraglutide', 'tirzepatide'];
      const hasObesityKeyword = searchTerms.some(term => 
        obesityKeywords.some(keyword => keyword.includes(term) || term.includes(keyword))
      );
      
      if (hasObesityKeyword) {
        // Match GLP-1 and weight-loss drugs
        const glpDrugs = ['semaglutide', 'liraglutide', 'tirzepatide', 'exenatide', 'dulaglutide', 'orlistat', 'phentermine', 'naltrexone', 'setmelanotide', 'benzphetamine', 'diethylpropion'];
        if (glpDrugs.some(glpDrug => genericName.includes(glpDrug))) {
          score += 30;
        }
      }
      
      // Word-by-word matching
      searchTerms.forEach(term => {
        if (drugName.includes(term)) score += 10;
        if (genericName.includes(term)) score += 8;
        if (manufacturer.includes(term)) score += 5;
      });
      
      return { drug, score };
    });
    
    // Filter to only include drugs with score > 0, sorted by score
    const filtered = drugsWithScores
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 5) // Top 5 results only
      .map(item => item.drug);
    
    setFilteredDrugs(filtered);
  };

  const toggleComparisonMode = () => {
    setComparisonMode(!comparisonMode);
    if (!comparisonMode) {
      setSelectedDrugs([]);
    }
  };

  const toggleDrugSelection = (drugId: number) => {
    setSelectedDrugs((prev) => {
      const exists = prev.find((d) => d.id === drugId);
      if (exists) {
        return prev.filter((d) => d.id !== drugId);
      } else {
        return [...prev, { id: drugId, role: 'competitor' }];
      }
    });
  };

  const setAsSource = (drugId: number) => {
    setSelectedDrugs((prev) => {
      // Set this drug as source and all others as competitors
      return prev.map((drug) => ({
        ...drug,
        role: drug.id === drugId ? 'source' : 'competitor',
      }));
    });
  };

  const isSelected = (drugId: number) => {
    return selectedDrugs.some((d) => d.id === drugId);
  };

  const getRole = (drugId: number) => {
    return selectedDrugs.find((d) => d.id === drugId)?.role || 'competitor';
  };

  const handleCompare = () => {
    const source = selectedDrugs.find((d) => d.role === 'source');
    const competitors = selectedDrugs.filter((d) => d.role === 'competitor');
    
    if (!source) {
      alert('Please select one drug as the source');
      return;
    }
    
    if (competitors.length === 0) {
      alert('Please select at least one competitor');
      return;
    }

    // Navigate to comparison workspace with all selected competitors
    const competitorIds = competitors.map(c => c.id).join(',');
    navigate(`/comparison/${source.id}/${competitorIds}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Loading size="lg" text="Loading drugs..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <p className="text-lg text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Drug Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Browse and monitor GLP-1 drug labels
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={toggleComparisonMode}
            variant={comparisonMode ? 'default' : 'outline'}
          >
            <GitCompare className="h-4 w-4 mr-2" />
            {comparisonMode ? 'Exit Comparison' : 'Compare'}
          </Button>
          {comparisonMode && selectedDrugs.length > 0 && (
            <Button onClick={handleCompare} variant="default">
              Compare Selected ({selectedDrugs.length})
            </Button>
          )}
        </div>
      </div>

      {/* Search */}
      <div>
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          onSearch={() => {}}
          placeholder="Search by drug name, manufacturer, or generic name (e.g., 'obesity', 'semaglutide', 'GLP-1')..."
        />
        {searchQuery.length > 0 && searchQuery.length < 3 && (
          <p className="text-xs text-muted-foreground mt-1">
            Type at least 3 characters to search...
          </p>
        )}
        {searchQuery.length >= 3 && filteredDrugs.length === 0 && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
            No drugs found. Try searching for 'Ozempic', 'Wegovy', 'obesity', or 'GLP-1'
          </p>
        )}
        {searchQuery.length >= 3 && filteredDrugs.length > 0 && filteredDrugs.length < drugs.length && (
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            Showing top {filteredDrugs.length} most relevant results
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-card border border-border">
          <div className="text-2xl font-bold">{drugs.length}</div>
          <div className="text-sm text-muted-foreground">Total Drugs</div>
        </div>
        <div className="p-4 rounded-lg bg-card border border-border">
          <div className="text-2xl font-bold">
            {drugs.filter((d) => d.version_check_enabled).length}
          </div>
          <div className="text-sm text-muted-foreground">Monitored</div>
        </div>
        <div className="p-4 rounded-lg bg-card border border-border">
          <div className="text-2xl font-bold">
            {drugs.filter((d) => !d.version_check_enabled).length}
          </div>
          <div className="text-sm text-muted-foreground">Not Monitored</div>
        </div>
      </div>

      {/* Drug List */}
      {filteredDrugs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No drugs found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredDrugs.map((drug) => (
            <div
              key={drug.id}
              onClick={() => !comparisonMode && navigate(`/analysis/${drug.id}`)}
              className={`flex items-center gap-4 p-4 rounded-lg bg-card border border-border transition-all hover:shadow-md ${
                isSelected(drug.id) ? 'ring-2 ring-primary' : ''
              } ${!comparisonMode ? 'cursor-pointer hover:border-primary' : ''}`}
            >
              {/* Checkbox */}
              {comparisonMode && (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isSelected(drug.id)}
                    onChange={() => toggleDrugSelection(drug.id)}
                    className="h-5 w-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                  />
                </div>
              )}

              {/* Drug Info */}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                <div className="md:col-span-2">
                  <h3 className="text-lg font-semibold">{drug.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Building2 className="h-3 w-3 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {drug.manufacturer || 'Unknown Manufacturer'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Version</div>
                    <div className="font-mono font-semibold">{drug.version}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Last Updated
                    </div>
                    <div className="text-sm font-medium">
                      {new Date(drug.last_updated).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2">
                  {drug.is_current_version ? (
                    <Badge variant="success" className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Active
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <XCircle className="h-3 w-3" />
                      Archived
                    </Badge>
                  )}
                </div>
              </div>

              {/* Role Badge and Action */}
              {comparisonMode && isSelected(drug.id) && (
                <div className="flex flex-col items-end gap-2 min-w-[140px]">
                  {getRole(drug.id) === 'competitor' && (
                    <Button
                      size="sm"
                      onClick={() => setAsSource(drug.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium"
                    >
                      Set as Source
                    </Button>
                  )}
                  <span
                    className={`text-sm font-medium tracking-wide ${
                      getRole(drug.id) === 'source'
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {getRole(drug.id) === 'source' ? 'Source' : 'Competitor'}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
