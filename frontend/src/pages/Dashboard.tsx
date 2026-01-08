import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { drugService } from '@/services/drugService';
import { useDrugStore } from '@/store/drugStore';
import { SearchBar } from '../components/features/SearchBar';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { PageTransition } from '../components/layout/PageTransition';
import { AlertCircle, GitCompare, Calendar, Building2, CheckCircle2, XCircle, FileText, FolderOpen } from 'lucide-react';

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
    <PageTransition>
      <div className="space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400">
              Drug Dashboard
            </h1>
            <p className="text-muted-foreground mt-2 text-lg">
              Browse and monitor GLP-1 drug labels with AI-powered insights
            </p>
          </div>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex gap-3"
          >
            <Button
              onClick={toggleComparisonMode}
              variant={comparisonMode ? 'default' : 'outline'}
              className="hover-lift btn-glow"
            >
              <GitCompare className="h-4 w-4 mr-2" />
              {comparisonMode ? 'Exit Comparison' : 'Compare'}
            </Button>
            {comparisonMode && selectedDrugs.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Button onClick={handleCompare} variant="default" className="hover-lift">
                  Compare Selected ({selectedDrugs.length})
                </Button>
              </motion.div>
            )}
          </motion.div>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
        >
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={() => {}}
            placeholder="Search by drug name, manufacturer, or generic name (e.g., 'obesity', 'semaglutide', 'GLP-1')..."
          />
          {searchQuery.length > 0 && searchQuery.length < 3 && (
            <p className="text-xs text-muted-foreground mt-2 ml-1">
              Type at least 3 characters to search...
            </p>
          )}
          {searchQuery.length >= 3 && filteredDrugs.length === 0 && (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-2 ml-1">
              No drugs found. Try searching for 'Ozempic', 'Wegovy', 'obesity', or 'GLP-1'
            </p>
          )}
          {searchQuery.length >= 3 && filteredDrugs.length > 0 && filteredDrugs.length < drugs.length && (
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 ml-1">
              Showing top {filteredDrugs.length} most relevant results
            </p>
          )}
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <motion.button
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              // User can select a drug from the list below for single drug analysis
            }}
            className="group relative p-6 rounded-2xl bg-gradient-to-br from-blue-50 via-blue-50 to-indigo-50 dark:from-blue-950/50 dark:via-blue-900/30 dark:to-indigo-950/50 border border-blue-200/60 dark:border-blue-800/40 shadow-lg hover:shadow-xl transition-all duration-300 text-left overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400/0 via-blue-400/0 to-indigo-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative">
              <div className="flex items-center gap-3 text-blue-600 dark:text-blue-400 mb-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-xl">
                  <FileText className="h-5 w-5" />
                </div>
                <span className="text-lg font-bold">New Analysis</span>
              </div>
              <div className="text-sm text-blue-700/80 dark:text-blue-300/80">
                Analyze a single drug label with AI-powered insights
              </div>
            </div>
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              if (!comparisonMode) {
                setComparisonMode(true);
              }
            }}
            className="group relative p-6 rounded-2xl bg-gradient-to-br from-purple-50 via-purple-50 to-pink-50 dark:from-purple-950/50 dark:via-purple-900/30 dark:to-pink-950/50 border border-purple-200/60 dark:border-purple-800/40 shadow-lg hover:shadow-xl transition-all duration-300 text-left overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-400/0 via-purple-400/0 to-pink-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative">
              <div className="flex items-center gap-3 text-purple-600 dark:text-purple-400 mb-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-xl">
                  <GitCompare className="h-5 w-5" />
                </div>
                <span className="text-lg font-bold">New Comparison</span>
              </div>
              <div className="text-sm text-purple-700/80 dark:text-purple-300/80">
                Compare multiple drug labels with semantic analysis
              </div>
            </div>
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/reports')}
            className="group relative p-6 rounded-2xl bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 dark:from-emerald-950/50 dark:via-green-900/30 dark:to-teal-950/50 border border-emerald-200/60 dark:border-emerald-800/40 shadow-lg hover:shadow-xl transition-all duration-300 text-left overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-400/0 via-green-400/0 to-teal-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative">
              <div className="flex items-center gap-3 text-emerald-600 dark:text-emerald-400 mb-3">
                <div className="p-2 bg-emerald-100 dark:bg-emerald-900/50 rounded-xl">
                  <FolderOpen className="h-5 w-5" />
                </div>
                <span className="text-lg font-bold">View Reports</span>
              </div>
              <div className="text-sm text-emerald-700/80 dark:text-emerald-300/80">
                Access your saved analysis and comparison reports
              </div>
            </div>
          </motion.button>
        </motion.div>

        {/* Drug List */}
        {filteredDrugs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-center py-16 glass-card rounded-2xl"
          >
            <p className="text-muted-foreground text-lg">No drugs found</p>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.25 }}
            className="space-y-3"
          >
            {filteredDrugs.map((drug, index) => (
              <motion.div
                key={drug.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.4,
                  delay: 0.3 + index * 0.05,
                  ease: [0.16, 1, 0.3, 1],
                }}
                whileHover={!comparisonMode ? { scale: 1.01, y: -2 } : undefined}
                onClick={() => !comparisonMode && navigate(`/analysis/${drug.id}`)}
                className={`group flex items-center gap-4 p-5 rounded-2xl glass-card transition-all duration-300 ${
                  isSelected(drug.id) ? 'ring-2 ring-primary shadow-lg' : ''
                } ${!comparisonMode ? 'cursor-pointer hover:shadow-xl hover:border-primary/50' : ''}`}
              >
                {/* Checkbox */}
                {comparisonMode && (
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isSelected(drug.id)}
                      onChange={() => toggleDrugSelection(drug.id)}
                      className="h-5 w-5 rounded-md border-gray-300 text-primary focus:ring-primary cursor-pointer transition-all duration-200"
                    />
                  </div>
                )}

                {/* Drug Info */}
                <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors duration-200">
                      {drug.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1.5">
                      <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        {drug.manufacturer || 'Unknown Manufacturer'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Version</div>
                      <div className="font-mono font-bold text-sm">{drug.version}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1 mb-1">
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
                      <Badge variant="success" className="flex items-center gap-1.5 px-3 py-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="flex items-center gap-1.5 px-3 py-1">
                        <XCircle className="h-3.5 w-3.5" />
                        Archived
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Role Badge and Action */}
                {comparisonMode && isSelected(drug.id) && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-end gap-2 min-w-[140px]"
                  >
                    {getRole(drug.id) === 'competitor' && (
                      <Button
                        size="sm"
                        onClick={() => setAsSource(drug.id)}
                        className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                      >
                        Set as Source
                      </Button>
                    )}
                    <span
                      className={`text-xs font-bold tracking-wider uppercase ${
                        getRole(drug.id) === 'source'
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-slate-500 dark:text-slate-400'
                      }`}
                    >
                      {getRole(drug.id) === 'source' ? '★ Source' : 'Competitor'}
                    </span>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </PageTransition>
  );
}
