import React, { useEffect, useRef } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';

interface HighlightRendererProps {
  sectionId: number;
  content: string;
}

export const HighlightRenderer: React.FC<HighlightRendererProps> = ({
  sectionId,
  content,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { highlights, setSelectedHighlightId, setNotesModalOpen } = useWorkspaceStore();

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const sectionHighlights = highlights.filter((h) => h.sectionId === sectionId);

    console.log('🎨 HighlightRenderer:', {
      sectionId,
      highlightCount: sectionHighlights.length,
      highlights: sectionHighlights
    });

    // Clear previous highlights
    const existingMarks = container.querySelectorAll('.highlight-mark');
    existingMarks.forEach((mark) => {
      const parent = mark.parentNode;
      while (mark.firstChild) {
        parent?.insertBefore(mark.firstChild, mark);
      }
      parent?.removeChild(mark);
    });
    container.normalize();

    if (sectionHighlights.length === 0) {
      console.log('❌ No highlights for section', sectionId);
      return;
    }

    // Apply highlights
    sectionHighlights.forEach((highlight, idx) => {
      console.log(`🔍 Processing highlight ${idx + 1}:`, {
        text: highlight.text,
        startOffset: highlight.startOffset,
        endOffset: highlight.endOffset,
        color: highlight.color
      });

      const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null
      );

      let currentOffset = 0;
      let textNode: Text | null;
      const nodesToHighlight: Array<{ node: Text; startInNode: number; endInNode: number }> = [];

      while ((textNode = walker.nextNode() as Text)) {
        const nodeLength = textNode.textContent?.length || 0;
        const nodeStart = currentOffset;
        const nodeEnd = currentOffset + nodeLength;

        // Check if highlight overlaps with this text node
        if (highlight.startOffset < nodeEnd && highlight.endOffset > nodeStart) {
          const startInNode = Math.max(0, highlight.startOffset - nodeStart);
          const endInNode = Math.min(nodeLength, highlight.endOffset - nodeStart);

          if (startInNode < endInNode) {
            nodesToHighlight.push({ node: textNode, startInNode, endInNode });
          }
        }

        currentOffset = nodeEnd;
      }

      console.log(`✅ Found ${nodesToHighlight.length} text nodes to highlight`);

      // Apply highlighting to collected nodes (in reverse to preserve positions)
      nodesToHighlight.reverse().forEach(({ node, startInNode, endInNode }) => {
        const range = document.createRange();
        range.setStart(node, startInNode);
        range.setEnd(node, endInNode);

        const mark = document.createElement('mark');
        mark.className = 'highlight-mark';
        mark.dataset.highlightId = highlight.id;

        const isRed = highlight.color === 'red';
        const bgColor = isRed ? '#ffcccc' : '#ccddff';  // BRIGHTER, less transparent
        const borderColor = isRed ? '#ff0000' : '#0066ff';  // STRONGER colors

        mark.style.cssText = `
          background-color: ${bgColor} !important;
          border-bottom: 4px solid ${borderColor} !important;
          cursor: pointer !important;
          padding: 3px 2px !important;
          margin: 0 !important;
          display: inline !important;
          font-weight: inherit !important;
          font-style: inherit !important;
          font-family: inherit !important;
          font-size: inherit !important;
          line-height: inherit !important;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        `;

        mark.addEventListener('click', (e) => {
          e.stopPropagation();
          console.log('🖱️ Highlight clicked:', highlight.id);
          setSelectedHighlightId(highlight.id);
          setNotesModalOpen(true);
        });

        mark.addEventListener('mouseenter', () => {
          mark.style.borderBottomWidth = '6px';
          mark.style.backgroundColor = isRed ? '#ffaaaa' : '#aaccff';
          mark.style.boxShadow = '0 3px 6px rgba(0,0,0,0.2)';
        });

        mark.addEventListener('mouseleave', () => {
          mark.style.borderBottomWidth = '4px';
          mark.style.backgroundColor = bgColor;
          mark.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        });

        try {
          range.surroundContents(mark);
          console.log('✨ Applied highlight to node');
        } catch (e) {
          console.error('❌ Failed to apply highlight:', e);
        }
      });
    });
  }, [highlights, sectionId, content, setSelectedHighlightId, setNotesModalOpen]);

  return (
    <div 
      ref={containerRef}
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
};