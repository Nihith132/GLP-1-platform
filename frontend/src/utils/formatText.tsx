/**
 * Utility to format AI-generated text with proper markdown-style formatting
 */

import React from 'react';

export const formatAIText = (text: string): JSX.Element => {
  if (!text) return <></>;

  // Clean up the text - remove extra whitespace and normalize line breaks
  const cleanedText = text.trim().replace(/\r\n/g, '\n');

  // Split by double newlines for paragraphs
  const paragraphs = cleanedText.split(/\n\n+/);

  return (
    <>
      {paragraphs.map((para, pIdx) => {
        // Skip empty paragraphs
        if (!para.trim()) return null;

        // Check if it's a list (starts with - or • or *)
        if (para.trim().match(/^[-•*]\s/m)) {
          const items = para.split('\n').filter(line => line.trim());
          return (
            <ul key={pIdx} className="space-y-2 my-3 pl-1">
              {items.map((item, iIdx) => (
                <li key={iIdx} className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span className="flex-1 text-gray-700">{formatInlineMarkdown(item.replace(/^[-•*]\s*/, ''))}</span>
                </li>
              ))}
            </ul>
          );
        }

        // Check if it's a numbered list
        if (para.trim().match(/^\d+\.\s/m)) {
          const items = para.split('\n').filter(line => line.trim());
          return (
            <ol key={pIdx} className="space-y-2 my-3 pl-1">
              {items.map((item, iIdx) => (
                <li key={iIdx} className="flex items-start gap-2">
                  <span className="text-primary font-bold mt-0.5">{iIdx + 1}.</span>
                  <span className="flex-1 text-gray-700">{formatInlineMarkdown(item.replace(/^\d+\.\s*/, ''))}</span>
                </li>
              ))}
            </ol>
          );
        }

        // Check if it's a heading
        if (para.trim().startsWith('###')) {
          return (
            <h4 key={pIdx} className="font-bold text-base text-gray-900 mt-5 mb-3">
              {para.replace(/^###\s*/, '').trim()}
            </h4>
          );
        }
        if (para.trim().startsWith('##')) {
          return (
            <h3 key={pIdx} className="font-bold text-lg text-gray-900 mt-6 mb-4">
              {para.replace(/^##\s*/, '').trim()}
            </h3>
          );
        }

        // Format inline markdown for regular paragraphs
        const formatted = formatInlineMarkdown(para);

        // Regular paragraph
        return (
          <p key={pIdx} className="text-gray-700 leading-relaxed my-3">
            {formatted}
          </p>
        );
      })}
    </>
  );
};

const formatInlineMarkdown = (text: string): (string | JSX.Element)[] => {
  const parts: (string | JSX.Element)[] = [];
  let currentIndex = 0;
  let keyCounter = 0;

  // Match **bold**, *italic*, `code`
  const patterns = [
    { regex: /\*\*(.+?)\*\*/g, component: (match: string, key: number) => <strong key={key} className="font-semibold">{match}</strong> },
    { regex: /\*(.+?)\*/g, component: (match: string, key: number) => <em key={key} className="italic">{match}</em> },
    { regex: /`(.+?)`/g, component: (match: string, key: number) => <code key={key} className="px-1.5 py-0.5 bg-gray-100 rounded text-sm font-mono">{match}</code> },
  ];

  const allMatches: Array<{ start: number; end: number; element: JSX.Element }> = [];

  patterns.forEach(({ regex, component }) => {
    let match;
    const regexCopy = new RegExp(regex.source, regex.flags);
    while ((match = regexCopy.exec(text)) !== null) {
      allMatches.push({
        start: match.index,
        end: match.index + match[0].length,
        element: component(match[1], keyCounter++),
      });
    }
  });

  // Sort by start position
  allMatches.sort((a, b) => a.start - b.start);

  // Build the result, avoiding overlaps
  let lastEnd = 0;
  allMatches.forEach((match) => {
    if (match.start >= lastEnd) {
      if (match.start > lastEnd) {
        parts.push(text.substring(lastEnd, match.start));
      }
      parts.push(match.element);
      lastEnd = match.end;
    }
  });

  if (lastEnd < text.length) {
    parts.push(text.substring(lastEnd));
  }

  return parts.length > 0 ? parts : [text];
};

export default formatAIText;
