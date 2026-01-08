import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { comparisonService } from '@/services/comparisonService';
import { chatService } from '@/services/chatService';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { formatAIText } from '@/utils/formatText';
import { 
  ArrowLeft, 
  Printer,
  MessageSquare,
  X,
  Send,
  ChevronDown,
  ChevronRight,
  FileText,
  Lightbulb,
  BarChart3,
  ExternalLink
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

interface SemanticSegment {
  text: string;
  start_char: number;
  end_char: number;
  highlight_color: 'green' | 'yellow' | 'red' | 'blue' | 'white';
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

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    section_name: string;
    drug_name: string;
  }>;
}

interface ExplanationModal {
  show: boolean;
  sourceText: string;
  competitorText: string;
  sectionLoinc: string;
  explanation?: {
    explanation: string;
    clinical_significance: string;
    marketing_implication: string;
    action_items: string[];
  };
}

interface ExecutiveSummary {
  executive_summary: string;
  category_summaries: Array<{
    category: string;
    advantages: string[];
    gaps: string[];
    conflicts: string[];
  }>;
  overall_statistics: SemanticDiffSummary;
}

export function ComparisonWorkspace() {
  const { sourceId, competitorId } = useParams<{ sourceId: string; competitorId: string }>();
  const navigate = useNavigate();
  
  const [sourceDrug, setSourceDrug] = useState<DrugWithSections | null>(null);
  const [competitorDrug, setCompetitorDrug] = useState<DrugWithSections | null>(null);
  const [allCompetitors, setAllCompetitors] = useState<DrugWithSections[]>([]);
  const [selectedCompetitorIndex, setSelectedCompetitorIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  
  const [semanticDiff, setSemanticDiff] = useState<SemanticDiffResult[]>([]);
  const [semanticSummary, setSemanticSummary] = useState<SemanticDiffSummary | null>(null);
  const [isLoadingDiff, setIsLoadingDiff] = useState(false);
  
  // UI state
  const [showDifferencesPanel, setShowDifferencesPanel] = useState(false);
  const [isNavCollapsed, setIsNavCollapsed] = useState(false);
  
  // Chat state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  
  // Explanation modal state
  const [explanationModal, setExplanationModal] = useState<ExplanationModal>({
    show: false,
    sourceText: '',
    competitorText: '',
    sectionLoinc: ''
  });
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
  
  // Summary modal state
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [executiveSummary, setExecutiveSummary] = useState<ExecutiveSummary | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const sourceScrollRef = useRef<HTMLDivElement>(null);
  const competitorScrollRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sourceId && competitorId) {
      loadComparisonData(parseInt(sourceId), parseInt(competitorId));
    }
  }, [sourceId, competitorId]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (isChatOpen && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isChatOpen]);

  const loadComparisonData = async (source: number, competitor: number) => {
    try {
      setIsLoading(true);
      const data = await comparisonService.loadComparison(source, [competitor]);
      
      setSourceDrug(data.source_drug);
      setAllCompetitors(data.competitors);
      setCompetitorDrug(data.competitors[0]);
      setSelectedCompetitorIndex(0);
      
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

  const loadSemanticDiff = async () => {
    if (!sourceId || !competitorId) return;
    
    try {
      setIsLoadingDiff(true);
      const result = await comparisonService.getSemanticDiff(
        parseInt(sourceId),
        parseInt(competitorId)
      );
      setSemanticDiff(result.diffs);
      setSemanticSummary(result.summary);
      setShowDifferencesPanel(true);
    } catch (err) {
      console.error('Error loading semantic diff:', err);
    } finally {
      setIsLoadingDiff(false);
    }
  };

  const loadExecutiveSummary = async () => {
    if (!sourceId || !competitorId) return;
    
    try {
      setIsLoadingSummary(true);
      const summary = await comparisonService.getSemanticSummary(
        parseInt(sourceId),
        parseInt(competitorId)
      );
      setExecutiveSummary(summary);
      setShowSummaryModal(true);
    } catch (err) {
      console.error('Error loading executive summary:', err);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const scrollToSection = (sectionTitle: string) => {
    setActiveSection(sectionTitle);
    
    // Scroll both papers to the same section
    const sourceRef = sectionRefs.current[`source-${sectionTitle}`];
    const competitorRef = sectionRefs.current[`competitor-${sectionTitle}`];
    
    if (sourceRef && sourceScrollRef.current) {
      sourceScrollRef.current.scrollTo({
        top: sourceRef.offsetTop - 20,
        behavior: 'smooth'
      });
    }
    
    if (competitorRef && competitorScrollRef.current) {
      competitorScrollRef.current.scrollTo({
        top: competitorRef.offsetTop - 20,
        behavior: 'smooth'
      });
    }
  };

  const handleCompetitorChange = async (index: number) => {
    setSelectedCompetitorIndex(index);
    setCompetitorDrug(allCompetitors[index]);
    
    // Clear diffs for new competitor
    setSemanticDiff([]);
    setSemanticSummary(null);
    setShowDifferencesPanel(false);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !sourceDrug || !competitorDrug) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: chatInput
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsSendingMessage(true);

    try {
      const response = await chatService.ask({
        message: `Comparing ${sourceDrug.name} vs ${competitorDrug.name}: ${chatInput}`,
        drug_id: sourceDrug.id
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer || response.response,
        citations: response.citations
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.'
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleExplainSegment = async (sourceText: string, competitorText: string, sectionLoinc: string) => {
    setExplanationModal({
      show: true,
      sourceText,
      competitorText,
      sectionLoinc,
      explanation: undefined
    });
    
    setIsLoadingExplanation(true);
    
    try {
      const explanation = await comparisonService.explainSegment(
        parseInt(sourceId!),
        parseInt(competitorId!),
        sectionLoinc,
        sourceText,
        competitorText
      );
      
      setExplanationModal(prev => ({
        ...prev,
        explanation
      }));
    } catch (err) {
      console.error('Error loading explanation:', err);
    } finally {
      setIsLoadingExplanation(false);
    }
  };

  const getDiffTypeColor = (diffType: string): string => {
    switch (diffType) {
      case 'high_similarity':
        return 'bg-green-100 text-green-800';
      case 'unique_to_source':
        return 'bg-green-100 text-green-800';
      case 'partial_match':
        return 'bg-yellow-100 text-yellow-800';
      case 'conflict':
        return 'bg-red-100 text-red-800';
      case 'omission':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getDiffTypeLabel = (diffType: string): string => {
    switch (diffType) {
      case 'high_similarity':
        return 'High Similarity';
      case 'unique_to_source':
        return 'Unique Advantage';
      case 'partial_match':
        return 'Partial Match';
      case 'conflict':
        return 'Conflict';
      case 'omission':
        return 'Omission/Gap';
      default:
        return 'Match';
    }
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

  // Get common sections
  const sourceLoincs = new Set(sourceDrug.sections.map(s => s.loinc_code));
  const competitorLoincs = new Set(competitorDrug.sections.map(s => s.loinc_code));
  const commonLoincs = sourceDrug.sections
    .map(s => s.loinc_code)
    .filter(l => competitorLoincs.has(l));

  const commonSections = sourceDrug.sections.filter(s => commonLoincs.includes(s.loinc_code));

  return (
    <div className="comparison-workspace h-screen flex flex-col bg-[#525659]">
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
          
          {/* Competitor Selector */}
          {allCompetitors.length > 1 && (
            <div className="relative">
              <select
                value={selectedCompetitorIndex}
                onChange={(e) => handleCompetitorChange(parseInt(e.target.value))}
                className="px-3 py-1.5 pr-8 text-sm border border-border rounded-lg bg-background appearance-none cursor-pointer hover:bg-accent"
              >
                {allCompetitors.map((comp, idx) => (
                  <option key={comp.id} value={idx}>
                    Competitor {idx + 1}: {comp.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 pointer-events-none" />
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* View Differences Button */}
          <Button
            variant="default"
            size="sm"
            onClick={loadSemanticDiff}
            disabled={isLoadingDiff}
          >
            <FileText className="h-4 w-4 mr-2" />
            {isLoadingDiff ? 'Loading...' : 'View Semantic Differences'}
          </Button>
          
          {/* Generate Summary Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={loadExecutiveSummary}
            disabled={isLoadingSummary}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            {isLoadingSummary ? 'Generating...' : 'Generate Summary'}
          </Button>
          
          {/* Chat Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsChatOpen(!isChatOpen)}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Ask AI
          </Button>
          
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

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Collapsible Navigation Sidebar */}
        <aside className={`no-print bg-white border-r border-border transition-all duration-300 ${isNavCollapsed ? 'w-12' : 'w-64'} flex flex-col`}>
          {/* Collapse Toggle */}
          <div className="p-2 border-b border-border flex justify-end">
            <button
              onClick={() => setIsNavCollapsed(!isNavCollapsed)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              {isNavCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronDown className="h-5 w-5 rotate-90" />}
            </button>
          </div>
          
          {!isNavCollapsed && (
            <nav className="flex-1 overflow-y-auto p-4">
              <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Common Sections</h3>
              <ul className="space-y-1">
                {commonSections.map((section) => (
                  <li key={section.loinc_code}>
                    <button
                      onClick={() => scrollToSection(section.title)}
                      className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${
                        activeSection === section.title
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-accent'
                      }`}
                    >
                      {section.title}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          )}
        </aside>

        {/* Papers Container */}
        <div className="flex-1 flex gap-6 p-8 overflow-hidden">
          {/* Source Drug Paper */}
          <div ref={sourceScrollRef} className="flex-1 overflow-y-auto">
            <div className="paper-sheet" style={{ transform: 'scale(0.85)', transformOrigin: 'top center' }}>
              {/* Drug Header */}
              <div className="drug-header source-header">
                <h1 className="drug-name" style={{ fontSize: '16pt' }}>{sourceDrug.name}</h1>
                <div className="drug-meta" style={{ fontSize: '7pt' }}>
                  <p><strong>Generic Name:</strong> {sourceDrug.generic_name}</p>
                  <p><strong>Manufacturer:</strong> {sourceDrug.manufacturer}</p>
                  <p><strong>Version:</strong> {sourceDrug.version}</p>
                </div>
              </div>

              {/* Sections */}
              <div className="drug-label-content">
                {sourceDrug.sections.map((section) => (
                  <div
                    key={section.loinc_code}
                    ref={(el) => {
                      sectionRefs.current[`source-${section.title}`] = el;
                    }}
                    className="section"
                  >
                    <h2 className="section-title" style={{ fontSize: '10pt' }}>{section.title}</h2>
                    <div 
                      className="section-content"
                      style={{ fontSize: '9pt' }}
                      dangerouslySetInnerHTML={{ __html: section.content_html || section.content }}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Competitor Drug Paper */}
          <div ref={competitorScrollRef} className="flex-1 overflow-y-auto">
            <div className="paper-sheet" style={{ transform: 'scale(0.85)', transformOrigin: 'top center' }}>
              {/* Drug Header */}
              <div className="drug-header competitor-header">
                <h1 className="drug-name" style={{ fontSize: '16pt' }}>{competitorDrug.name}</h1>
                <div className="drug-meta" style={{ fontSize: '7pt' }}>
                  <p><strong>Generic Name:</strong> {competitorDrug.generic_name}</p>
                  <p><strong>Manufacturer:</strong> {competitorDrug.manufacturer}</p>
                  <p><strong>Version:</strong> {competitorDrug.version}</p>
                </div>
              </div>

              {/* Sections */}
              <div className="drug-label-content">
                {competitorDrug.sections.map((section) => (
                  <div
                    key={section.loinc_code}
                    ref={(el) => {
                      sectionRefs.current[`competitor-${section.title}`] = el;
                    }}
                    className="section"
                  >
                    <h2 className="section-title" style={{ fontSize: '10pt' }}>{section.title}</h2>
                    <div 
                      className="section-content"
                      style={{ fontSize: '9pt' }}
                      dangerouslySetInnerHTML={{ __html: section.content_html || section.content }}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading Overlay for Semantic Diff */}
      {isLoadingDiff && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md">
            <Loading size="lg" text="Analyzing semantic differences..." />
            <p className="text-sm text-muted-foreground text-center mt-4">
              This may take a few moments as we perform deep AI-powered comparison
            </p>
          </div>
        </div>
      )}

      {/* Differences Panel Modal */}
      {showDifferencesPanel && semanticDiff.length > 0 && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-border">
              <h2 className="text-2xl font-bold">Differences</h2>
              <button
                onClick={() => setShowDifferencesPanel(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {semanticDiff.map((diffSection) => (
                <div key={diffSection.section_loinc} className="mb-8">
                  <div className="flex items-center justify-between mb-4 pb-2 border-b">
                    <h3 className="text-lg font-semibold text-primary">
                      {diffSection.section_title}
                    </h3>
                    <button
                      onClick={() => scrollToSection(diffSection.section_title)}
                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 px-2 py-1 hover:bg-blue-50 rounded"
                      title="Jump to section in document"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View in Document
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    {diffSection.matches.map((match, idx) => {
                      const sourceSegment = match.source_segment;
                      const competitorSegment = match.competitor_segment;
                      const diffType = sourceSegment?.diff_type || competitorSegment?.diff_type || 'neutral';
                      
                      return (
                        <div 
                          key={idx}
                          className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => {
                            const sourceText = sourceSegment?.text || '';
                            const competitorText = competitorSegment?.text || '';
                            handleExplainSegment(sourceText, competitorText, diffSection.section_loinc);
                          }}
                        >
                          <div className="grid grid-cols-2 divide-x divide-gray-200">
                            {/* Source Column */}
                            <div className="p-4">
                              <div className="text-sm font-semibold text-gray-600 mb-2">
                                {sourceDrug.name}
                              </div>
                              {sourceSegment ? (
                                <div className={`p-3 rounded ${getDiffTypeColor(diffType)}`}>
                                  <div className="text-sm mb-2">
                                    <span className="font-semibold">{getDiffTypeLabel(diffType)}</span>
                                  </div>
                                  <div className="text-sm">{sourceSegment.text}</div>
                                </div>
                              ) : (
                                <div className="text-sm text-gray-400 italic p-3">
                                  No matching text
                                </div>
                              )}
                            </div>
                            
                            {/* Competitor Column */}
                            <div className="p-4">
                              <div className="text-sm font-semibold text-gray-600 mb-2">
                                {competitorDrug.name}
                              </div>
                              {competitorSegment ? (
                                <div className={`p-3 rounded ${getDiffTypeColor(diffType)}`}>
                                  <div className="text-sm mb-2">
                                    <span className="font-semibold">{getDiffTypeLabel(diffType)}</span>
                                  </div>
                                  <div className="text-sm">{competitorSegment.text}</div>
                                </div>
                              ) : (
                                <div className="text-sm text-gray-400 italic p-3">
                                  No matching text
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Explanation Preview */}
                          {match.explanation && (
                            <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
                              <div className="flex items-center gap-2 text-xs text-gray-600">
                                <Lightbulb className="h-3 w-3" />
                                <span>{match.explanation}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Footer with Stats */}
            {semanticSummary && (
              <div className="p-6 border-t border-border bg-gray-50">
                <div className="flex justify-around text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">{semanticSummary.unique_to_source}</div>
                    <div className="text-xs text-gray-600">Unique Advantages</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{semanticSummary.omissions}</div>
                    <div className="text-xs text-gray-600">Gaps to Address</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">{semanticSummary.conflicts}</div>
                    <div className="text-xs text-gray-600">Conflicts</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">{semanticSummary.partial_matches}</div>
                    <div className="text-xs text-gray-600">Partial Matches</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-600">{semanticSummary.high_similarity}</div>
                    <div className="text-xs text-gray-600">High Similarity</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Explanation Modal */}
      {explanationModal.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-yellow-500" />
                AI Explanation
              </h2>
              <button
                onClick={() => setExplanationModal({ show: false, sourceText: '', competitorText: '', sectionLoinc: '' })}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {isLoadingExplanation ? (
                <div className="flex items-center justify-center py-12">
                  <Loading size="lg" text="Generating AI explanation..." />
                </div>
              ) : explanationModal.explanation ? (
                <div className="space-y-6">
                  {/* Compared Texts */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-semibold text-sm text-gray-600 mb-2">{sourceDrug?.name}</h3>
                      <div className="p-4 bg-blue-50 rounded-lg text-sm">
                        {explanationModal.sourceText}
                      </div>
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-gray-600 mb-2">{competitorDrug?.name}</h3>
                      <div className="p-4 bg-purple-50 rounded-lg text-sm">
                        {explanationModal.competitorText}
                      </div>
                    </div>
                  </div>

                  {/* AI Analysis */}
                  <div className="space-y-6">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-bold mb-3 text-gray-900 text-base">Explanation</h3>
                      <div className="text-gray-700 leading-relaxed">
                        {formatAIText(explanationModal.explanation.explanation)}
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-bold mb-3 text-gray-900 text-base">Clinical Significance</h3>
                      <div className="text-gray-700 leading-relaxed">
                        {formatAIText(explanationModal.explanation.clinical_significance)}
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-bold mb-3 text-gray-900 text-base">Marketing Implication</h3>
                      <div className="text-gray-700 leading-relaxed">
                        {formatAIText(explanationModal.explanation.marketing_implication)}
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-bold mb-3 text-gray-900 text-base">Action Items</h3>
                      <ul className="space-y-2">
                        {explanationModal.explanation.action_items.map((item, idx) => (
                          <li key={idx} className="text-gray-700 flex items-start gap-2">
                            <span className="text-primary mt-1">•</span>
                            <div className="flex-1">{formatAIText(item)}</div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-12">
                  Failed to load explanation
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Executive Summary Modal */}
      {showSummaryModal && executiveSummary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <BarChart3 className="h-6 w-6 text-primary" />
                Executive Summary
              </h2>
              <button
                onClick={() => setShowSummaryModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {isLoadingSummary ? (
                <div className="flex items-center justify-center py-12">
                  <Loading size="lg" text="Generating executive summary..." />
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Overall Summary */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Overall Analysis</h3>
                    <div className="text-gray-700 leading-relaxed">
                      {formatAIText(executiveSummary.executive_summary)}
                    </div>
                  </div>

                  {/* Category Breakdown */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Category Analysis</h3>
                    <div className="space-y-4">
                      {executiveSummary.category_summaries.map((category, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-lg p-4">
                          <h4 className="font-semibold text-primary mb-3">{category.category}</h4>
                          
                          {category.advantages.length > 0 && (
                            <div className="mb-4">
                              <div className="text-sm font-bold text-green-700 mb-2 bg-green-50 px-3 py-1.5 rounded">Advantages</div>
                              <div className="space-y-2 pl-2">
                                {category.advantages.map((adv, i) => (
                                  <div key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                    <span className="text-green-600 font-bold mt-0.5">•</span>
                                    <span className="flex-1">{formatAIText(adv)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {category.gaps.length > 0 && (
                            <div className="mb-4">
                              <div className="text-sm font-bold text-blue-700 mb-2 bg-blue-50 px-3 py-1.5 rounded">Gaps</div>
                              <div className="space-y-2 pl-2">
                                {category.gaps.map((gap, i) => (
                                  <div key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                    <span className="text-blue-600 font-bold mt-0.5">•</span>
                                    <span className="flex-1">{formatAIText(gap)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {category.conflicts.length > 0 && (
                            <div className="mb-4">
                              <div className="text-sm font-bold text-red-700 mb-2 bg-red-50 px-3 py-1.5 rounded">Conflicts</div>
                              <div className="space-y-2 pl-2">
                                {category.conflicts.map((conflict, i) => (
                                  <div key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                    <span className="text-red-600 font-bold mt-0.5">•</span>
                                    <span className="flex-1">{formatAIText(conflict)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Statistics */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-lg font-semibold mb-4">Overall Statistics</h3>
                    <div className="grid grid-cols-5 gap-4 text-center">
                      <div>
                        <div className="text-3xl font-bold text-green-600">{executiveSummary.overall_statistics.unique_to_source}</div>
                        <div className="text-xs text-gray-600 mt-1">Unique Advantages</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-blue-600">{executiveSummary.overall_statistics.omissions}</div>
                        <div className="text-xs text-gray-600 mt-1">Gaps</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-red-600">{executiveSummary.overall_statistics.conflicts}</div>
                        <div className="text-xs text-gray-600 mt-1">Conflicts</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-yellow-600">{executiveSummary.overall_statistics.partial_matches}</div>
                        <div className="text-xs text-gray-600 mt-1">Partial Matches</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-gray-600">{executiveSummary.overall_statistics.high_similarity}</div>
                        <div className="text-xs text-gray-600 mt-1">High Similarity</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Chat Modal */}
      {isChatOpen && (
        <div className="fixed bottom-6 right-6 w-[450px] h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 border border-border">
          <div className="flex items-center justify-between p-4 border-b border-border bg-primary text-primary-foreground rounded-t-lg">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              <h3 className="font-semibold">AI Assistant</h3>
            </div>
            <button
              onClick={() => setIsChatOpen(false)}
              className="p-1 hover:bg-primary-foreground/20 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">Ask questions about the comparison</p>
              </div>
            ) : (
              chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-border/30">
                        <p className="text-xs opacity-75">Sources:</p>
                        {msg.citations.map((cite, i) => (
                          <p key={i} className="text-xs opacity-75">
                            • {cite.section_name} ({cite.drug_name})
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-4 border-t border-border">
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                placeholder="Ask about the comparison..."
                className="flex-1 px-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={isSendingMessage}
              />
              <Button
                size="sm"
                onClick={handleSendMessage}
                disabled={isSendingMessage || !chatInput.trim()}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
