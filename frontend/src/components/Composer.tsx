import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, ChevronDown, Check, X } from 'lucide-react';

interface ComposerProps {
  onSendMessage: (content: string, mode?: string) => Promise<void>;
  isLoading: boolean;
  disabled: boolean;
  autoFocus?: boolean;
}

interface ModeOption {
  id: string;
  label: string;
  icon: string;
  badge?: string;
  description: string;
}

interface ModeCategory {
  name: string;
  modes: ModeOption[];
}

const MODE_CATEGORIES: ModeCategory[] = [
  {
    name: 'General & Conversational',
    modes: [
      {
        id: 'auto',
        label: 'Auto Detect',
        icon: '✨',
        description: 'Intelligently detects query intent and routes to the best skill or framework',
      },
      {
        id: 'grounded_qa',
        label: 'Grounded Q&A Only',
        icon: '💬',
        description: 'Conversational answers strictly citing Lenny transcripts (no artifact)',
      },
    ],
  },
  {
    name: 'Long-Form Content',
    modes: [
      {
        id: 'ship30_essay',
        label: 'Ship 30 for 30 Essay',
        icon: '📝',
        badge: '1k–1.5k words',
        description: 'Structured essay with hook, 3 acts, key takeaways, and transcript evidence',
      },
    ],
  },
  {
    name: 'Frameworks & Strategy',
    modes: [
      {
        id: 'growth_action_plan',
        label: 'Growth Action Plan',
        icon: '📊',
        description: 'Prioritized 30-60-90 day tactical execution roadmap with metrics and milestones',
      },
      {
        id: 'framework',
        label: 'Growth Framework',
        icon: '🎯',
        description: 'Structured mental models, compounding growth loops, and scoring tables',
      },
      {
        id: 'checklist',
        label: 'Audit Checklist',
        icon: '✅',
        description: 'Diagnostic PM/Growth audit with actionable checkpoints and evaluation criteria',
      },
      {
        id: 'experiment_plan',
        label: 'Experiment Plan',
        icon: '🧪',
        description: 'Hypothesis statement, sample size, ICE prioritization, and test design',
      },
      {
        id: 'strategy_doc',
        label: 'Strategy Document',
        icon: '🧭',
        description: 'Executive strategy memo detailing problem, strategic bets, moats, and trade-offs',
      },
    ],
  },
  {
    name: 'Interactive UI & Code',
    modes: [
      {
        id: 'html_css_component',
        label: 'HTML/CSS Component',
        icon: '💻',
        badge: 'Sandboxed',
        description: 'Live interactive calculators, dashboards, and sandboxed interactive UI widgets',
      },
    ],
  },
];

const ALL_MODES = MODE_CATEGORIES.flatMap((c) => c.modes);

export const Composer: React.FC<ComposerProps> = ({
  onSendMessage,
  isLoading,
  disabled,
  autoFocus = false,
}) => {
  const [content, setContent] = useState('');
  const [selectedMode, setSelectedMode] = useState<string>('auto');
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const modeButtonRef = useRef<HTMLDivElement>(null);

  const activeMode = ALL_MODES.find((m) => m.id === selectedMode) || ALL_MODES[0];

  // Auto-focus textarea when requested
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  // Auto-expand textarea up to max height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 180)}px`;
    }
  }, [content]);

  // Handle outside click to close mode popover
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        modeButtonRef.current &&
        !modeButtonRef.current.contains(event.target as Node)
      ) {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  // Close menu on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMenuOpen) {
        setIsMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMenuOpen]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || isLoading || disabled) return;

    setContent('');
    setIsMenuOpen(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    await onSendMessage(trimmed, selectedMode);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSubmit = content.trim().length > 0 && !isLoading && !disabled;

  return (
    <div className="p-4 bg-white/90 backdrop-blur-md border-t border-slate-200">
      <div className="max-w-3xl mx-auto">
        <form
          onSubmit={handleSubmit}
          className="relative rounded-2xl bg-white border border-slate-200 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-100 transition-all shadow-xs"
        >
          {/* Main Textarea */}
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled
                ? 'Select or create a conversation first...'
                : selectedMode === 'auto'
                ? 'Ask a growth question or request an artifact (Action Plan, Ship 30 essay, Checklist)...'
                : `Generate ${activeMode.label} grounded in Lenny transcripts...`
            }
            disabled={disabled || isLoading}
            rows={1}
            className="w-full bg-transparent px-4 pt-3.5 pb-2 text-xs md:text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none max-h-44 disabled:opacity-50 disabled:cursor-not-allowed"
          />

          {/* Integrated Action Toolbar */}
          <div className="flex items-center justify-between px-3 pb-2.5 pt-1.5 border-t border-slate-100">
            {/* Left: Mode Dropdown Selector */}
            <div ref={modeButtonRef} className="relative">
              {selectedMode === 'auto' ? (
                <button
                  type="button"
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  disabled={disabled || isLoading}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-all shadow-2xs active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Choose output format or skill mode"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Auto Detect</span>
                  <ChevronDown
                    className={`w-3 h-3 text-slate-400 transition-transform duration-150 ${
                      isMenuOpen ? 'rotate-180' : ''
                    }`}
                  />
                </button>
              ) : (
                <div className="flex items-center space-x-1 bg-blue-50 border border-blue-200 text-blue-700 px-2.5 py-1 rounded-xl text-xs font-semibold shadow-2xs">
                  <button
                    type="button"
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    disabled={disabled || isLoading}
                    className="flex items-center space-x-1.5 hover:text-blue-800"
                    title="Change output mode"
                  >
                    <span>{activeMode.icon}</span>
                    <span className="font-semibold">{activeMode.label}</span>
                    <ChevronDown
                      className={`w-3 h-3 text-blue-600 transition-transform duration-150 ${
                        isMenuOpen ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedMode('auto');
                    }}
                    className="p-0.5 ml-0.5 hover:bg-blue-100 rounded text-blue-600 hover:text-blue-800 transition-colors"
                    title="Reset to Auto Detect"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}

              {/* Popover Dropdown Menu */}
              {isMenuOpen && (
                <div
                  ref={menuRef}
                  className="absolute bottom-full left-0 mb-2 w-80 sm:w-96 max-h-[420px] overflow-y-auto bg-white border border-slate-200 rounded-2xl shadow-xl z-50 p-2 space-y-2.5 divide-y divide-slate-100 animate-in fade-in slide-in-from-bottom-2 duration-150"
                >
                  {/* Popover Header */}
                  <div className="px-2 pt-1 pb-1 flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                        <span>Output Format & Skill Mode</span>
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Choose how the assistant structures the response
                      </p>
                    </div>
                    {selectedMode !== 'auto' && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedMode('auto');
                          setIsMenuOpen(false);
                        }}
                        className="text-[10px] text-blue-600 hover:text-blue-700 font-semibold px-2 py-0.5 rounded bg-blue-50 hover:bg-blue-100 transition-colors"
                      >
                        Reset to Auto
                      </button>
                    )}
                  </div>

                  {/* Categorized Options */}
                  {MODE_CATEGORIES.map((category) => (
                    <div key={category.name} className="pt-2">
                      <span className="px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                        {category.name}
                      </span>
                      <div className="space-y-0.5">
                        {category.modes.map((mode) => {
                          const isSelected = selectedMode === mode.id;
                          return (
                            <button
                              key={mode.id}
                              type="button"
                              onClick={() => {
                                setSelectedMode(mode.id);
                                setIsMenuOpen(false);
                                textareaRef.current?.focus();
                              }}
                              className={`w-full text-left px-2.5 py-2 rounded-xl flex items-start space-x-2.5 transition-colors ${
                                isSelected
                                  ? 'bg-blue-50 border border-blue-200 text-slate-900 font-medium'
                                  : 'hover:bg-slate-50 text-slate-700 border border-transparent'
                              }`}
                            >
                              <span className="text-base flex-shrink-0 mt-0.5">{mode.icon}</span>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-1.5">
                                  <span
                                    className={`text-xs ${
                                      isSelected
                                        ? 'text-blue-700 font-bold'
                                        : 'text-slate-800 font-medium'
                                    }`}
                                  >
                                    {mode.label}
                                  </span>
                                  {mode.badge && (
                                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                                      {mode.badge}
                                    </span>
                                  )}
                                </div>
                                <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5 leading-tight">
                                  {mode.description}
                                </p>
                              </div>
                              {isSelected && (
                                <Check className="w-4 h-4 text-blue-600 flex-shrink-0 mt-1" />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right: Keyboard Hint & Send Button */}
            <div className="flex items-center space-x-2.5">
              <div className="hidden sm:flex items-center text-[11px] text-slate-400 space-x-1 font-medium">
                <kbd className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200 font-mono text-[10px]">
                  Shift
                </kbd>
                <span>+</span>
                <kbd className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200 font-mono text-[10px]">
                  Enter
                </kbd>
                <span className="text-slate-400 ml-0.5">newline</span>
              </div>

              <button
                type="submit"
                disabled={!canSubmit}
                className={`w-9 h-9 rounded-xl transition-all flex items-center justify-center ${
                  canSubmit
                    ? 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-sm shadow-blue-500/25 active:scale-95'
                    : 'bg-blue-100/70 text-blue-300 cursor-not-allowed'
                }`}
                title="Send message (Enter)"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
