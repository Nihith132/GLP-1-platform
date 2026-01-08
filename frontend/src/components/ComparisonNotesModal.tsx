import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, ExternalLink, StickyNote, FileText } from 'lucide-react';
import { useComparisonWorkspaceStore } from '../store/comparisonWorkspaceStore';

// Use the Note type from the store (matches snake_case convention)
interface Note {
  id: string;
  content: string;
  highlightId?: string;
  created_at: string;
  updated_at: string;
}

interface ComparisonNotesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ComparisonNotesModal: React.FC<ComparisonNotesModalProps> = ({ isOpen, onClose }) => {
  const {
    citedNotes,
    uncitedNotes,
    sourceHighlights,
    addUncitedNote,
    updateNote,
    deleteNote,
    removeSourceHighlight,
    sourceDrugName,
  } = useComparisonWorkspaceStore();

  const [isAddingNote, setIsAddingNote] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [noteContent, setNoteContent] = useState('');
  const [expandedHighlights, setExpandedHighlights] = useState<Set<string>>(new Set());

  const toggleHighlightExpand = (highlightId: string) => {
    setExpandedHighlights(prev => {
      const newSet = new Set(prev);
      if (newSet.has(highlightId)) {
        newSet.delete(highlightId);
      } else {
        newSet.add(highlightId);
      }
      return newSet;
    });
  };

  const getFullHighlightText = (highlightId: string) => {
    const highlight = sourceHighlights.find((h) => h.id === highlightId);
    return highlight?.text || 'Unknown highlight';
  };

  const handleAddNote = () => {
    if (noteContent.trim()) {
      const newNote: Note = {
        id: `note-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        content: noteContent.trim(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      addUncitedNote(newNote);
      setNoteContent('');
      setIsAddingNote(false);
    }
  };

  const handleUpdateNote = (id: string) => {
    if (noteContent.trim()) {
      updateNote(id, noteContent.trim());
      setNoteContent('');
      setEditingNoteId(null);
    }
  };

  const handleEditClick = (note: Note) => {
    setEditingNoteId(note.id);
    setNoteContent(note.content);
    setIsAddingNote(false);
  };

  const handleDeleteNote = (id: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      deleteNote(id);
    }
  };

  const handleCitationClick = (highlightId: string) => {
    // Scroll to the highlighted text
    const element = document.getElementById(`highlight-${highlightId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    onClose();
  };

  const handleDeleteHighlight = (highlightId: string) => {
    if (confirm('Delete this highlight? This will also delete the linked note.')) {
      removeSourceHighlight(highlightId);
    }
  };

  const getHighlightPreview = (highlightId: string) => {
    const highlight = sourceHighlights.find((h) => h.id === highlightId);
    if (!highlight) return 'Unknown highlight';
    return highlight.text.substring(0, 50) + (highlight.text.length > 50 ? '...' : '');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <StickyNote className="h-6 w-6 text-primary" />
            <div>
              <h2 className="text-2xl font-bold">Quick Notes</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {sourceDrugName || 'Comparison Workspace'} • {citedNotes.length + uncitedNotes.length} notes
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Cited Notes Section - Show only when highlights exist */}
          {citedNotes.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-semibold">Cited Notes ({citedNotes.length})</h3>
              </div>
              
              <div className="space-y-4">
                {citedNotes.map((note) => {
                  const isExpanded = expandedHighlights.has(note.highlightId || '');
                  const highlight = sourceHighlights.find(h => h.id === note.highlightId);
                  const highlightColor = highlight?.color || 'red';
                  const fullText = getFullHighlightText(note.highlightId || '');
                  
                  return (
                    <div 
                      key={note.id} 
                      className={`border-2 rounded-lg p-4 space-y-3 transition-all ${
                        highlightColor === 'red'
                          ? 'bg-red-50 border-red-200 hover:border-red-300'
                          : 'bg-blue-50 border-blue-200 hover:border-blue-300'
                      }`}
                    >
                      {/* Citation Section with Color Coding */}
                      {note.highlightId && (
                        <div className="space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <button
                              onClick={() => toggleHighlightExpand(note.highlightId!)}
                              className="flex-1 text-left"
                            >
                              <div className={`p-3 rounded-md ${
                                highlightColor === 'red'
                                  ? 'bg-red-100 border border-red-300'
                                  : 'bg-blue-100 border border-blue-300'
                              }`}>
                                <div className="flex items-start gap-2">
                                  <ExternalLink className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                                    highlightColor === 'red' ? 'text-red-600' : 'text-blue-600'
                                  }`} />
                                  <div className="flex-1 min-w-0">
                                    <p className={`text-sm font-medium italic ${
                                      highlightColor === 'red' ? 'text-red-900' : 'text-blue-900'
                                    }`}>
                                      {isExpanded ? fullText : `"${getHighlightPreview(note.highlightId!)}"`}
                                    </p>
                                    {fullText.length > 50 && (
                                      <button className={`text-xs mt-1 font-medium ${
                                        highlightColor === 'red' ? 'text-red-600 hover:text-red-800' : 'text-blue-600 hover:text-blue-800'
                                      }`}>
                                        {isExpanded ? 'Show less' : 'Show full text'}
                                      </button>
                                    )}
                                  </div>
                                  <span 
                                    className={`px-2 py-1 rounded text-xs font-bold ${
                                      highlightColor === 'red' 
                                        ? 'bg-red-200 text-red-800' 
                                        : 'bg-blue-200 text-blue-800'
                                    }`}
                                  >
                                    {highlightColor === 'red' ? 'RED' : 'BLUE'}
                                  </span>
                                </div>
                              </div>
                            </button>
                          </div>
                          
                          {/* Quick Actions */}
                          <div className="flex gap-2">
                            <button
                              onClick={() => note.highlightId && handleCitationClick(note.highlightId)}
                              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                                highlightColor === 'red'
                                  ? 'bg-red-100 hover:bg-red-200 text-red-700'
                                  : 'bg-blue-100 hover:bg-blue-200 text-blue-700'
                              }`}
                            >
                              <ExternalLink className="h-4 w-4" />
                              Go to Citation
                            </button>
                            <button
                              onClick={() => note.highlightId && handleDeleteHighlight(note.highlightId)}
                              className="px-3 py-2 bg-red-100 hover:bg-red-200 rounded-lg transition-colors text-red-700 text-sm font-medium"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Note Content */}
                      {editingNoteId === note.id ? (
                        <div className="space-y-2">
                          <textarea
                            value={noteContent}
                            onChange={(e) => setNoteContent(e.target.value)}
                            className="w-full p-3 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                            rows={4}
                            placeholder="Edit your note..."
                            autoFocus
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleUpdateNote(note.id)}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => {
                                setEditingNoteId(null);
                                setNoteContent('');
                              }}
                              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-gray-700 flex-1 whitespace-pre-wrap">{note.content}</p>
                          <div className="flex gap-1 flex-shrink-0">
                            <button
                              onClick={() => handleEditClick(note)}
                              className="p-1.5 hover:bg-blue-100 rounded transition-colors"
                              title="Edit note"
                            >
                              <Edit2 className="h-4 w-4 text-blue-600" />
                            </button>
                            <button
                              onClick={() => handleDeleteNote(note.id)}
                              className="p-1.5 hover:bg-red-100 rounded transition-colors"
                              title="Delete note"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          </div>
                        </div>
                      )}

                      <div className={`mt-2 text-xs ${highlightColor === 'red' ? 'text-red-600' : 'text-blue-600'}`}>
                        {new Date(note.created_at).toLocaleString()}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Uncited Notes Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <StickyNote className="h-5 w-5 text-gray-600" />
                <h3 className="text-lg font-semibold">Uncited Notes ({uncitedNotes.length})</h3>
              </div>
              {!isAddingNote && !editingNoteId && (
                <button
                  onClick={() => setIsAddingNote(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                >
                  <Plus className="h-4 w-4" />
                  Add Note
                </button>
              )}
            </div>

            {/* Add Note Form */}
            {isAddingNote && (
              <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <textarea
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                  rows={4}
                  placeholder="Write your note..."
                  autoFocus
                />
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={handleAddNote}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                  >
                    Save Note
                  </button>
                  <button
                    onClick={() => {
                      setIsAddingNote(false);
                      setNoteContent('');
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Uncited Notes List */}
            {uncitedNotes.length > 0 ? (
              <div className="space-y-4">
                {uncitedNotes.map((note) => (
                  <div key={note.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    {editingNoteId === note.id ? (
                      <div className="space-y-2">
                        <textarea
                          value={noteContent}
                          onChange={(e) => setNoteContent(e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                          rows={4}
                          placeholder="Edit your note..."
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdateNote(note.id)}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setEditingNoteId(null);
                              setNoteContent('');
                            }}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-gray-700 flex-1 whitespace-pre-wrap">{note.content}</p>
                          <div className="flex gap-1 flex-shrink-0">
                            <button
                              onClick={() => handleEditClick(note)}
                              className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                              title="Edit note"
                            >
                              <Edit2 className="h-4 w-4 text-gray-600" />
                            </button>
                            <button
                              onClick={() => handleDeleteNote(note.id)}
                              className="p-1.5 hover:bg-red-100 rounded transition-colors"
                              title="Delete note"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                          {new Date(note.created_at).toLocaleString()}
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              !isAddingNote && (
                <div className="text-center py-8 text-gray-500">
                  <StickyNote className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                  <p>No uncited notes yet</p>
                  <p className="text-sm mt-1">Click "Add Note" to create one</p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
