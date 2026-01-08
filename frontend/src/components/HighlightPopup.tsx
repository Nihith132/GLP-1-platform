import React from 'react';
import { Highlighter, X } from 'lucide-react';

interface HighlightPopupProps {
  position: { top: number; left: number };
  onSelectColor: (color: 'red' | 'blue') => void;
  onCancel: () => void;
}

export const HighlightPopup: React.FC<HighlightPopupProps> = ({
  position,
  onSelectColor,
  onCancel,
}) => {
  return (
    <div
      className="fixed z-50 bg-white rounded-lg shadow-xl border-2 border-gray-200 p-3"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        transform: 'translate(-50%, -100%) translateY(-10px)',
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <Highlighter className="w-4 h-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">Highlight Color</span>
        <button
          onClick={onCancel}
          className="ml-auto p-1 hover:bg-gray-100 rounded transition-colors"
          title="Cancel"
        >
          <X className="w-3 h-3 text-gray-500" />
        </button>
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={() => onSelectColor('red')}
          className="flex items-center gap-2 px-3 py-2 border-2 border-red-500 rounded-lg hover:bg-red-50 transition-colors group"
          title="Red highlight"
        >
          <div className="w-6 h-6 border-2 border-red-500 rounded bg-red-50 group-hover:bg-red-100" />
          <span className="text-sm font-medium text-red-700">Red</span>
        </button>
        
        <button
          onClick={() => onSelectColor('blue')}
          className="flex items-center gap-2 px-3 py-2 border-2 border-blue-500 rounded-lg hover:bg-blue-50 transition-colors group"
          title="Blue highlight"
        >
          <div className="w-6 h-6 border-2 border-blue-500 rounded bg-blue-50 group-hover:bg-blue-100" />
          <span className="text-sm font-medium text-blue-700">Blue</span>
        </button>
      </div>
    </div>
  );
};
