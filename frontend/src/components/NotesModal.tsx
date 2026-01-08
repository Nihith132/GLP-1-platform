import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, ExternalLink, Palette, Download, Copy, FileText, FileJson, FileCode } from 'lucide-react';
import { useWorkspaceStore } from '../store/workspaceStore';
import type { Note } from '../types';
import { exportAsJSON, exportAsText, exportAsMarkdown, copyToClipboard } from '../utils/exportUtils';

export const NotesModal: React.FC = () => {
  const {
    notes,
    highlights,
    isNotesModalOpen,
    setNotesModalOpen,
    addNote,
    updateNote,
    removeNote,
    removeHighlight,
    updateHighlightColor,
    setSelectedHighlightId,
    drugName,
  } = useWorkspaceStore();

  const [isAddingNote, setIsAddingNote] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [noteContent, setNoteContent] = useState('');
  const [expandedHighlights, setExpandedHighlights] = useState<Set<string>>(new Set());
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [exportStatus, setExportStatus] = useState<string>('');

  const handleExport = async (format: 'json' | 'text' | 'markdown' | 'clipboard') => {
    const exportData = {
      drugName: drugName || 'Unknown Drug',
      exportDate: new Date().toLocaleString(),
      highlights,
      notes,
    };

    try {
      switch (format) {
        case 'json':
          exportAsJSON(exportData);
          setExportStatus('✅ Exported as JSON');
          break;
        case 'text':
          exportAsText(exportData);
          setExportStatus('✅ Exported as Text');
          break;
        case 'markdown':
          exportAsMarkdown(exportData);
          setExportStatus('✅ Exported as Markdown');
          break;
        case 'clipboard':
          await copyToClipboard(exportData);
          setExportStatus('✅ Copied to clipboard');
          break;
      }
      
      setTimeout(() => {
        setExportStatus('');
        setShowExportMenu(false);
      }, 2000);
    } catch (error) {
      setExportStatus('❌ Export failed');
      setTimeout(() => setExportStatus(''), 2000);
    }
  };

  // Separate cited and uncited notes
  const citedNotes = notes.filter((note) => note.type === 'cited' && note.highlightId);
  const uncitedNotes = notes.filter((note) => note.type === 'uncited' || !note.highlightId);

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
    const highlight = highlights.find((h) => h.id === highlightId);
    return highlight?.text || 'Unknown highlight';
  };

  const handleAddNote = () => {
    if (noteContent.trim()) {
      addNote({
        type: 'uncited',
        content: noteContent.trim(),
      });
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
      removeNote(id);
    }
  };

  const handleCitationClick = (highlightId: string) => {
    setSelectedHighlightId(highlightId);
    // Scroll to the highlighted text
    const element = document.getElementById(`highlight-${highlightId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleDeleteHighlight = (highlightId: string) => {
    if (confirm('Delete this highlight? This will also delete the linked note.')) {
      removeHighlight(highlightId);
    }
  };

  const handleChangeHighlightColor = (highlightId: string, currentColor: 'red' | 'blue') => {
    const newColor = currentColor === 'red' ? 'blue' : 'red';
    updateHighlightColor(highlightId, newColor);
  };

  const getHighlightPreview = (highlightId: string) => {
    const highlight = highlights.find((h) => h.id === highlightId);
    if (!highlight) return 'Unknown highlight';
    return highlight.text.substring(0, 50) + (highlight.text.length > 50 ? '...' : '');
  };
  
  const getHighlightColor = (highlightId: string): 'red' | 'blue' => {
    const highlight = highlights.find((h) => h.id === highlightId);
    return highlight?.color || 'red';
  };

  if (!isNotesModalOpen) return null;

  const totalHighlights = highlights.length;
  const redHighlights = highlights.filter(h => h.color === 'red').length;
  const blueHighlights = highlights.filter(h => h.color === 'blue').length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Notes & Highlights</h2>
            <p className="text-sm text-gray-600 mt-1">
              Manage your analysis citations and notes
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Export Menu */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                <Download className="h-4 w-4" />
                Export
              </button>
              
              {showExportMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                  <button
                    onClick={() => handleExport('markdown')}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 text-sm"
                  >
                    <FileCode className="h-4 w-4 text-gray-600" />
                    <span>Markdown (.md)</span>
                  </button>
                  <button
                    onClick={() => handleExport('text')}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 text-sm"
                  >
                    <FileText className="h-4 w-4 text-gray-600" />
                    <span>Plain Text (.txt)</span>
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 text-sm"
                  >
                    <FileJson className="h-4 w-4 text-gray-600" />
                    <span>JSON (.json)</span>
                  </button>
                  <div className="border-t border-gray-200 my-2"></div>
                  <button
                    onClick={() => handleExport('clipboard')}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 text-sm"
                  >
                    <Copy className="h-4 w-4 text-gray-600" />
                    <span>Copy to Clipboard</span>
                  </button>
                  
                  {exportStatus && (
                    <div className="px-4 py-2 mt-2 text-sm text-center font-medium text-green-700 bg-green-50 border-t border-green-200">
                      {exportStatus}
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <button
              onClick={() => setNotesModalOpen(false)}
              className="p-2 hover:bg-white/50 rounded-lg transition-colors"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="px-6 py-4 bg-gray-50 border-b">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-sm font-medium text-gray-700">
                {totalHighlights} Highlights
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                {redHighlights} Red
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                {blueHighlights} Blue
              </span>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                {notes.length} Total Notes
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Cited Notes Section - Show only when highlights exist */}
          {citedNotes.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Cited Notes ({citedNotes.length})
              </h3>
              <div className="space-y-3">
                {citedNotes.map((note) => {
                  const highlightColor = note.highlightId ? getHighlightColor(note.highlightId) : 'red';
                  const isExpanded = note.highlightId ? expandedHighlights.has(note.highlightId) : false;
                  const fullText = note.highlightId ? getFullHighlightText(note.highlightId) : '';
                  
                  return (
                    <div
                      key={note.id}
                      className={`border-2 rounded-lg p-4 space-y-3 transition-all ${
                        highlightColor === 'red'
                          ? 'bg-red-50 border-red-200 hover:border-red-300'
                          : 'bg-blue-50 border-blue-200 hover:border-blue-300'
                      }`}
                    >
                      {/* Highlighted Text Preview */}
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
                              onClick={() => handleCitationClick(note.highlightId!)}
                              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                highlightColor === 'red'
                                  ? 'bg-red-100 text-red-700 hover:bg-red-200 border border-red-300'
                                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200 border border-blue-300'
                              }`}
                            >
                              Jump to Highlight
                            </button>
                            <button
                              onClick={() => handleChangeHighlightColor(note.highlightId!, highlightColor)}
                              className="px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                              title={`Change to ${highlightColor === 'red' ? 'blue' : 'red'}`}
                            >
                              <Palette className="h-4 w-4 text-gray-600" />
                            </button>
                            <button
                              onClick={() => handleDeleteHighlight(note.highlightId!)}
                              className="px-3 py-2 bg-white border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                              title="Delete highlight & note"
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
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                          rows={3}
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdateNote(note.id)}
                            className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setEditingNoteId(null);
                              setNoteContent('');
                            }}
                            className="px-3 py-1 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-gray-700 text-sm flex-1">{note.content}</p>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleEditClick(note)}
                            className="p-1 hover:bg-blue-200 rounded transition-colors"
                            title="Edit note"
                          >
                            <Edit2 className="h-4 w-4 text-blue-600" />
                          </button>
                          <button
                            onClick={() => handleDeleteNote(note.id)}
                            className="p-1 hover:bg-red-200 rounded transition-colors"
                            title="Delete note"
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Timestamp */}
                    <p className="text-xs text-gray-500">
                      {new Date(note.createdAt).toLocaleString()}
                    </p>
                  </div>
                );
                })}
              </div>
            </div>
          )}

          {/* Uncited Notes Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Uncited Notes ({uncitedNotes.length})
            </h3>
            {uncitedNotes.length === 0 && !isAddingNote ? (
              <p className="text-gray-500 text-sm italic">
                No uncited notes yet. Click "Add Note" to create one.
              </p>
            ) : (
              <div className="space-y-3">
                {uncitedNotes.map((note) => (
                  <div
                    key={note.id}
                    className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2"
                  >
                    {editingNoteId === note.id ? (
                      <div className="space-y-2">
                        <textarea
                          value={noteContent}
                          onChange={(e) => setNoteContent(e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                          rows={3}
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdateNote(note.id)}
                            className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setEditingNoteId(null);
                              setNoteContent('');
                            }}
                            className="px-3 py-1 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-gray-700 text-sm flex-1">{note.content}</p>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleEditClick(note)}
                            className="p-1 hover:bg-gray-300 rounded transition-colors"
                            title="Edit note"
                          >
                            <Edit2 className="h-4 w-4 text-gray-600" />
                          </button>
                          <button
                            onClick={() => handleDeleteNote(note.id)}
                            className="p-1 hover:bg-red-200 rounded transition-colors"
                            title="Delete note"
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </button>
                        </div>
                      </div>
                    )}

                    <p className="text-xs text-gray-500">
                      {new Date(note.createdAt).toLocaleString()}
                    </p>
                  </div>
                ))}

                {/* Add New Note Form */}
                {isAddingNote && (
                  <div className="bg-white border-2 border-blue-400 rounded-lg p-4 space-y-2">
                    <textarea
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      placeholder="Enter your note..."
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleAddNote}
                        className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                      >
                        Add Note
                      </button>
                      <button
                        onClick={() => {
                          setIsAddingNote(false);
                          setNoteContent('');
                        }}
                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer with Add Note Button */}
        {!isAddingNote && !editingNoteId && (
          <div className="p-6 border-t bg-gray-50">
            <button
              onClick={() => setIsAddingNote(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors ml-auto"
            >
              <Plus className="h-5 w-5" />
              Add Note
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
