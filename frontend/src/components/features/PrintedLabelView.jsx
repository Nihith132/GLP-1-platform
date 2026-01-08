import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { drugService } from '@/services/drugService';
import { Loading } from '../ui/Loading';
import { Button } from '../ui/Button';
import { ArrowLeft } from 'lucide-react';
import PrintedLabelDoc from '../features/PrintedLabelDoc';

/**
 * Adapter component that fetches drug data and transforms it
 * into the format expected by PrintedLabelDoc
 */
const PrintedLabelView = () => {
  const { drugId } = useParams();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [labelData, setLabelData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (drugId) {
      loadDrugData(parseInt(drugId));
    }
  }, [drugId]);

  const loadDrugData = async (id) => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch drug data with sections
      const drugData = await drugService.getDrugById(id);

      // Transform data to PrintedLabelDoc format
      const transformedData = {
        drugName: drugData.name || 'Unknown Drug',
        version: drugData.last_updated 
          ? new Date(drugData.last_updated).toLocaleDateString('en-US', { month: '2-digit', year: 'numeric' })
          : null,
        id: drugData.set_id || drugData.id?.toString(),
        sections: drugData.sections?.map((section, index) => ({
          id: section.loinc_code || `section-${index}`,
          title: `${section.order || index + 1} ${section.title}`,
          content_html: formatContentAsHTML(section.content, section.ner_entities)
        })) || []
      };

      setLabelData(transformedData);
    } catch (err) {
      console.error('Error loading drug data:', err);
      setError('Failed to load drug label. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Convert plain text content to HTML with NER entity highlighting
   */
  const formatContentAsHTML = (content, nerEntities = []) => {
    if (!content) return '<p>No content available</p>';

    // Convert plain text to HTML paragraphs
    let html = content
      .split('\n\n')
      .filter(para => para.trim())
      .map(para => `<p>${para.trim()}</p>`)
      .join('\n');

    // Optional: Add NER highlighting if needed
    // This is a simplified version - you can enhance it to highlight entities
    if (nerEntities && nerEntities.length > 0) {
      // Sort entities by start position (descending) to avoid offset issues
      const sortedEntities = [...nerEntities].sort((a, b) => b.start_char - a.start_char);

      sortedEntities.forEach(entity => {
        const { text, label, start_char, end_char } = entity;
        
        // Color mapping for entity types
        const colorMap = {
          'drug_name': '#3b82f6',
          'condition': '#f59e0b',
          'strength': '#10b981',
          'side_effect': '#ef4444',
          'contraindication': '#dc2626'
        };

        const color = colorMap[label] || '#6b7280';
        
        // Insert highlighting (simplified - you may need more sophisticated logic)
        const before = content.substring(0, start_char);
        const highlighted = content.substring(start_char, end_char);
        const after = content.substring(end_char);
        
        // Only highlight if the text matches
        if (highlighted === text) {
          html = html.replace(
            text,
            `<mark style="background-color: ${color}20; color: ${color}; font-weight: 600; padding: 2px 4px; border-radius: 2px;">${text}</mark>`
          );
        }
      });
    }

    return html;
  };

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100vh',
        backgroundColor: '#525659'
      }}>
        <Loading size="lg" text="Loading drug label..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100vh',
        backgroundColor: '#525659',
        color: 'white',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <p style={{ fontSize: '18px' }}>{error}</p>
        <Button onClick={() => navigate('/dashboard')}>
          <ArrowLeft style={{ width: '16px', height: '16px', marginRight: '8px' }} />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return <PrintedLabelDoc data={labelData} />;
};

export default PrintedLabelView;
