import type { Highlight, Note } from '../types';

export interface ExportData {
  drugName: string;
  exportDate: string;
  highlights: Highlight[];
  notes: Note[];
}

/**
 * Export notes and highlights as JSON
 */
export function exportAsJSON(data: ExportData): void {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${data.drugName}-analysis-${Date.now()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export notes and highlights as formatted text
 */
export function exportAsText(data: ExportData): void {
  let textContent = `# Analysis Report: ${data.drugName}\n`;
  textContent += `Export Date: ${data.exportDate}\n`;
  textContent += `\n${'='.repeat(80)}\n\n`;

  // Cited Notes Section
  const citedNotes = data.notes.filter(n => n.type === 'cited' && n.highlightId);
  if (citedNotes.length > 0) {
    textContent += `## Cited Notes (${citedNotes.length})\n\n`;
    
    citedNotes.forEach((note, index) => {
      const highlight = data.highlights.find(h => h.id === note.highlightId);
      if (highlight) {
        textContent += `### Citation ${index + 1} [${highlight.color.toUpperCase()}]\n`;
        textContent += `**Highlighted Text:**\n"${highlight.text}"\n\n`;
        textContent += `**Note:**\n${note.content}\n\n`;
        textContent += `Created: ${new Date(note.createdAt).toLocaleString()}\n`;
        textContent += `${'-'.repeat(80)}\n\n`;
      }
    });
  }

  // Uncited Notes Section
  const uncitedNotes = data.notes.filter(n => n.type === 'uncited' || !n.highlightId);
  if (uncitedNotes.length > 0) {
    textContent += `## Uncited Notes (${uncitedNotes.length})\n\n`;
    
    uncitedNotes.forEach((note, index) => {
      textContent += `### Note ${index + 1}\n`;
      textContent += `${note.content}\n\n`;
      textContent += `Created: ${new Date(note.createdAt).toLocaleString()}\n`;
      textContent += `${'-'.repeat(80)}\n\n`;
    });
  }

  // Summary
  textContent += `\n## Summary\n`;
  textContent += `Total Highlights: ${data.highlights.length}\n`;
  textContent += `- Red: ${data.highlights.filter(h => h.color === 'red').length}\n`;
  textContent += `- Blue: ${data.highlights.filter(h => h.color === 'blue').length}\n`;
  textContent += `Total Notes: ${data.notes.length}\n`;

  const blob = new Blob([textContent], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${data.drugName}-analysis-${Date.now()}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export notes and highlights as Markdown
 */
export function exportAsMarkdown(data: ExportData): void {
  let mdContent = `# Analysis Report: ${data.drugName}\n\n`;
  mdContent += `**Export Date:** ${data.exportDate}\n\n`;
  mdContent += `---\n\n`;

  // Cited Notes Section
  const citedNotes = data.notes.filter(n => n.type === 'cited' && n.highlightId);
  if (citedNotes.length > 0) {
    mdContent += `## 📌 Cited Notes (${citedNotes.length})\n\n`;
    
    citedNotes.forEach((note, index) => {
      const highlight = data.highlights.find(h => h.id === note.highlightId);
      if (highlight) {
        const colorEmoji = highlight.color === 'red' ? '🔴' : '🔵';
        mdContent += `### ${colorEmoji} Citation ${index + 1}\n\n`;
        mdContent += `> **Highlighted Text:**\n> \n> "${highlight.text}"\n\n`;
        mdContent += `**Your Note:**\n\n${note.content}\n\n`;
        mdContent += `*Created: ${new Date(note.createdAt).toLocaleString()}*\n\n`;
        mdContent += `---\n\n`;
      }
    });
  }

  // Uncited Notes Section
  const uncitedNotes = data.notes.filter(n => n.type === 'uncited' || !n.highlightId);
  if (uncitedNotes.length > 0) {
    mdContent += `## 📝 Uncited Notes (${uncitedNotes.length})\n\n`;
    
    uncitedNotes.forEach((note, index) => {
      mdContent += `### Note ${index + 1}\n\n`;
      mdContent += `${note.content}\n\n`;
      mdContent += `*Created: ${new Date(note.createdAt).toLocaleString()}*\n\n`;
      mdContent += `---\n\n`;
    });
  }

  // Summary Table
  mdContent += `## 📊 Summary\n\n`;
  mdContent += `| Metric | Count |\n`;
  mdContent += `|--------|-------|\n`;
  mdContent += `| Total Highlights | ${data.highlights.length} |\n`;
  mdContent += `| 🔴 Red Highlights | ${data.highlights.filter(h => h.color === 'red').length} |\n`;
  mdContent += `| 🔵 Blue Highlights | ${data.highlights.filter(h => h.color === 'blue').length} |\n`;
  mdContent += `| Total Notes | ${data.notes.length} |\n`;
  mdContent += `| Cited Notes | ${citedNotes.length} |\n`;
  mdContent += `| Uncited Notes | ${uncitedNotes.length} |\n`;

  const blob = new Blob([mdContent], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${data.drugName}-analysis-${Date.now()}.md`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy all notes to clipboard
 */
export async function copyToClipboard(data: ExportData): Promise<void> {
  let textContent = `Analysis Report: ${data.drugName}\n`;
  textContent += `Export Date: ${data.exportDate}\n\n`;

  const citedNotes = data.notes.filter(n => n.type === 'cited' && n.highlightId);
  citedNotes.forEach((note) => {
    const highlight = data.highlights.find(h => h.id === note.highlightId);
    if (highlight) {
      textContent += `[${highlight.color.toUpperCase()}] "${highlight.text}"\n`;
      textContent += `Note: ${note.content}\n\n`;
    }
  });

  const uncitedNotes = data.notes.filter(n => n.type === 'uncited' || !n.highlightId);
  if (uncitedNotes.length > 0) {
    textContent += `\nUncited Notes:\n`;
    uncitedNotes.forEach((note) => {
      textContent += `- ${note.content}\n`;
    });
  }

  await navigator.clipboard.writeText(textContent);
}
