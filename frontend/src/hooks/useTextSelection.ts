import { useState, useEffect, useCallback } from 'react';

interface TextSelection {
  text: string;
  startOffset: number;
  endOffset: number;
  sectionId: number;
  rect: DOMRect | null;
}

export const useTextSelection = (containerRef: React.RefObject<HTMLElement>) => {
  const [selection, setSelection] = useState<TextSelection | null>(null);

  const handleSelectionChange = useCallback(() => {
    const sel = window.getSelection();
    
    if (!sel || sel.isCollapsed || !sel.rangeCount || !containerRef.current) {
      setSelection(null);
      return;
    }

    const range = sel.getRangeAt(0);
    const selectedText = sel.toString().trim();
    
    if (!selectedText || selectedText.length < 3) {
      setSelection(null);
      return;
    }

    // Check if selection is within our container
    const container = containerRef.current;
    if (!container.contains(range.commonAncestorContainer)) {
      setSelection(null);
      return;
    }

    // Find the section element
    let sectionElement = range.commonAncestorContainer as HTMLElement;
    while (sectionElement && !sectionElement.dataset?.sectionId) {
      sectionElement = sectionElement.parentElement as HTMLElement;
    }

    if (!sectionElement?.dataset?.sectionId) {
      console.error('❌ Could not find section element with data-section-id');
      setSelection(null);
      return;
    }

    const sectionId = parseInt(sectionElement.dataset.sectionId, 10);

    // CRITICAL FIX: Find the content container (.drug-label-content), not the section wrapper
    const contentContainer = sectionElement.querySelector('.drug-label-content');
    if (!contentContainer) {
      console.error('❌ Could not find .drug-label-content within section');
      setSelection(null);
      return;
    }

    console.log('📍 Text selection captured:', {
      sectionId,
      sectionTitle: sectionElement.dataset.sectionTitle,
      text: selectedText.substring(0, 50) + '...',
    });

    // Create a range from the start of the CONTENT (not section header) to the start of the selection
    const startRange = document.createRange();
    startRange.selectNodeContents(contentContainer);
    startRange.setEnd(range.startContainer, range.startOffset);
    const startOffset = startRange.toString().length;
    
    // Get the selected text length
    const selectedLength = range.toString().length;
    const endOffset = startOffset + selectedLength;

    const rect = range.getBoundingClientRect();

    console.log('📊 Offsets calculated:', { startOffset, endOffset, length: selectedLength });

    setSelection({
      text: selectedText,
      startOffset,
      endOffset,
      sectionId,
      rect,
    });
  }, [containerRef]);

  useEffect(() => {
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
    };
  }, [handleSelectionChange]);

  const clearSelection = useCallback(() => {
    window.getSelection()?.removeAllRanges();
    setSelection(null);
  }, []);

  return { selection, clearSelection };
};
