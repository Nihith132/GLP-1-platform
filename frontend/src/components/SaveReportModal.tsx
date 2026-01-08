import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { reportService } from '../services/reportService';

interface SaveReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportType?: 'analysis' | 'comparison';
  onSave?: (title: string, description?: string, tags?: string[]) => Promise<void>;
  previewData?: {
    drugName: string;
    highlightsCount: number;
    notesCount: number;
    flaggedChatsCount: number;
    hasContent: boolean;
  };
}

export const SaveReportModal: React.FC<SaveReportModalProps> = ({ 
  isOpen, 
  onClose, 
  reportType = 'analysis',
  onSave: customOnSave,
  previewData
}) => {
  const { saveAsReport, highlights, notes, flaggedChats, drugName } = useWorkspaceStore();
  
  // Use preview data if provided, otherwise use workspace store
  const effectiveDrugName = previewData?.drugName || drugName;
  const effectiveHighlightsCount = previewData?.highlightsCount ?? highlights.length;
  const effectiveNotesCount = previewData?.notesCount ?? Object.keys(notes).length;
  const effectiveFlaggedChatsCount = previewData?.flaggedChatsCount ?? flaggedChats.length;
  const hasContent = previewData?.hasContent ?? (highlights.length > 0 || Object.keys(notes).length > 0 || flaggedChats.length > 0);
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [existingReportTitles, setExistingReportTitles] = useState<string[]>([]);

  // Load existing report titles when modal opens
  useEffect(() => {
    if (isOpen) {
      loadExistingTitles();
    }
  }, [isOpen]);

  const loadExistingTitles = async () => {
    try {
      const reports = await reportService.getAllReports();
      const titles = reports.map(r => r.title.toLowerCase().trim());
      setExistingReportTitles(titles);
    } catch (error) {
      console.error('Failed to load existing reports:', error);
    }
  };

  const validateInputs = (): string | null => {
    if (!title.trim()) {
      return 'Please enter a report title';
    }
    if (title.length > 200) {
      return 'Title is too long (max 200 characters)';
    }
    
    // Check for duplicate title
    const normalizedTitle = title.toLowerCase().trim();
    if (existingReportTitles.includes(normalizedTitle)) {
      return 'A report with this title already exists. Please use a different name.';
    }
    
    if (!hasContent) {
      return `Cannot save empty ${reportType} report. Add highlights, notes, or flag chats first.`;
    }
    return null;
  };

  const handleSave = async () => {
    const validationError = validateInputs();
    if (validationError) {
      setErrorMessage(validationError);
      setSaveStatus('error');
      return;
    }

    setIsSaving(true);
    setSaveStatus('idle');
    setErrorMessage('');

    try {
      // Parse tags
      const parsedTags = tags.trim() 
        ? tags.split(',').map(t => t.trim()).filter(t => t.length > 0)
        : undefined;

      // Use custom save function if provided, otherwise use workspace store
      if (customOnSave) {
        await customOnSave(title.trim(), description.trim() || undefined, parsedTags);
      } else {
        await saveAsReport(
          title.trim(), 
          description.trim() || undefined,
          parsedTags
        );
      }
      
      setSaveStatus('success');
      
      // Close modal after 1.5 seconds
      setTimeout(() => {
        onClose();
        // Reset form
        setTitle('');
        setDescription('');
        setTags('');
        setSaveStatus('idle');
      }, 1500);
    } catch (error) {
      console.error('Failed to save report:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Failed to save report');
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    if (!isSaving) {
      onClose();
      setSaveStatus('idle');
      setErrorMessage('');
    }
  };

  if (!isOpen) return null;

  const reportTypeLabel = reportType === 'comparison' ? 'Comparison' : 'Analysis';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Save {reportTypeLabel} Report</h2>
            <p className="text-sm text-gray-600 mt-1">
              Save your current {reportType} workspace for later access
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={isSaving}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Workspace Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">What will be saved:</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-700">
                  <strong>{effectiveDrugName || 'Unknown Drug'}</strong>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-700">
                  <strong>{effectiveHighlightsCount}</strong> Highlights
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-sm text-gray-700">
                  <strong>{effectiveNotesCount}</strong> Notes
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <span className="text-sm text-gray-700">
                  <strong>{effectiveFlaggedChatsCount}</strong> Flagged Chats
                </span>
              </div>
            </div>
            {!hasContent && (
              <div className="mt-3 flex items-start gap-2 text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <p className="text-sm">
                  Your workspace is empty. Add highlights, notes, or flag chats before saving.
                </p>
              </div>
            )}
          </div>

          {/* Title Input */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Report Title <span className="text-red-500">*</span>
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                // Clear error when user starts typing
                if (saveStatus === 'error') {
                  setSaveStatus('idle');
                  setErrorMessage('');
                }
              }}
              placeholder="e.g., Ozempic Safety Analysis - January 2026"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                title.trim() && existingReportTitles.includes(title.toLowerCase().trim())
                  ? 'border-red-300 bg-red-50'
                  : 'border-gray-300'
              }`}
              disabled={isSaving}
              maxLength={200}
            />
            <div className="flex items-center justify-between mt-1">
              <p className="text-xs text-gray-500">
                {title.length}/200 characters
              </p>
              {title.trim() && existingReportTitles.includes(title.toLowerCase().trim()) && (
                <p className="text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Title already exists
                </p>
              )}
            </div>
          </div>

          {/* Description Input (Optional) */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description <span className="text-gray-400">(Optional)</span>
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add notes about this analysis..."
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={isSaving}
            />
          </div>

          {/* Tags Input (Optional) */}
          <div>
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
              Tags <span className="text-gray-400">(Optional, comma-separated)</span>
            </label>
            <input
              id="tags"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., safety, efficacy, cardiovascular"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSaving}
            />
          </div>

          {/* Status Messages */}
          {saveStatus === 'success' && (
            <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg p-3">
              <CheckCircle className="h-5 w-5 flex-shrink-0" />
              <p className="text-sm font-medium">Report saved successfully!</p>
            </div>
          )}

          {saveStatus === 'error' && errorMessage && (
            <div className="flex items-start gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
              <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm">{errorMessage}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={handleClose}
            disabled={isSaving}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !hasContent}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Save Report</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
