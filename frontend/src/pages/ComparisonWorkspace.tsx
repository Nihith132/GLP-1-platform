import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { comparisonService } from '@/services/comparisonService';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { 
  ArrowLeft, 
  Printer,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import './ComparisonWorkspace.css';

interface DrugSection {
  id: number;
  loinc_code: string;
  title: string;
  content: string;
  content_html?: string;
  section_number?: string;
  level?: number;
  parent_section_id?: number;
  order: number;
  ner_entities: any[];
}

interface DrugWithSections {
  id: number;
  name: string;
  generic_name: string;
  manufacturer: string;
  set_id: string;
  version: number;
  sections: DrugSection[];
}

interface TextChange {
  change_type: 'addition' | 'deletion';
  text: string;
  start_char: number;
  end_char: number;
}

interface LexicalDiffResult {
  section_loinc: string;
  section_title: string;
  source_text: string;
  competitor_text: string;
  additions: TextChange[];
  deletions: TextChange[];
}

interface SemanticSegment {
  text: string;
  start_char: number;
  end_char: number;
  highlight_color: 'green' | 'yellow' | 'red' | 'blue';
  underline_style?: 'wavy';
  diff_type: 'high_similarity' | 'partial_match' | 'unique_to_source' | 'omission' | 'conflict';
}

interface SemanticMatch {
  source_segment: SemanticSegment | null;
  competitor_segment: SemanticSegment | null;
  similarity_score: number | null;
  explanation: string;
}

interface SemanticDiffResult {
  section_loinc: string;
  section_title: string;
  matches: SemanticMatch[];
}

interface SemanticDiffSummary {
  total_matches: number;
  high_similarity: number;
  partial_matches: number;
  unique_to_source: number;
  omissions: number;
  conflicts: number;
}

export function ComparisonWorkspace() {
  const { sourceId, competitorId } = useParams<{ sourceId: string; competitorId: string }>();
  const navigate = useNavigate();
  
  const [sourceDrug, setSourceDrug] = useState<DrugWithSections | null>(null);
  const [competitorDrug, setCompetitorDrug] = useState<DrugWithSections | null>(null);
  const [mode, setMode] = useState<'lexical' | 'semantic'>('lexical');
  const [isLoading, setIsLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  
  const [lexicalDiff, setLexicalDiff] = useState<LexicalDiffResult[]>([]);
  const [semanticDiff, setSemanticDiff] = useState<SemanticDiffResult[]>([]);
  const [semanticSummary, setSemanticSummary] = useState<SemanticDiffSummary | null>(null);
  
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sourceId && competitorId) {
      loadComparisonData(parseInt(sourceId), parseInt(competitorId));
    }
  }, [sourceId, competitorId]);

  useEffect(() => {
    // Load diff data when mode changes
    if (sourceDrug && competitorDrug) {
      if (mode === 'lexical' && lexicalDiff.length === 0) {
        loadLexicalDiff();
      } else if (mode === 'semantic' && semanticDiff.length === 0) {
        loadSemanticDiff();
      }
    }
  }, [mode, sourceDrug, competitorDrug]);

  const loadComparisonData = async (source: number, competitor: number) => {
    try {
      setIsLoading(true);
      const data = await comparisonService.loadComparison(source, [competitor]);
      
      setSourceDrug(data.source_drug);
      setCompetitorDrug(data.competitors[0]);
      
      // Set first common section as active
      const sourceLoincs = data.source_drug.sections.map(s => s.loinc_code);
      const competitorLoincs = data.competitors[0].sections.map(s => s.loinc_code);
      const commonLoincs = sourceLoincs.filter(l => competitorLoincs.includes(l));
      
      if (commonLoincs.length > 0) {
        const firstSection = data.source_drug.sections.find(s => s.loinc_code === commonLoincs[0]);
        if (firstSection) {
          setActiveSection(firstSection.title);
        }
      }
    } catch (err) {
      console.error('Error loading comparison data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadLexicalDiff = async () => {
    if (!sourceId || !competitorId) return;
    
    try {
      const result = await comparisonService.getLexicalDiff(
        parseInt(sourceId),
        parseInt(competitorId)
      );
      setLexicalDiff(result.diffs);
    } catch (err) {
      console.error('Error loading lexical diff:', err);
    }
  };

  const loadSemanticDiff = async () => {
    if (!sourceId || !competitorId) return;
    
    try {
      const result = await comparisonService.getSemanticDiff(
        parseInt(sourceId),
        parseInt(competitorId)
      );
      setSemanticDiff(result.diffs);
      setSemanticSummary(result.summary);
    } catch (err) {
      console.error('Error loading semantic diff:', err);
    }
  };

  const scrollToSection = (sectionTitle: string) => {
    setActiveSection(sectionTitle);
    const ref = sectionRefs.current[sectionTitle];
    if (ref) {
      ref.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const toggleMode = () => {
    setMode(prev => prev === 'lexical' ? 'semantic' : 'lexical');
  };

  const renderTextWithLexicalHighlights = (
    text: string,
    changes: TextChange[],
    type: 'source' | 'competitor'
  ) => {
    if (changes.length === 0) {
      return <div className="whitespace-pre-wrap">{text}</div>;
    }

    // Sort changes by position
    const sortedChanges = [...changes].sort((a, b) => a.start_char - b.start_char);
    
    const segments: JSX.Element[] = [];
    let lastIndex = 0;

    sortedChanges.forEach((change, idx) => {
      // Add text before this change
      if (change.start_char > lastIndex) {
        segments.push(
          <span key={`text-${idx}`}>
            {text.substring(lastIndex, change.start_char)}
          </span>
        );
      }

      // Add highlighted change
      const className = change.change_type === 'deletion' 
        ? 'lexical-deletion' 
        : 'lexical-addition';
      
      segments.push(
        <span key={`change-${idx}`} className={className}>
          {change.text}
        </span>
      );

      lastIndex = change.end_char;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      segments.push(
        <span key="text-end">
          {text.substring(lastIndex)}
        </span>
      );
    }

    return <div className="whitespace-pre-wrap">{segments}</div>;
  };

  const renderSemanticSegments = (
    matches: SemanticMatch[],
    drugType: 'source' | 'competitor'
  ) => {
    const segments = matches
      .map(match => drugType === 'source' ? match.source_segment : match.competitor_segment)
      .filter((seg): seg is SemanticSegment => seg !== null);

    if (segments.length === 0) {
      return null;
    }

    return (
      <div className="space-y-2">
        {segments.map((segment, idx) => {
          const className = `semantic-segment semantic-${segment.highlight_color} ${
            segment.underline_style ? 'semantic-underline-wavy' : ''
          }`;
          
          const match = matches.find(m => 
            (drugType === 'source' && m.source_segment === segment) ||
            (drugType === 'competitor' && m.competitor_segment === segment)
          );

          return (
            <div
              key={idx}
              className={className}
              title={match?.explanation}
            >
              {segment.text}
            </div>
          );
        })}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <Loading size="lg" text="Loading comparison..." />
      </div>
    );
  }

  if (!sourceDrug || !competitorDrug) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center space-y-4">
          <p className="text-lg text-muted-foreground">Failed to load comparison data</p>
          <Button onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  // Get common sections (hide if missing from either drug)
  const sourceLoincs = new Set(sourceDrug.sections.map(s => s.loinc_code));
  const competitorLoincs = new Set(competitorDrug.sections.map(s => s.loinc_code));
  const commonLoincs = sourceDrug.sections
    .map(s => s.loinc_code)
    .filter(l => competitorLoincs.has(l));

  const commonSections = sourceDrug.sections.filter(s => commonLoincs.includes(s.loinc_code));

  return (
    <div className="comparison-workspace h-screen flex flex-col">
      {/* Header */}
      <header className="comparison-header no-print bg-white border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div className="text-lg font-semibold">
            <span className="text-primary">{sourceDrug.name}</span>
            <span className="text-muted-foreground mx-2">vs</span>
            <span className="text-secondary">{competitorDrug.name}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Mode Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={toggleMode}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {mode === 'lexical' ? 'Switch to Semantic' : 'Switch to Lexical'}
          </Button>
          
          {/* Analytics Button */}
          {mode === 'semantic' && semanticSummary && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAnalytics(!showAnalytics)}
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </Button>
          )}
          
          {/* Print Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
          >
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Section Navigation */}
        <aside className="sidebar no-print w-72 bg-card border-r border-border overflow-y-auto">
          <div className="p-4">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              SECTIONS ({commonSections.length})
            </h3>
            <nav className="space-y-1">
              {commonSections.map((section) => {
                const isActive = activeSection === section.title;
                
                return (
                  <button
                    key={section.loinc_code}
                    onClick={() => scrollToSection(section.title)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                  >
                    {section.title}
                  </button>
                );
              })}
            </nav>
          </div>
        </aside>

        {/* Center Content - Two Papers Side by Side */}
        <div 
          ref={contentRef}
          className="comparison-content flex-1 overflow-y-auto"
        >
          <div className="comparison-grid">
            {/* Source Drug Paper */}
            <div className="paper-container source-paper">
              <div className="paper-sheet">
                {/* Drug Header */}
                <div className="drug-header source-header">
                  <h1 className="drug-name">{sourceDrug.name}</h1>
                  <div className="drug-meta">
                    <p><strong>Generic Name:</strong> {sourceDrug.generic_name}</p>
                    <p><strong>Manufacturer:</strong> {sourceDrug.manufacturer}</p>
                    <p><strong>Version:</strong> {sourceDrug.version}</p>
                  </div>
                </div>

                {/* Sections */}
                <div className="drug-label-content">
                  {commonSections.map((section) => {
                    const diffData = mode === 'lexical'
                      ? lexicalDiff.find(d => d.section_loinc === section.loinc_code)
                      : semanticDiff.find(d => d.section_loinc === section.loinc_code);

                    return (
                      <div
                        key={section.loinc_code}
                        ref={(el) => {
                          sectionRefs.current[section.title] = el;
                        }}
                        data-section-title={section.title}
                        className="section"
                      >
                        <h2 className="section-title">{section.title}</h2>
                        
                        <div className="section-content">
                          {mode === 'lexical' && diffData && 'deletions' in diffData ? (
                            renderTextWithLexicalHighlights(
                              diffData.source_text,
                              diffData.deletions,
                              'source'
                            )
                          ) : mode === 'semantic' && diffData && 'matches' in diffData ? (
                            renderSemanticSegments(diffData.matches, 'source')
                          ) : (
                            <div className="whitespace-pre-wrap">{section.content}</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Competitor Drug Paper */}
            <div className="paper-container competitor-paper">
              <div className="paper-sheet">
                {/* Drug Header */}
                <div className="drug-header competitor-header">
                  <h1 className="drug-name">{competitorDrug.name}</h1>
                  <div className="drug-meta">
                    <p><strong>Generic Name:</strong> {competitorDrug.generic_name}</p>
                    <p><strong>Manufacturer:</strong> {competitorDrug.manufacturer}</p>
                    <p><strong>Version:</strong> {competitorDrug.version}</p>
                  </div>
                </div>

                {/* Sections */}
                <div className="drug-label-content">
                  {commonSections.map((sourceSection) => {
                    const competitorSection = competitorDrug.sections.find(
                      s => s.loinc_code === sourceSection.loinc_code
                    );
                    
                    if (!competitorSection) return null;

                    const diffData = mode === 'lexical'
                      ? lexicalDiff.find(d => d.section_loinc === sourceSection.loinc_code)
                      : semanticDiff.find(d => d.section_loinc === sourceSection.loinc_code);

                    return (
                      <div
                        key={sourceSection.loinc_code}
                        className="section"
                      >
                        <h2 className="section-title">{competitorSection.title}</h2>
                        
                        <div className="section-content">
                          {mode === 'lexical' && diffData && 'additions' in diffData ? (
                            renderTextWithLexicalHighlights(
                              diffData.competitor_text,
                              diffData.additions,
                              'competitor'
                            )
                          ) : mode === 'semantic' && diffData && 'matches' in diffData ? (
                            renderSemanticSegments(diffData.matches, 'competitor')
                          ) : (
                            <div className="whitespace-pre-wrap">{competitorSection.content}</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Modal */}
      {showAnalytics && semanticSummary && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 no-print"
            onClick={() => setShowAnalytics(false)}
          />
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-lg shadow-2xl w-[600px] max-h-[80vh] overflow-y-auto no-print">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Semantic Diff Analytics</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAnalytics(false)}
                >
                  ×
                </Button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-700">
                      {semanticSummary.unique_to_source}
                    </div>
                    <div className="text-sm text-green-600">Competitive Advantages</div>
                  </div>
                  
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-700">
                      {semanticSummary.omissions}
                    </div>
                    <div className="text-sm text-blue-600">Gaps to Address</div>
                  </div>
                  
                  <div className="p-4 bg-green-100 rounded-lg">
                    <div className="text-2xl font-bold text-green-800">
                      {semanticSummary.high_similarity}
                    </div>
                    <div className="text-sm text-green-700">High Similarity</div>
                  </div>
                  
                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-700">
                      {semanticSummary.partial_matches}
                    </div>
                    <div className="text-sm text-yellow-600">Partial Matches</div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="text-sm text-muted-foreground">
                    <p><strong>Total Comparisons:</strong> {semanticSummary.total_matches}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
