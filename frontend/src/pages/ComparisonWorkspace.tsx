import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { comparisonService } from '@/services/comparisonService';
import { chatService } from '@/services/chatService';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { formatAIText } from '@/utils/formatText';
import { SaveReportModal } from '../components/SaveReportModal';
import { ComparisonNotesModal } from '../components/ComparisonNotesModal';
import { HighlightPopup } from '../components/HighlightPopup';
import { useTextSelection } from '../hooks/useTextSelection';
import { useComparisonWorkspaceStore } from '../store/comparisonWorkspaceStore';
import { 
  ArrowLeft, 
  Printer,
  MessageSquare,
  Loader2,
  X,
  Send,
  ChevronDown,
  ChevronRight,
  FileText,
  Lightbulb,
  BarChart3,
  ExternalLink,
  ArrowLeftRight,
  Save,
  Building2,
  Calendar,
  StickyNote,
  Star,
  Flag
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
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  question?: string;
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
  const location = useLocation();
  
  // Comparison workspace store
  const { 
    saveAsComparisonReport,
    loadComparisonReport,
    clearComparison,
    setComparisonDrugs,
    sourceHighlights,
    addSourceHighlight,
    addCitedNote,
    citedNotes,
    uncitedNotes,
    flaggedChats: storedFlaggedChats,
    flagChat,
    unflagChat,
    starredDiffIds,
    toggleStarDiff
  } = useComparisonWorkspaceStore();
  
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
  const [showOnlyStarred, setShowOnlyStarred] = useState(false);
  
  // Save Report modal state
  const [showSaveModal, setShowSaveModal] = useState(false);
  
  // Notes modal state
  const [showNotesModal, setShowNotesModal] = useState(false);
  
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
  
  // Text selection and highlighting for source drug
  const sourceContentRef = useRef<HTMLDivElement>(null);
  const { selection, clearSelection } = useTextSelection(sourceContentRef);
  const [showHighlightPopup, setShowHighlightPopup] = useState(false);
  const [highlightPopupPosition, setHighlightPopupPosition] = useState({ top: 0, left: 0 });
  
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const sourceScrollRef = useRef<HTMLDivElement>(null);
  const competitorScrollRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Show highlight popup when text is selected
  useEffect(() => {
    if (selection && selection.rect) {
      setHighlightPopupPosition({
        top: selection.rect.top + window.scrollY,
        left: selection.rect.left + (selection.rect.width / 2),
      });
      setShowHighlightPopup(true);
    } else {
      setShowHighlightPopup(false);
    }
  }, [selection]);

  useEffect(() => {
    if (sourceId && competitorId) {
      // ⭐ CRITICAL FIX: Check if this is a NEW comparison or loading a saved report
      const urlParams = new URLSearchParams(location.search);
      const isLoadingReport = urlParams.get('loadReport');
      
      // If NOT loading a report, this is a new comparison -> CLEAR OLD STATE
      if (!isLoadingReport) {
        console.log('🧹 Clearing old comparison state for NEW comparison');
        clearComparison();
      }
      
      const competitorIds = competitorId.split(',').map(id => parseInt(id.trim()));
      loadComparisonData(parseInt(sourceId), competitorIds);
    }
  }, [sourceId, competitorId]);

  // ⭐ Report Load Detection
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const reportId = urlParams.get('loadReport');
    
    if (reportId) {
      const reportData = sessionStorage.getItem('pendingReportLoad');
      if (reportData) {
        try {
          const report = JSON.parse(reportData);
          loadComparisonReportData(report);
          sessionStorage.removeItem('pendingReportLoad');
        } catch (error) {
          console.error('Failed to load comparison report:', error);
        }
      }
    }
  }, [location.search]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (isChatOpen && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isChatOpen]);
  
  // Apply source drug highlights
  useEffect(() => {
    if (!sourceDrug || !sourceContentRef.current) return;

    const applyHighlights = () => {
      if (!sourceContentRef.current) return;

      // Clear all existing highlights first
      const existingMarks = sourceContentRef.current.querySelectorAll('.highlight-mark');
      existingMarks.forEach(mark => {
        const parent = mark.parentNode;
        if (parent) {
          while (mark.firstChild) {
            parent.insertBefore(mark.firstChild, mark);
          }
          parent.removeChild(mark);
        }
      });
      
      // Normalize text nodes after clearing
      sourceContentRef.current.querySelectorAll('.section-content').forEach(el => el.normalize());

      // If no highlights, we're done
      if (sourceHighlights.length === 0) return;

      // Apply each highlight
      sourceHighlights.forEach(highlight => {
        const sectionElement = sourceContentRef.current?.querySelector(
          `[data-section-id="${highlight.sectionId}"] .section-content`
        );
        
        if (!sectionElement) return;

        const textNodes: Node[] = [];
        const walker = document.createTreeWalker(
          sectionElement,
          NodeFilter.SHOW_TEXT,
          null
        );

        let node;
        while ((node = walker.nextNode())) {
          textNodes.push(node);
        }

        let currentOffset = 0;
        for (const textNode of textNodes) {
          const textLength = textNode.textContent?.length || 0;
          const nodeStart = currentOffset;
          const nodeEnd = currentOffset + textLength;

          if (highlight.position.start < nodeEnd && highlight.position.end > nodeStart) {
            const range = document.createRange();
            const startOffset = Math.max(0, highlight.position.start - nodeStart);
            const endOffset = Math.min(textLength, highlight.position.end - nodeStart);

            try {
              range.setStart(textNode, startOffset);
              range.setEnd(textNode, endOffset);

              const mark = document.createElement('mark');
              mark.className = `highlight-mark ${highlight.color === 'red' ? 'bg-red-200' : 'bg-blue-200'}`;
              mark.style.cursor = 'pointer';
              mark.dataset.highlightId = highlight.id;
              
              range.surroundContents(mark);
            } catch (e) {
              console.warn('Failed to apply highlight:', e);
            }
          }

          currentOffset = nodeEnd;
        }
      });
    };

    // Apply highlights after a short delay to ensure content is rendered
    const timeoutId = setTimeout(applyHighlights, 100);
    
    return () => clearTimeout(timeoutId);
  }, [sourceDrug, sourceHighlights]);

  const handleSwapDrugs = () => {
    // Cycle through competitors, keeping source fixed
    if (!allCompetitors || allCompetitors.length <= 1) return;
    
    const nextIndex = (selectedCompetitorIndex + 1) % allCompetitors.length;
    setSelectedCompetitorIndex(nextIndex);
    setCompetitorDrug(allCompetitors[nextIndex]);
    
    // Clear diffs and summary for new competitor
    setSemanticDiff([]);
    setSemanticSummary(null);
    setShowDifferencesPanel(false);
    setExecutiveSummary(null);
  };
  
  // Handle source drug highlighting
  const handleHighlightColor = (color: 'red' | 'blue') => {
    if (!selection) return;

    const highlightId = `highlight-${Date.now()}-${Math.random()}`;
    const highlight = {
      id: highlightId,
      sectionId: selection.sectionId.toString(),
      text: selection.text.substring(0, 100),
      color,
      position: {
        start: selection.startOffset,
        end: selection.endOffset,
      },
      created_at: new Date().toISOString(),
    };

    addSourceHighlight(highlight);
    
    // Automatically create a cited note for this highlight
    const note = {
      id: `note-${Date.now()}-${Math.random()}`,
      content: '', // User will fill this in later
      highlightId: highlightId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    addCitedNote(note, highlightId);
    
    clearSelection();
    setShowHighlightPopup(false);
  };

  const handleCancelHighlight = () => {
    clearSelection();
    setShowHighlightPopup(false);
  };

  const loadComparisonData = async (source: number, competitors: number[]) => {
    try {
      setIsLoading(true);
      const data = await comparisonService.loadComparison(source, competitors);
      
      setSourceDrug(data.source_drug);
      setAllCompetitors(data.competitors);
      setCompetitorDrug(data.competitors[0]);
      setSelectedCompetitorIndex(0);
      
      // ⭐ CRITICAL: Update store with drug IDs and names for saving reports
      const competitorNames = data.competitors.map(c => c.name);
      setComparisonDrugs(
        data.source_drug.id,
        data.source_drug.name,
        competitors,
        competitorNames
      );
      
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

  const loadComparisonReportData = async (report: any) => {
    try {
      // Load report state into store
      loadComparisonReport(report);
      
      // Extract workspace state
      const workspaceState = report.workspace_state;
      
      // Load drugs (this will also trigger normal comparison data loading)
      const sourceDrugId = workspaceState?.source_drug_id || workspaceState?.sourceDrugId;
      const competitorIds = workspaceState?.competitor_drug_ids || workspaceState?.competitorDrugIds || [];
      
      if (sourceDrugId && competitorIds.length > 0) {
        await loadComparisonData(sourceDrugId, competitorIds);
        
        // After drugs are loaded, restore UI state
        if (workspaceState?.show_differences_panel || workspaceState?.showDifferencesPanel) {
          // Re-run semantic diff for current competitor
          if (competitorIds[0]) {
            await loadSemanticDiff();
          }
        }
        
        // Restore scroll positions after a brief delay
        setTimeout(() => {
          const scrollPositions = workspaceState?.scroll_positions || workspaceState?.scrollPositions;
          if (scrollPositions) {
            if (sourceScrollRef.current && scrollPositions.source) {
              sourceScrollRef.current.scrollTop = scrollPositions.source;
            }
            if (competitorScrollRef.current && scrollPositions.competitor) {
              competitorScrollRef.current.scrollTop = scrollPositions.competitor;
            }
          }
        }, 500);
      }
    } catch (error) {
      console.error('Failed to load comparison report data:', error);
      alert('Failed to restore report state. Please try again.');
    }
  };

  const loadSemanticDiff = async () => {
    if (!sourceId || !competitorId) return;
    
    // ⭐ FIX 4: Skip loading if data already exists (cached)
    if (semanticDiff.length > 0) {
      console.log('✓ Semantic diff already loaded, using cached data');
      setShowDifferencesPanel(true);
      return;
    }
    
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
    
    // ⭐ FIX 4: Skip loading if summary already exists (cached)
    if (executiveSummary) {
      console.log('✓ Executive summary already loaded, using cached data');
      setShowSummaryModal(true);
      return;
    }
    
    setIsLoadingSummary(true);
    setShowSummaryModal(false);
    
    try {
      const summary = await comparisonService.getDiffSummary(
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
      // Get the element's position relative to the scrollable container
      const containerRect = sourceScrollRef.current.getBoundingClientRect();
      const elementRect = sourceRef.getBoundingClientRect();
      const scrollTop = sourceScrollRef.current.scrollTop;
      const targetScrollTop = scrollTop + (elementRect.top - containerRect.top) - 10;
      
      sourceScrollRef.current.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      });
    }
    
    if (competitorRef && competitorScrollRef.current) {
      // Get the element's position relative to the scrollable container
      const containerRect = competitorScrollRef.current.getBoundingClientRect();
      const elementRect = competitorRef.getBoundingClientRect();
      const scrollTop = competitorScrollRef.current.scrollTop;
      const targetScrollTop = scrollTop + (elementRect.top - containerRect.top) - 10;
      
      competitorScrollRef.current.scrollTo({
        top: targetScrollTop,
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
      id: `msg-${Date.now()}-${Math.random()}`,
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    const currentInput = chatInput;
    setChatInput('');
    setIsSendingMessage(true);

    try {
      // Pass drug IDs to ensure comparison only uses selected drugs
      const response = await chatService.compare({
        message: `Comparing ${sourceDrug.name} vs ${competitorDrug.name}: ${currentInput}`,
        drug_ids: [sourceDrug.id, competitorDrug.id]
      });

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-${Math.random()}`,
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        timestamp: new Date().toISOString(),
        question: currentInput,
      };

      setChatMessages(prev => [...prev, assistantMessage]);
      
      // Scroll to bottom
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-${Math.random()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date().toISOString(),
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
  const competitorLoincs = new Set(competitorDrug.sections.map(s => s.loinc_code));
  const commonLoincs = sourceDrug.sections
    .map(s => s.loinc_code)
    .filter(l => competitorLoincs.has(l));

  const commonSections = sourceDrug.sections.filter(s => commonLoincs.includes(s.loinc_code));

  return (
    <div className="comparison-workspace h-screen flex flex-col overflow-hidden bg-background">
      {/* Header - Match Analysis Workspace Style */}
      <div className="border-b border-border bg-card px-6 py-4 flex-shrink-0 no-print">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/dashboard')}
              className="hover:bg-accent"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{sourceDrug.name}</h1>
              <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Building2 className="w-4 h-4" />
                  {sourceDrug.manufacturer}
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Version {sourceDrug.version}
                </div>
                <div className="flex items-center gap-1">
                  <ArrowLeftRight className="w-4 h-4" />
                  vs {competitorDrug.name}
                </div>
                {/* Competitor Selector (if multiple) */}
                {allCompetitors && allCompetitors.length > 1 && (
                  <div className="relative">
                    <select
                      value={selectedCompetitorIndex}
                      onChange={(e) => handleCompetitorChange(parseInt(e.target.value))}
                      className="px-2 py-1 pr-6 text-xs border border-border rounded bg-background appearance-none cursor-pointer hover:bg-accent"
                    >
                      {allCompetitors.map((comp, idx) => (
                        <option key={comp.id} value={idx}>
                          {comp.name}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 h-3 w-3 pointer-events-none" />
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Save Report Button - First, matching Analysis */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSaveModal(true)}
              className="no-print"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Report
            </Button>
            
            {/* Print Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="no-print"
            >
              <Printer className="w-4 h-4 mr-2" />
              Print
            </Button>
            
            {/* Notes Button - Badge shows count */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowNotesModal(true)}
              className="no-print relative"
            >
              <StickyNote className="w-4 h-4 mr-2" />
              Notes
              {(citedNotes.length + uncitedNotes.length) > 0 && (
                <span className="ml-2 px-1.5 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
                  {citedNotes.length + uncitedNotes.length}
                </span>
              )}
            </Button>
            
            {/* View Differences Button */}
            <Button
              variant={showDifferencesPanel ? 'default' : 'outline'}
              size="sm"
              onClick={loadSemanticDiff}
              disabled={isLoadingDiff}
              className="no-print"
            >
              <FileText className="w-4 h-4 mr-2" />
              {isLoadingDiff ? 'Loading...' : 'Differences'}
            </Button>
            
            {/* Generate Summary Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={loadExecutiveSummary}
              disabled={isLoadingSummary}
              className="no-print"
            >
              {isLoadingSummary ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <BarChart3 className="w-4 h-4 mr-2" />
              )}
              Summary
            </Button>
          </div>
        </div>
      </div>

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
        <div className="flex-1 flex gap-2 p-2 overflow-hidden justify-center">
          {/* Source Drug Paper */}
          <div ref={sourceScrollRef} className="flex-1 overflow-y-auto">
            <div className="paper-sheet" ref={sourceContentRef}>
              {/* Drug Header */}
              <div className="drug-header source-header">
                <h1 className="drug-name" style={{ fontSize: '11pt' }}>{sourceDrug.name}</h1>
                <div className="drug-meta" style={{ fontSize: '11pt' }}>
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
                    data-section-id={section.id}
                    data-section-title={section.title}
                  >
                    <h2 className="section-title" style={{ fontSize: '2.8pt' }}>{section.title}</h2>
                    <div className="section-content drug-label-content" style={{ fontSize: '3.5pt' }}>
                      <div 
                        dangerouslySetInnerHTML={{ __html: section.content_html || section.content }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Competitor Drug Paper */}
          <div ref={competitorScrollRef} className="flex-1 overflow-y-auto">
            <div className="paper-sheet">
              {/* Drug Header */}
              <div className="drug-header competitor-header">
                <h1 className="drug-name" style={{ fontSize: '11pt' }}>{competitorDrug.name}</h1>
                <div className="drug-meta" style={{ fontSize: '11pt' }}>
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
                    <h2 className="section-title" style={{ fontSize: '2.8pt' }}>{section.title}
                    </h2>
                    <div 
                      className="section-content"
                      style={{ fontSize: '3.5pt' }}
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

      {/* Loading Overlay for Executive Summary */}
      {isLoadingSummary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md">
            <Loading size="lg" text="Generating executive summary..." />
            <p className="text-sm text-muted-foreground text-center mt-4">
              Please wait while we analyze and summarize the comparison
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
              <div className="flex items-center gap-4">
                <h2 className="text-2xl font-bold">Differences</h2>
                {starredDiffIds.length > 0 && (
                  <button
                    onClick={() => setShowOnlyStarred(!showOnlyStarred)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      showOnlyStarred
                        ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <Star className={`h-4 w-4 ${showOnlyStarred ? 'fill-current' : ''}`} />
                    {showOnlyStarred ? 'Show All' : `Starred Only (${starredDiffIds.length})`}
                  </button>
                )}
              </div>
              <button
                onClick={() => setShowDifferencesPanel(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {(() => {
                const hasAnyVisibleMatches = semanticDiff.some((diffSection) => {
                  if (!showOnlyStarred) return true;
                  return diffSection.matches.some((_, idx) => {
                    const diffId = `${diffSection.section_loinc}_match_${idx}`;
                    return starredDiffIds.includes(diffId);
                  });
                });

                if (showOnlyStarred && !hasAnyVisibleMatches) {
                  return (
                    <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                      <Star className="h-16 w-16 mb-4 text-gray-300" />
                      <p className="text-lg font-medium">No starred differences yet</p>
                      <p className="text-sm mt-2">Star important differences to save them for later review</p>
                    </div>
                  );
                }

                return semanticDiff.map((diffSection) => {
                // Filter matches based on showOnlyStarred
                const filteredMatches = showOnlyStarred
                  ? diffSection.matches.filter((_, idx) => {
                      const diffId = `${diffSection.section_loinc}_match_${idx}`;
                      return starredDiffIds.includes(diffId);
                    })
                  : diffSection.matches;
                
                // Skip section if no matches after filtering
                if (filteredMatches.length === 0) return null;
                
                return (
                  <div key={diffSection.section_loinc} className="mb-8">
                    <div className="flex items-center justify-between mb-4 pb-2 border-b">
                      <h3 className="text-lg font-semibold text-primary">{diffSection.section_title}</h3>
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
                      {filteredMatches.map((match, originalIdx) => {
                        // Get original index for ID generation
                        const idx = showOnlyStarred 
                          ? diffSection.matches.indexOf(match)
                          : originalIdx;
                      const sourceSegment = match.source_segment;
                      const competitorSegment = match.competitor_segment;
                      const diffType = sourceSegment?.diff_type || competitorSegment?.diff_type || 'neutral';
                      
                      // Create unique ID for this diff match
                      const diffId = `${diffSection.section_loinc}_match_${idx}`;
                      const isStarred = starredDiffIds.includes(diffId);

                      return (
                        <div
                          key={idx}
                          className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                        >
                          {/* Header with Star Button */}
                          <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
                            <div className="flex items-center gap-2 text-xs text-gray-600">
                              <span className="font-medium">Match #{idx + 1}</span>
                              {match.similarity_score !== null && (
                                <span className="text-gray-500">
                                  • Similarity: {(match.similarity_score * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleStarDiff(diffId);
                              }}
                              className={`p-1.5 rounded transition-colors ${
                                isStarred 
                                  ? 'text-yellow-500 hover:text-yellow-600 bg-yellow-50' 
                                  : 'text-gray-400 hover:text-yellow-500 hover:bg-yellow-50'
                              }`}
                              title={isStarred ? 'Unstar this difference' : 'Star this difference'}
                            >
                              <Star 
                                className={`h-4 w-4 ${isStarred ? 'fill-current' : ''}`}
                              />
                            </button>
                          </div>

                          <div 
                            className="grid grid-cols-2 divide-x divide-gray-200 cursor-pointer"
                            onClick={() => {
                              const sourceText = sourceSegment?.text || '';
                              const competitorText = competitorSegment?.text || '';
                              handleExplainSegment(sourceText, competitorText, diffSection.section_loinc);
                            }}
                          >
                            {/* Source Column */}
                            <div className="p-4">
                              <div className="text-sm font-semibold text-gray-600 mb-2">{sourceDrug.name}</div>
                              {sourceSegment ? (
                                <div className={`p-3 rounded ${getDiffTypeColor(diffType)}`}>
                                  <div className="text-sm mb-2">
                                    <span className="font-semibold">{getDiffTypeLabel(diffType)}</span>
                                  </div>
                                  <div className="text-sm">{sourceSegment.text}</div>
                                </div>
                              ) : (
                                <div className="text-sm text-gray-400 italic p-3">No matching text</div>
                              )}
                            </div>

                            {/* Competitor Column */}
                            <div className="p-4">
                              <div className="text-sm font-semibold text-gray-600 mb-2">{competitorDrug.name}</div>
                              {competitorSegment ? (
                                <div className={`p-3 rounded ${getDiffTypeColor(diffType)}`}>
                                  <div className="text-sm mb-2">
                                    <span className="font-semibold">{getDiffTypeLabel(diffType)}</span>
                                  </div>
                                  <div className="text-sm">{competitorSegment.text}</div>
                                </div>
                              ) : (
                                <div className="text-sm text-gray-400 italic p-3">No matching text</div>
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
              );
            });
              })()}
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

      {/* Floating Chat Button - Match Analysis Workspace */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 bg-primary text-primary-foreground rounded-full p-4 shadow-lg hover:scale-110 transition-transform z-50 no-print"
          aria-label="Open chat"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
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
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-accent text-accent-foreground'
                    }`}
                  >
                    {/* Flag button for assistant messages */}
                    {msg.role === 'assistant' && (
                      <div className="flex justify-end mb-2">
                        <button
                          onClick={() => {
                            const isFlagged = storedFlaggedChats.some(c => c.id === msg.id);
                            if (isFlagged) {
                              unflagChat(msg.id);
                            } else {
                              flagChat(msg);
                            }
                          }}
                          className={`p-1 rounded hover:bg-gray-200/50 transition-colors ${
                            storedFlaggedChats.some(c => c.id === msg.id) ? 'text-yellow-600' : 'text-gray-500'
                          }`}
                          title={storedFlaggedChats.some(c => c.id === msg.id) ? 'Unflag' : 'Flag for report'}
                        >
                          <Flag className="h-4 w-4" fill={storedFlaggedChats.some(c => c.id === msg.id) ? 'currentColor' : 'none'} />
                        </button>
                      </div>
                    )}
                    
                    {msg.role === 'user' ? (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div 
                        className="text-sm prose prose-sm max-w-none"
                        style={{
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          lineHeight: '1.6'
                        }}
                        dangerouslySetInnerHTML={{ 
                          __html: msg.content
                            // Format markdown headers
                            .replace(/^### (.*?)$/gm, '<h3 class="text-base font-semibold mt-3 mb-2">$1</h3>')
                            .replace(/^## (.*?)$/gm, '<h2 class="text-lg font-bold mt-4 mb-2">$1</h2>')
                            .replace(/^# (.*?)$/gm, '<h1 class="text-xl font-bold mt-4 mb-3">$1</h1>')
                            // Format bold and italic
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*(.*?)\*/g, '<em>$1</em>')
                            // Format inline code
                            .replace(/`(.*?)`/g, '<code class="bg-gray-200 px-1 rounded text-xs">$1</code>')
                            // Format bullet points
                            .replace(/^- (.*?)$/gm, '<div class="ml-4 mb-1">• $1</div>')
                            // Format numbered lists
                            .replace(/^(\d+)\. (.*?)$/gm, '<div class="ml-4 mb-1">$1. $2</div>')
                            // Paragraphs and line breaks
                            .replace(/\n\n/g, '</p><p class="mt-2">')
                            .replace(/\n/g, '<br/>')
                        }}
                      />
                    )}
                    
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-xs font-semibold mb-2">Citations:</p>
                        <div className="space-y-1">
                          {msg.citations.map((citation, citIndex) => {
                            // Determine which paper this citation belongs to
                            const isSourceDrug = citation.drug_name === sourceDrug?.name;
                            const sectionKey = isSourceDrug 
                              ? `source-${citation.section_name}` 
                              : `competitor-${citation.section_name}`;
                            
                            return (
                              <button
                                key={citIndex}
                                onClick={() => {
                                  const sectionElement = sectionRefs.current[sectionKey];
                                  if (sectionElement) {
                                    // Scroll the appropriate paper container
                                    const scrollContainer = isSourceDrug ? sourceScrollRef.current : competitorScrollRef.current;
                                    if (scrollContainer) {
                                      const containerRect = scrollContainer.getBoundingClientRect();
                                      const sectionRect = sectionElement.getBoundingClientRect();
                                      const scrollTop = scrollContainer.scrollTop + (sectionRect.top - containerRect.top) - 20;
                                      scrollContainer.scrollTo({ top: scrollTop, behavior: 'smooth' });
                                    }
                                  }
                                }}
                                className="text-xs text-left w-full hover:underline text-primary flex items-start gap-1"
                              >
                                <span className="flex-shrink-0">→</span>
                                <span className="flex-1">
                                  {citation.section_name} <span className="opacity-60">({citation.drug_name})</span>
                                </span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            
            {isSendingMessage && (
              <div className="flex justify-start">
                <div className="bg-accent text-accent-foreground rounded-lg px-4 py-2">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
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
      
      {/* Save Report Modal */}
      <SaveReportModal
        isOpen={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        reportType="comparison"
        onSave={saveAsComparisonReport}
        previewData={{
          drugName: sourceDrug && competitorDrug 
            ? `${sourceDrug.name} vs ${competitorDrug.name}` 
            : 'Comparison',
          highlightsCount: sourceHighlights.length,
          notesCount: citedNotes.length + uncitedNotes.length,
          flaggedChatsCount: storedFlaggedChats.length,
          hasContent: sourceHighlights.length > 0 || citedNotes.length > 0 || uncitedNotes.length > 0 || storedFlaggedChats.length > 0
        }}
      />
      
      {/* Notes Modal */}
      <ComparisonNotesModal
        isOpen={showNotesModal}
        onClose={() => setShowNotesModal(false)}
      />
      
      {/* Highlight Popup for Source Drug */}
      {showHighlightPopup && selection && (
        <HighlightPopup
          position={highlightPopupPosition}
          onSelectColor={handleHighlightColor}
          onCancel={handleCancelHighlight}
        />
      )}
    </div>
  );
}
