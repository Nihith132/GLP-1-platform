import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { drugService } from '@/services/drugService';
import { analyticsService } from '@/services/analyticsService';
import { chatService } from '@/services/chatService';
import { Loading } from '../components/ui/Loading';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { 
  ArrowLeft, 
  MessageSquare, 
  X, 
  Send, 
  BarChart3,
  Calendar,
  Building2,
  Printer
} from 'lucide-react';
import type { Drug } from '@/types';
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

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    section_name: string;
    drug_name: string;
  }>;
}

export function AnalysisWorkspace() {
  const { drugId } = useParams<{ drugId: string }>();
  const navigate = useNavigate();
  
  const [drug, setDrug] = useState<DrugDetail | null>(null);
  const [analytics, setAnalytics] = useState<DrugAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  
  // Track scroll position for active section highlighting
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  
  const contentRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

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
      role: 'user',
      content: chatInput
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsSendingMessage(true);

    try {
      const response = await chatService.ask({
        message: chatInput,
        drug_id: drug.id
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
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
              onClick={() => window.print()}
              className="no-print"
            >
              <Printer className="w-4 h-4 mr-2" />
              Print Label
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

                {/* Section Content - Document Style */}
                <div>
                  <div 
                    className="drug-label-content"
                    dangerouslySetInnerHTML={{ __html: section.content_html || section.content }}
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
              
              {chatMessages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-accent text-accent-foreground'
                    }`}
                  >
                    <div 
                      className="text-sm prose prose-sm max-w-none"
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
    </div>
  );
}
