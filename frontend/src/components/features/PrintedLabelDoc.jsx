import React from 'react';
import './PrintedLabel.css';

const PrintedLabelDoc = ({ data }) => {
  if (!data) {
    return (
      <div className="label-container">
        <div className="no-data-message">
          <p>No drug label data available</p>
        </div>
      </div>
    );
  }

  const { drugName, version, id, sections } = data;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="label-container">
      {/* Print Button - Only visible on screen */}
      <div className="print-toolbar no-print">
        <button onClick={handlePrint} className="print-button">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
          </svg>
          Print / Save PDF
        </button>
      </div>

      {/* The Paper */}
      <div className="paper">
        {/* Formal Header */}
        <header className="label-header">
          <div className="header-top">
            <strong>HIGHLIGHTS OF PRESCRIBING INFORMATION</strong>
          </div>
          <div className="header-subtitle">
            These highlights do not include all the information needed to use{' '}
            <strong>{drugName}</strong> safely and effectively. See full prescribing
            information for <strong>{drugName}</strong>.
          </div>
          <div className="drug-title">
            <h1>{drugName}</h1>
          </div>
          {version && (
            <div className="header-metadata">
              <span>Initial U.S. Approval: {version}</span>
            </div>
          )}
          {id && (
            <div className="header-metadata">
              <span>Reference ID: {id}</span>
            </div>
          )}
        </header>

        <hr className="section-divider" />

        {/* Main Content - 2 Column Layout */}
        <div className="label-body">
          {sections && sections.length > 0 ? (
            sections.map((section, index) => (
              <section key={section.id || index} className="label-section">
                <h2 className="section-title">{section.title}</h2>
                <div
                  className="section-content"
                  dangerouslySetInnerHTML={{ __html: section.content_html }}
                />
              </section>
            ))
          ) : (
            <p>No sections available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PrintedLabelDoc;
