import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { drugService } from '@/services/drugService';
import { analyticsService } from '@/services/analyticsService';
import { chatService } from '@/services/chatService';
import { useChatStore } from '@/store/chatStore';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { NotesModal } from '../components/NotesModal';
import { HighlightPopup } from '../components/HighlightPopup';
import { HighlightRenderer } from '../components/HighlightRenderer';
import { SaveReportModal } from '../components/SaveReportModal';
import { useTextSelection } from '../hooks/useTextSelection';
import { 
  ArrowLeft, 
  MessageSquare, 
  X, 
  Send, 
  BarChart3,
  Calendar,
  Building2,
  Printer,
  Flag,
  StickyNote,
  Save
} from 'lucide-react';
import type { Drug, ChatMessage } from '@/types';
import './AnalysisWorkspace.css';

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
}

interface DrugLabel {
  meta: {
    set_id: string;
    brand_name: string;
    generic_name: string;
    version_number: number;
    last_updated: string;
  };
  sections: {
    id: string;
    loinc_code: string;
    title: string;
    content: string;
    subsections?: {
      id: string;
      title: string;
      content: string;
    }[];
  }[];
}

interface DrugDetail extends Drug {
  sections: DrugSection[];
}

interface DrugAnalytics {
  drug_id: number;
  drug_name: string;
  total_sections: number;
  total_entities: number;
  entity_breakdown: Array<{
    entity_type: string;
    count: number;
    percentage: number;
  }>;
  most_common_entities: Array<{
    entity_type: string;
    count: number;
  }>;
}

export function AnalysisWorkspace() {
  const { drugId } = useParams<{ drugId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const loadReportId = searchParams.get('loadReport');
  
  // Chat store
  const { messages: chatMessages, addMessage, toggleFlag, getFlaggedMessages, restoreMessages } = useChatStore();
  
  // Workspace store for notes and highlights
  const { 
    setNotesModalOpen, 
    notes, 
    addHighlight, 
    addNote, 
    setDrug: setWorkspaceDrug,
    syncFlaggedChats,
    loadReport: loadWorkspaceReport 
  } = useWorkspaceStore();
  
  const [drug, setDrug] = useState<DrugDetail | null>(null);
  const [analytics, setAnalytics] = useState<DrugAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [isSaveReportModalOpen, setIsSaveReportModalOpen] = useState(false);
  const [isRestoringReport, setIsRestoringReport] = useState(false);
  
  // Track scroll position for active section highlighting
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  
  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Text selection and highlighting
  const { selection, clearSelection } = useTextSelection(contentRef);
  const [showColorPicker, setShowColorPicker] = useState(false);

  useEffect(() => {
    if (drugId) {
      loadDrugData(parseInt(drugId));
    }
  }, [drugId]);

  useEffect(() => {
    // Auto-scroll chat to bottom
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  const loadDrugData = async (id: number) => {
    try {
      setIsLoading(true);
      const [drugData, analyticsData] = await Promise.all([
        drugService.getDrugById(id),
        analyticsService.getDrugAnalytics(id)
      ]);
      
      // Type cast since getDrugById returns drug with sections
      setDrug(drugData as any);
      setAnalytics(analyticsData);
      
      // Set first section as active
      const sections = (drugData as any).sections;
      if (sections && sections.length > 0) {
        setActiveSection(sections[0].title);
      }
    } catch (err) {
      console.error('Error loading drug data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const restoreReport = async (report: any) => {
    try {
      setIsRestoringReport(true);
      
      console.log('📝 Restoring report:', report);
      
      // Wait a moment for DOM to be fully ready
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Restore workspace state (highlights, notes, flagged chats, scroll position)
      if (report.workspace_state) {
        loadWorkspaceReport(report.workspace_state);
        console.log('✅ Workspace state restored');
        
        // Restore flagged chat messages to chat store
        if (report.workspace_state.flaggedChats && report.workspace_state.flaggedChats.length > 0) {
          restoreMessages(report.workspace_state.flaggedChats);
          console.log('💬 Chat messages restored:', report.workspace_state.flaggedChats.length);
        }
      }
      
      // Restore scroll position after a short delay
      if (report.workspace_state?.scrollPosition && contentRef.current) {
        setTimeout(() => {
          if (contentRef.current) {
            contentRef.current.scrollTop = report.workspace_state.scrollPosition;
            console.log('📜 Scroll position restored');
          }
        }, 500);
      }
      
      console.log('🎉 Report restoration complete!');
    } catch (error) {
      console.error('❌ Failed to restore report:', error);
      alert('Failed to restore report. Some data may be missing.');
    } finally {
      setIsRestoringReport(false);
    }
  };

  useEffect(() => {
    // Intersection Observer for active section tracking
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
            const sectionTitle = entry.target.getAttribute('data-section-title');
            if (sectionTitle) {
              setActiveSection(sectionTitle);
            }
          }
        });
      },
      {
        root: contentRef.current,
        rootMargin: '-100px 0px -60% 0px',
        threshold: [0, 0.5, 1],
      }
    );

    Object.values(sectionRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, [drug]);

  // Update workspace store when drug changes
  useEffect(() => {
    if (drug) {
      setWorkspaceDrug(drug.id, drug.name);
    }
  }, [drug, setWorkspaceDrug]);

  // Sync flagged chats to workspace store whenever chat messages change
  useEffect(() => {
    const flaggedMessages = getFlaggedMessages();
    syncFlaggedChats(flaggedMessages);
  }, [chatMessages, getFlaggedMessages, syncFlaggedChats]);

  // Handle report restoration from Reports page
  useEffect(() => {
    if (loadReportId && drug) {
      const pendingReport = sessionStorage.getItem('pendingReportLoad');
      if (pendingReport) {
        try {
          const report = JSON.parse(pendingReport);
          restoreReport(report);
          sessionStorage.removeItem('pendingReportLoad');
        } catch (error) {
          console.error('Failed to parse pending report:', error);
        }
      }
    }
  }, [loadReportId, drug]);

  // Show color picker when text is selected
  useEffect(() => {
    if (selection) {
      setShowColorPicker(true);
    } else {
      setShowColorPicker(false);
    }
  }, [selection]);

  const handleColorSelect = (color: 'red' | 'blue') => {
    if (!selection) return;

    console.log('➕ Adding highlight:', {
      sectionId: selection.sectionId,
      color,
      text: selection.text.substring(0, 50) + '...',
      startOffset: selection.startOffset,
      endOffset: selection.endOffset,
    });

    // Add highlight with position data
    const highlightId = addHighlight({
      sectionId: selection.sectionId,
      startOffset: selection.startOffset,
      endOffset: selection.endOffset,
      text: selection.text,
      color,
      rect: selection.rect ? {
        top: selection.rect.top + window.scrollY,
        left: selection.rect.left,
        width: selection.rect.width,
        height: selection.rect.height,
      } : undefined,
    });

    console.log('✅ Highlight added with ID:', highlightId);

    // Automatically create a cited note for this highlight
    addNote({
      type: 'cited',
      content: '', // Empty content, user will fill it in
      highlightId,
    });

    // Clear selection and hide popup
    clearSelection();
    setShowColorPicker(false);
  };

  const handleCancelHighlight = () => {
    clearSelection();
    setShowColorPicker(false);
  };

  const scrollToSection = (sectionTitle: string) => {
    setActiveSection(sectionTitle);
    const ref = sectionRefs.current[sectionTitle];
    if (ref) {
      ref.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !drug) return;

    const userMessage: ChatMessage = {
      id: `${Date.now()}_user`,
      role: 'user',
      content: chatInput,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setChatInput('');
    setIsSendingMessage(true);

    try {
      const response = await chatService.ask({
        message: chatInput,
        drug_id: drug.id
      });

      const assistantMessage: ChatMessage = {
        id: `${Date.now()}_assistant`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        citations: response.citations?.map(c => ({
          ...c,
          relevance_score: 0 // Default value since API doesn't return it
        })),
        isFlagged: false,
      };

      addMessage(assistantMessage);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage: ChatMessage = {
        id: `${Date.now()}_error`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date(),
        isFlagged: false,
      };
      addMessage(errorMessage);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleCitationClick = (citation: { section_name: string }) => {
    // Find section by title
    const section = drug?.sections.find(s => 
      s.title.toLowerCase() === citation.section_name.toLowerCase()
    );
    if (section) {
      scrollToSection(section.title);
      setIsChatOpen(false);
    }
  };

  if (isLoading) {
    return <Loading />;
  }

  if (!drug) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-xl text-muted-foreground">Drug not found</p>
          <Button onClick={() => navigate('/dashboard')} className="mt-4">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-background">
      {/* Header */}
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
              <h1 className="text-2xl font-bold text-foreground">{drug.name}</h1>
              <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Building2 className="w-4 h-4" />
                  {drug.manufacturer}
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Version {drug.version}
                </div>
                {drug.generic_name && (
                  <Badge variant="secondary">{drug.generic_name}</Badge>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsSaveReportModalOpen(true)}
              className="no-print"
            >
              <Save className="w-4 h-4 mr-2" />
              Save as Report
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="no-print"
            >
              <Printer className="w-4 h-4 mr-2" />
              Print Label
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setNotesModalOpen(true)}
              className="no-print relative"
            >
              <StickyNote className="w-4 h-4 mr-2" />
              Notes
              {notes.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {notes.length}
                </span>
              )}
            </Button>
            <Button
              variant={showAnalytics ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowAnalytics(!showAnalytics)}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Section Navigation */}
        <div className="w-96 border-r border-gray-200 bg-white overflow-y-auto flex-shrink-0 no-print">
          <div className="p-6 sticky top-0 bg-white border-b border-gray-100 z-10">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Contents
            </h2>
            <p className="text-xs text-gray-400">{drug.sections.length} sections</p>
          </div>
          <nav className="p-4">
            <ul className="space-y-0.5">
              {drug.sections.map((section) => {
                const indentLevel = (section.level || 1) - 1;
                const marginLeft = indentLevel * 16; // 16px per level
                
                return (
                  <li key={section.id}>
                    <button
                      onClick={() => scrollToSection(section.title)}
                      style={{ marginLeft: `${marginLeft}px` }}
                      className={`w-full text-left px-3 py-2.5 rounded-md text-sm transition-all group ${
                        activeSection === section.title
                          ? 'bg-blue-50 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate">
                          {section.section_number && (
                            <span className="text-gray-400 mr-2">{section.section_number}</span>
                          )}
                          {section.title}
                        </span>
                        {activeSection === section.title && (
                          <div className="w-1 h-1 bg-blue-600 rounded-full flex-shrink-0" />
                        )}
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        {/* Center - Label Content (Stripe Docs Style) */}
        <div 
          ref={contentRef}
          className="flex-1 overflow-y-auto label-content-area transition-all duration-300"
        >
          {/* Drug Label - Paper Style */}
          <div className="paper-sheet">
            {drug.sections.map((section) => (
              <div
                key={section.id}
                ref={(el) => (sectionRefs.current[section.title] = el)}
                data-section-title={section.title}
                data-section-id={section.id}
                className="mb-8 last:mb-0"
              >
                {/* Section Header - FDA Style */}
                <div className="mb-4">
                  <h2 className="font-bold uppercase mb-1" style={{fontFamily: "'Times New Roman', Times, serif", fontSize: '13pt', color: '#000', borderBottom: '2px solid #000', paddingBottom: '4px'}}>
                    {section.section_number && (
                      <span className="text-gray-500 mr-2">{section.section_number}</span>
                    )}
                    {section.title}
                  </h2>
                </div>

                {/* Section Content - Document Style with Highlighting */}
                <div className="drug-label-content">
                  <HighlightRenderer 
                    sectionId={section.id}
                    content={section.content_html || section.content}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Floating Chat Modal */}
      {isChatOpen && (
        <>
          {/* Backdrop overlay */}
          <div 
            className="fixed inset-0 bg-black/50 z-40 no-print"
            onClick={() => setIsChatOpen(false)}
          />
          
          {/* Chat Modal */}
          <div className="fixed bottom-6 right-6 w-[450px] h-[600px] bg-card border border-border rounded-xl shadow-2xl flex flex-col z-50 no-print animate-slide-in">
            {/* Chat Header */}
            <div className="px-4 py-3 border-b border-border flex items-center justify-between">
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                RAG Chat Assistant
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsChatOpen(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.length === 0 && (
                <div className="text-center text-muted-foreground text-sm py-8">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Ask me anything about {drug.name}</p>
                  <p className="text-xs mt-2">I'll provide answers with citations</p>
                </div>
              )}
              
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 relative ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-accent text-accent-foreground'
                    }`}
                  >
                    {/* Flag button for assistant messages */}
                    {message.role === 'assistant' && (
                      <button
                        onClick={() => toggleFlag(message.id)}
                        className={`absolute top-2 right-2 p-1 rounded hover:bg-background/10 transition-colors ${
                          message.isFlagged ? 'text-red-500' : 'text-muted-foreground'
                        }`}
                        title={message.isFlagged ? 'Unflag' : 'Flag for report'}
                      >
                        <Flag className={`w-4 h-4 ${message.isFlagged ? 'fill-current' : ''}`} />
                      </button>
                    )}
                    
                    <div 
                      className="text-sm prose prose-sm max-w-none pr-8"
                      style={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        lineHeight: '1.6'
                      }}
                      dangerouslySetInnerHTML={{ 
                        __html: message.content
                          .replace(/\n\n/g, '</p><p class="mt-2">')
                          .replace(/\n/g, '<br/>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/`(.*?)`/g, '<code class="bg-gray-200 px-1 rounded">$1</code>')
                      }}
                    />
                    
                    {message.citations && message.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-xs font-semibold mb-2">Citations:</p>
                        <div className="space-y-1">
                          {message.citations.map((citation, citIndex) => (
                            <button
                              key={citIndex}
                              onClick={() => handleCitationClick(citation)}
                              className="text-xs text-left w-full hover:underline text-primary"
                            >
                              → {citation.section_name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
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

            {/* Chat Input */}
            <div className="p-4 border-t border-border">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isSendingMessage && handleSendMessage()}
                  placeholder="Ask about this drug..."
                  className="flex-1 px-4 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isSendingMessage}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!chatInput.trim() || isSendingMessage}
                  size="sm"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Analytics Modal */}
      {showAnalytics && analytics && (
        <>
          {/* Backdrop overlay */}
          <div 
            className="fixed inset-0 bg-black/50 z-40 no-print"
            onClick={() => setShowAnalytics(false)}
          />
          
          {/* Analytics Modal */}
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] max-h-[80vh] bg-card border border-border rounded-xl shadow-2xl overflow-auto z-50 no-print">
            <div className="p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <BarChart3 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Label Analytics</h2>
                    <p className="text-sm text-gray-500">Entity extraction & statistics</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAnalytics(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="grid grid-cols-3 gap-6 mb-8">
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-3xl font-bold text-gray-900">{analytics.total_sections}</div>
                  <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">Sections</div>
                </div>
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-3xl font-bold text-gray-900">{analytics.total_entities}</div>
                  <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">Entities</div>
                </div>
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-3xl font-bold text-gray-900">{analytics.entity_breakdown.length}</div>
                  <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">Types</div>
                </div>
              </div>

              {analytics.entity_breakdown.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Entity Types</h3>
                  <div className="space-y-3">
                    {analytics.entity_breakdown.slice(0, 5).map((entity, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-medium text-gray-700">{entity.entity_type}</span>
                          <span className="text-xs text-gray-500">
                            {entity.count} ({entity.percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                          <div 
                            className="bg-blue-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${entity.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Floating Chat Button */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 bg-primary text-primary-foreground rounded-full p-4 shadow-lg hover:scale-110 transition-transform z-50 no-print"
          aria-label="Open chat"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}

      {/* Notes Modal */}
      <NotesModal />

      {/* Save Report Modal */}
      <SaveReportModal 
        isOpen={isSaveReportModalOpen}
        onClose={() => setIsSaveReportModalOpen(false)}
      />

      {/* Highlight Color Picker Popup */}
      {showColorPicker && selection && selection.rect && (
        <HighlightPopup
          position={{
            top: selection.rect.top + window.scrollY,
            left: selection.rect.left + selection.rect.width / 2,
          }}
          onSelectColor={handleColorSelect}
          onCancel={handleCancelHighlight}
        />
      )}

      {/* Report Restoration Loading Overlay */}
      {isRestoringReport && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 shadow-2xl max-w-md">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Restoring Report</h3>
              <p className="text-sm text-gray-500 text-center">
                Loading highlights, notes, and flagged chats...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
