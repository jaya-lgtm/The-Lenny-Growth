import React, { useState, useEffect } from 'react';
import {
  X,
  Copy,
  Check,
  Download,
  FileText,
  Code,
  BookOpen,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { Artifact, SourceCitation } from '../types/api';

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClose: () => void;
  citations?: SourceCitation[];
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClose,
  citations = [],
}) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'code' | 'citations'>('preview');
  const [copied, setCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!artifact) return null;

  const wordCount =
    artifact.artifact_metadata?.word_count ||
    artifact.content.trim().split(/\s+/).filter(Boolean).length;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard', err);
    }
  };

  const handleDownload = () => {
    const ext = artifact.content_format === 'html' ? 'html' : 'md';
    const mime = artifact.content_format === 'html' ? 'text/html' : 'text/markdown';
    const blob = new Blob([artifact.content], { type: `${mime};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const safeTitle = artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    link.href = url;
    link.download = `${safeTitle}.${ext}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Human-readable type label
  const typeLabelMap: Record<string, string> = {
    growth_action_plan: 'Growth Action Plan',
    ship30_essay: 'Ship 30 Essay',
    framework: 'Growth Framework',
    checklist: 'Audit Checklist',
    experiment_plan: 'Experiment Plan',
    strategy_doc: 'Strategy Document',
    html_css_component: 'Interactive HTML/CSS Component',
    grounded_qa: 'Grounded Analysis',
  };

  const typeLabel = typeLabelMap[artifact.artifact_type] || artifact.artifact_type;

  // Lightweight Markdown Renderer that securely structures headings, bold, bullet points, tables, and alerts
  const renderMarkdownFormatted = (content: string) => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let listItems: string[] = [];

    const flushList = (keyPrefix: string) => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`${keyPrefix}-list`} className="list-disc list-inside space-y-1.5 my-3 text-slate-700">
            {listItems.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {renderInlineStyles(item)}
              </li>
            ))}
          </ul>
        );
        listItems = [];
      }
    };

    const renderInlineStyles = (text: string): React.ReactNode => {
      // Bold **text**
      const parts = text.split(/(\*\*.*?\*\*)/g);
      return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={i} className="text-slate-900 font-semibold">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      if (trimmed.startsWith('# ')) {
        flushList(`line-${index}`);
        elements.push(
          <h1 key={index} className="text-xl md:text-2xl font-bold text-slate-900 mt-6 mb-3 border-b border-slate-200 pb-2">
            {trimmed.slice(2)}
          </h1>
        );
      } else if (trimmed.startsWith('## ')) {
        flushList(`line-${index}`);
        elements.push(
          <h2 key={index} className="text-lg md:text-xl font-bold text-blue-700 mt-5 mb-2.5">
            {trimmed.slice(3)}
          </h2>
        );
      } else if (trimmed.startsWith('### ')) {
        flushList(`line-${index}`);
        elements.push(
          <h3 key={index} className="text-sm md:text-base font-semibold text-slate-800 mt-4 mb-2">
            {trimmed.slice(4)}
          </h3>
        );
      } else if (trimmed.startsWith('> [!NOTE]') || trimmed.startsWith('> [!TIP]') || trimmed.startsWith('> [!IMPORTANT]')) {
        flushList(`line-${index}`);
        elements.push(
          <div key={index} className="p-3.5 my-3 rounded-xl bg-blue-50/80 border-l-4 border-blue-600 text-xs text-blue-900 font-medium">
            {trimmed.replace(/^>\s*/, '')}
          </div>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        listItems.push(trimmed.slice(2));
      } else if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        // Simple table row
        flushList(`line-${index}`);
        const cells = trimmed.split('|').map((c) => c.trim()).filter(Boolean);
        if (!trimmed.includes('---')) {
          elements.push(
            <div key={index} className="grid grid-cols-3 gap-2 p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono my-1 text-slate-700">
              {cells.map((cell, cIdx) => (
                <span key={cIdx} className="truncate">{cell}</span>
              ))}
            </div>
          );
        }
      } else if (trimmed === '') {
        flushList(`line-${index}`);
      } else {
        flushList(`line-${index}`);
        elements.push(
          <p key={index} className="text-xs md:text-sm text-slate-700 leading-relaxed mb-3">
            {renderInlineStyles(trimmed)}
          </p>
        );
      }
    });

    flushList('final');
    return elements;
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs transition-opacity duration-200">
      {/* Slide-over Container */}
      <div
        className={`flex flex-col bg-white border-l border-slate-200 shadow-2xl h-full transition-all duration-300 ${
          isFullscreen ? 'w-full' : 'w-full max-w-2xl lg:max-w-3xl'
        }`}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between flex-shrink-0">
          <div className="min-w-0 flex-1 mr-4">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
                {typeLabel}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 border border-slate-200 uppercase font-mono">
                {artifact.content_format} • {artifact.schema_version}
              </span>
              <span className="text-[11px] text-slate-500 hidden sm:inline">
                {wordCount} words
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-900 mt-1 truncate tracking-tight">
              {artifact.title}
            </h2>
          </div>

          <div className="flex items-center space-x-2">
            {/* Fullscreen Toggle */}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1 px-2.5 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium border border-slate-200 transition-all active:scale-95 cursor-pointer shadow-xs"
              title="Copy Content"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-600 font-semibold">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-500" />
                  <span>Copy</span>
                </>
              )}
            </button>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium shadow-sm transition-all active:scale-95 cursor-pointer"
              title="Download Artifact"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors ml-1 cursor-pointer"
              title="Close (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-slate-200 bg-slate-50/60 flex items-center justify-between text-xs">
          <div className="flex space-x-5">
            <button
              onClick={() => setActiveTab('preview')}
              className={`py-2.5 font-medium border-b-2 transition-colors flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'preview'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Formatted View</span>
            </button>

            <button
              onClick={() => setActiveTab('code')}
              className={`py-2.5 font-medium border-b-2 transition-colors flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'code'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Raw Source</span>
            </button>

            <button
              onClick={() => setActiveTab('citations')}
              className={`py-2.5 font-medium border-b-2 transition-colors flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'citations'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Evidence & Citations ({citations.length})</span>
            </button>
          </div>

          {artifact.content_format === 'html' && (
            <div className="flex items-center space-x-1.5 text-[10.5px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
              <ShieldCheck className="w-3 h-3" />
              <span>Sandboxed Iframe</span>
            </div>
          )}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-[#FAFCFF]">
          {activeTab === 'preview' && (
            <div className="h-full">
              {artifact.content_format === 'html' ? (
                /* Secure Sandboxed Iframe Rendering */
                <div className="h-full min-h-[500px] rounded-xl overflow-hidden border border-slate-200 bg-white shadow-xs flex flex-col">
                  <div className="px-3.5 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-mono">Sandboxed Rendering: allow-scripts (no same-origin)</span>
                    <span className="text-blue-600 font-medium">Safe Sandbox</span>
                  </div>
                  <iframe
                    title={artifact.title}
                    srcDoc={artifact.content}
                    sandbox="allow-scripts"
                    className="w-full flex-1 border-none bg-white"
                    data-testid="sandboxed-artifact-iframe"
                  />
                </div>
              ) : (
                /* Markdown Formatted Document */
                <article className="max-w-none text-slate-800 leading-relaxed font-sans select-text">
                  {renderMarkdownFormatted(artifact.content)}
                </article>
              )}
            </div>
          )}

          {activeTab === 'code' && (
            <div className="rounded-xl overflow-hidden border border-slate-800 bg-[#0F172A] shadow-xs">
              <div className="px-4 py-2 bg-[#1E293B] border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span className="font-mono text-[11px]">
                  {artifact.content_format === 'html' ? 'HTML / CSS Component Source' : 'Markdown Source'}
                </span>
                <span className="text-[11px] font-mono">{artifact.content.length} bytes</span>
              </div>
              <pre className="p-4 text-xs font-mono text-slate-200 overflow-x-auto whitespace-pre leading-relaxed select-text">
                <code>{artifact.content}</code>
              </pre>
            </div>
          )}

          {activeTab === 'citations' && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-100 text-xs text-blue-900 flex items-start space-x-2.5">
                <Sparkles className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <p>
                  This artifact was synthesized from real Lenny Podcast transcripts indexed in PostgreSQL with pgvector embeddings.
                  All citations trace back to real episode chunks.
                </p>
              </div>

              {citations.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate-400">
                  No explicit citations attached to this artifact record.
                </div>
              ) : (
                citations.map((cite, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5 text-xs shadow-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 truncate">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 border border-blue-100 text-blue-700">
                          {cite.guest ? `🎙️ ${cite.guest}` : '🎙️ Podcast Episode'}
                        </span>
                        <span className="font-semibold text-slate-900 truncate">{cite.title}</span>
                      </div>
                      {cite.source_url && (
                        <a
                          href={cite.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 flex items-center space-x-1 text-[11px] font-medium"
                        >
                          <span>YouTube</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <blockquote className="italic text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100 text-[11px] leading-relaxed">
                      "{cite.excerpt}"
                    </blockquote>
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span>{cite.relative_path || `Chunk ${cite.chunk_index}`}</span>
                      {cite.similarity > 0 && <span className="text-blue-600 font-medium">Relevance: {(cite.similarity * 100).toFixed(1)}%</span>}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-2.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-[11px] text-slate-500">
          <span>Immutable ID: <span className="font-mono text-slate-600">{artifact.id.slice(0, 8)}...</span></span>
          <span>Created: {new Date(artifact.created_at).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};
