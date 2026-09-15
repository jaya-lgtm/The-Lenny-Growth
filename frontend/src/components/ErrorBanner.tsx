import React from 'react';
import { AlertCircle, X } from 'lucide-react';
import { ApiError } from '../types/api';

interface ErrorBannerProps {
  error: ApiError | null;
  onDismiss: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, onDismiss }) => {
  if (!error) return null;

  return (
    <div className="bg-red-950/80 border border-red-800/80 text-red-200 px-4 py-3 rounded-lg flex items-start justify-between shadow-lg backdrop-blur-sm mx-4 mt-3 mb-1 animate-in fade-in duration-200">
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
        <div>
          <div className="font-semibold text-sm tracking-wide text-red-300">
            {error.code || 'ERROR'}
          </div>
          <div className="text-xs text-red-200/90 mt-0.5">{error.message}</div>
          {error.details && (
            <pre className="text-[11px] text-red-300/80 mt-1.5 p-1.5 bg-red-950/60 rounded border border-red-900/50 max-h-24 overflow-auto">
              {typeof error.details === 'string'
                ? error.details
                : JSON.stringify(error.details, null, 2)}
            </pre>
          )}
        </div>
      </div>
      <button
        onClick={onDismiss}
        className="text-red-400 hover:text-red-200 p-1 rounded-md transition-colors"
        title="Dismiss error"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
