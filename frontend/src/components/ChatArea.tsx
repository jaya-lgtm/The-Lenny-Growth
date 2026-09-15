import React, { useState, useEffect, useRef } from 'react';
import {
  Sprout,
  Terminal,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  TrendingUp,
  Sun,
  PanelLeft,
  SquarePen,
} from 'lucide-react';
import { Session, Message, Artifact, SourceCitation } from '../types/api';
import { Composer } from './Composer';
import { ArtifactCard } from './ArtifactCard';
import { EmptyState } from './EmptyState';
import { api } from '../api/client';

interface ChatAreaProps {
  session: Session | null;
  messages: Message[];
  isLoadingMessages: boolean;
  isSendingMessage: boolean;
  onSendMessage: (content: string, mode?: string) => Promise<void>;
  selectedProvider?: string;
  onSelectProvider?: (provider: string) => void;
  onOpenArtifact: (artifact: Artifact, citations?: SourceCitation[]) => void;
  sessionArtifacts: Record<string, Artifact>;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  onNewSession?: () => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  session,
  messages,
  isLoadingMessages,
  isSendingMessage,
  onSendMessage,
  selectedProvider = 'mock',
  onSelectProvider,
  onOpenArtifact,
  sessionArtifacts,
  isSidebarOpen = true,
  onToggleSidebar,
  onNewSession,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const [fetchedArtifacts, setFetchedArtifacts] = useState<Record<string, Artifact>>({});
  const [isChatBoxVisible, setIsChatBoxVisible] = useState<boolean>(false);

  // Keep chatbox hidden on new/empty conversation, visible on active conversation
  useEffect(() => {
    if (messages.length > 0) {
      setIsChatBoxVisible(true);
    } else {
      setIsChatBoxVisible(false);
    }
  }, [session?.id, messages.length]);

  const handleStartNewChat = () => {
    setIsChatBoxVisible(true);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSendingMessage]);

  const toggleSource = (msgId: string) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const formatMessageTime = (dateString: string) => {
    try {
      const d = new Date(dateString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  // If a message has an artifact_id not in sessionArtifacts or fetchedArtifacts, lazily fetch it
  useEffect(() => {
    messages.forEach((msg) => {
      const artId = msg.message_metadata?.artifact_id;
      if (artId && !sessionArtifacts[artId] && !fetchedArtifacts[artId]) {
        api.getArtifact(artId)
          .then((art) => {
            setFetchedArtifacts((prev) => ({ ...prev, [artId]: art }));
          })
          .catch((err) => {
            console.warn(`Could not load artifact ${artId}:`, err);
          });
      }
    });
  }, [messages, sessionArtifacts, fetchedArtifacts]);

  // Clean Markdown Renderer for assistant responses
  const renderFormattedMessage = (content: string) => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let listItems: string[] = [];

    const flushList = (keyPrefix: string) => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`${keyPrefix}-list`} className="list-disc list-inside space-y-1.5 my-2.5 text-slate-700">
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
          <h1 key={index} className="text-base md:text-lg font-bold text-slate-900 mt-4 mb-2 border-b border-slate-100 pb-1.5">
            {trimmed.slice(2)}
          </h1>
        );
      } else if (trimmed.startsWith('## ')) {
        flushList(`line-${index}`);
        elements.push(
          <h2 key={index} className="text-sm md:text-base font-bold text-blue-700 mt-3.5 mb-1.5">
            {trimmed.slice(3)}
          </h2>
        );
      } else if (trimmed.startsWith('### ')) {
        flushList(`line-${index}`);
        elements.push(
          <h3 key={index} className="text-xs md:text-sm font-bold text-slate-900 mt-3 mb-1">
            {trimmed.slice(4)}
          </h3>
        );
      } else if (trimmed.startsWith('> [!NOTE]') || trimmed.startsWith('> [!TIP]') || trimmed.startsWith('> [!IMPORTANT]')) {
        flushList(`line-${index}`);
        elements.push(
          <div key={index} className="p-3 my-2.5 rounded-xl bg-blue-50/80 border-l-3 border-blue-600 text-xs text-blue-900 font-medium">
            {trimmed.replace(/^>\s*/, '')}
          </div>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        listItems.push(trimmed.slice(2));
      } else if (trimmed === '') {
        flushList(`line-${index}`);
      } else {
        flushList(`line-${index}`);
        elements.push(
          <p key={index} className="text-xs md:text-sm text-slate-800 leading-relaxed mb-2.5">
            {renderInlineStyles(trimmed)}
          </p>
        );
      }
    });

    flushList('final');
    return elements;
  };

  if (!session) {
    return (
      <main className="flex-1 flex flex-col bg-white h-full items-center justify-center p-6 text-center relative">
        {onToggleSidebar && (
          <div className={`absolute top-4 left-4 flex items-center space-x-1.5 ${isSidebarOpen ? 'md:hidden' : 'flex'}`}>
            <button
              onClick={onToggleSidebar}
              title="Open sidebar (Ctrl+B)"
              className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center space-x-1.5 text-xs shadow-2xs cursor-pointer"
              aria-label="Open sidebar"
            >
              <PanelLeft className="w-4 h-4 text-blue-600" />
              <span className="font-semibold">Open History</span>
            </button>
            {onNewSession && (
              <button
                onClick={onNewSession}
                title="New conversation"
                className="p-2 rounded-xl text-slate-600 hover:text-blue-600 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center space-x-1.5 text-xs shadow-2xs cursor-pointer"
              >
                <SquarePen className="w-4 h-4" />
                <span className="font-semibold">New Chat</span>
              </button>
            )}
          </div>
        )}
        <div className="max-w-md animate-fade-in-up">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-xs">
            <Sprout className="w-7 h-7" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 mb-2">No Active Session</h2>
          <p className="text-xs text-slate-500 mb-4">
            Select a conversation from the sidebar or start a new one to begin.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col bg-white h-full overflow-hidden">
      {/* Session Header */}
      <header className="px-6 py-3.5 border-b border-slate-200 bg-white flex items-center justify-between flex-shrink-0 shadow-2xs">
        <div className="flex items-center space-x-3 min-w-0 mr-4">
          {/* Open Sidebar Toggle Button & Quick New Chat Button */}
          {onToggleSidebar && (
            <div className={`flex items-center space-x-2 flex-shrink-0 ${isSidebarOpen ? 'md:hidden' : 'flex'}`}>
              <button
                onClick={onToggleSidebar}
                title="Open chat history (Ctrl+B)"
                className="px-2.5 py-1.5 rounded-xl text-slate-700 hover:text-slate-900 bg-slate-100/80 hover:bg-slate-200/80 border border-slate-200/80 transition-all flex items-center space-x-1.5 text-xs font-semibold shadow-2xs cursor-pointer"
                aria-label="Open chat history"
              >
                <PanelLeft className="w-3.5 h-3.5 text-blue-600" />
                <span className="hidden sm:inline">History</span>
              </button>

              {onNewSession && (
                <button
                  onClick={onNewSession}
                  title="New conversation"
                  className="px-2.5 py-1.5 rounded-xl text-slate-700 hover:text-blue-600 bg-slate-100/80 hover:bg-slate-200/80 border border-slate-200/80 transition-all flex items-center space-x-1.5 text-xs font-semibold shadow-2xs cursor-pointer"
                  aria-label="New conversation"
                >
                  <SquarePen className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">New Chat</span>
                </button>
              )}
            </div>
          )}

          <div className="min-w-0">
            <h2 className="text-base font-bold text-slate-900 truncate tracking-tight">
              {session.title}
            </h2>
            <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5 font-medium">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>Session ID: {session.id.slice(0, 8)}...</span>
              <span>•</span>
              <span>Created {new Date(session.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 flex-shrink-0">
          {/* Provider Selector */}
          <div className="flex items-center space-x-1.5 bg-slate-100/90 border border-slate-200 rounded-full px-3 py-1 text-xs text-slate-600 font-medium">
            <span className="text-slate-400 text-[10px] uppercase font-bold">LLM:</span>
            <select
              value={selectedProvider}
              onChange={(e) => onSelectProvider && onSelectProvider(e.target.value)}
              className="bg-transparent text-blue-600 font-semibold text-[11px] focus:outline-none cursor-pointer"
            >
              <option value="mock">Mock (Offline)</option>
              <option value="ollama">Ollama (Local)</option>
              <option value="openai">OpenAI (Cloud)</option>
              <option value="anthropic">Anthropic (Cloud)</option>
            </select>
          </div>

          {/* Growth Skills Pill */}
          <span className="hidden sm:flex text-[11px] px-3 py-1 rounded-full bg-blue-50 border border-blue-200/80 text-blue-600 font-semibold items-center space-x-1.5 shadow-2xs">
            <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
            <span>Growth Skills</span>
          </span>

          {/* Message Count */}
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-500 font-medium">
            {messages.length} {messages.length === 1 ? 'msg' : 'msgs'}
          </span>

          {/* Sun / Theme Icon */}
          <button
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            title="Theme: Light"
          >
            <Sun className="w-4 h-4" />
          </button>

          {/* User Profile Avatar */}
          <div
            className="w-7 h-7 rounded-full bg-blue-100 border border-blue-200 text-blue-700 font-bold text-xs flex items-center justify-center shadow-2xs select-none"
            title="Jayakrishna"
          >
            JK
          </div>
        </div>
      </header>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6 bg-white">
        {isLoadingMessages ? (
          <div className="flex flex-col items-center justify-center h-full space-y-3">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-slate-500 font-medium">Loading conversation history...</span>
          </div>
        ) : messages.length === 0 ? (
          <EmptyState
            onSelectPrompt={onSendMessage}
            onStartNewChat={handleStartNewChat}
            isChatBoxVisible={isChatBoxVisible}
          />
        ) : (
          <div className="max-w-3xl mx-auto w-full space-y-6">
            {messages.map((message) => {
              const isUser = message.role === 'user';
              const isSystem = message.role === 'system';
              const sources: SourceCitation[] = message.message_metadata?.sources || [];
              const isSourcesOpen = !!expandedSources[message.id];
              const artifactId = message.message_metadata?.artifact_id;
              const artifact = artifactId ? (sessionArtifacts[artifactId] || fetchedArtifacts[artifactId]) : null;

              if (isSystem) {
                return (
                  <div key={message.id} className="flex justify-center my-2 animate-fade-in-up">
                    <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-[11px] text-slate-600 shadow-2xs font-medium">
                      <Terminal className="w-3.5 h-3.5 text-blue-600" />
                      <span>{message.content}</span>
                    </div>
                  </div>
                );
              }

              return (
                <div
                  key={message.id}
                  className={`animate-fade-in-up ${isUser ? 'flex justify-end' : 'flex justify-start'}`}
                >
                  {isUser ? (
                    <div className="max-w-xl ml-auto">
                      <div className="bg-slate-100/90 text-slate-900 border border-slate-200/80 rounded-2xl rounded-tr-xs px-4 py-3 text-xs md:text-sm leading-relaxed shadow-2xs select-text">
                        {message.content}
                      </div>
                      <div className="mt-1 text-right text-[10px] text-slate-400">
                        {formatMessageTime(message.created_at)}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start space-x-3 w-full">
                      <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white text-xs flex-shrink-0 shadow-xs mt-1">
                        <Sprout className="w-4 h-4" />
                      </div>

                      <div className="flex-1 bg-white border border-slate-200/90 rounded-2xl rounded-tl-xs p-4 md:p-5 shadow-xs text-xs md:text-sm text-slate-800 space-y-3">
                        <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-[11px] text-slate-400">
                          <span className="font-bold text-slate-900">The Lenny Assistant</span>
                          <span>{formatMessageTime(message.created_at)}</span>
                        </div>

                        {/* Clean Structured Content */}
                        <div className="select-text">
                          {renderFormattedMessage(message.content)}
                        </div>

                        {/* Embedded Artifact Card */}
                        {artifact && (
                          <div className="pt-2">
                            <ArtifactCard
                              artifact={artifact}
                              onOpenViewer={(art) => onOpenArtifact(art, sources)}
                            />
                          </div>
                        )}

                        {/* Grounded Source Citations (Collapsible) */}
                        {sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-slate-100">
                            <button
                              onClick={() => toggleSource(message.id)}
                              className="flex items-center justify-between w-full text-left py-1 text-xs font-semibold text-blue-600 hover:text-blue-700 transition-colors cursor-pointer"
                            >
                              <div className="flex items-center space-x-1.5">
                                <BookOpen className="w-3.5 h-3.5" />
                                <span>Supporting Evidence & Citations ({sources.length})</span>
                              </div>
                              {isSourcesOpen ? (
                                <ChevronUp className="w-3.5 h-3.5" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5" />
                              )}
                            </button>

                            {isSourcesOpen && (
                              <div className="mt-2.5 space-y-2.5 animate-fade-in-up">
                                {sources.map((src, sIdx) => (
                                  <div
                                    key={sIdx}
                                    className="rounded-xl p-3 bg-slate-50/80 border border-slate-200 text-xs space-y-1.5"
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center space-x-1.5 truncate">
                                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 border border-blue-200/80 text-blue-700">
                                          {src.guest ? `🎙️ ${src.guest}` : '🎙️ Podcast'}
                                        </span>
                                        <span className="font-bold text-slate-800 truncate">{src.title}</span>
                                      </div>
                                      {src.source_url && (
                                        <a
                                          href={src.source_url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          title="Watch Episode on YouTube"
                                          className="text-slate-400 hover:text-blue-600 flex items-center ml-2 flex-shrink-0 transition-colors"
                                        >
                                          <ExternalLink className="w-3.5 h-3.5" />
                                        </a>
                                      )}
                                    </div>
                                    <p className="text-slate-600 italic bg-white p-2.5 rounded-lg border border-slate-200/80 text-[11px] leading-relaxed shadow-2xs">
                                      "{src.excerpt}"
                                    </p>
                                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                                      <span className="truncate max-w-[70%]">
                                        {src.relative_path ? `📁 ${src.relative_path}` : `Chunk ${src.chunk_index}`}
                                        {src.publish_date ? ` • ${src.publish_date}` : ''}
                                      </span>
                                      {src.similarity > 0 && (
                                        <span className="text-blue-600 font-semibold">Match: {(src.similarity * 100).toFixed(1)}%</span>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Sending message indicator */}
        {isSendingMessage && (
          <div className="max-w-3xl mx-auto w-full flex items-start space-x-3 mr-auto animate-fade-in-up">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white text-xs flex-shrink-0 shadow-xs mt-1">
              <Sprout className="w-4 h-4 animate-spin" />
            </div>
            <div className="rounded-2xl rounded-tl-xs px-4 py-3 bg-white border border-slate-200 text-xs text-slate-600 flex items-center space-x-2.5 shadow-xs">
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
              <span className="font-medium text-slate-700">Synthesizing growth knowledge & generating artifact...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Input Container with Smooth Slide-Up Transition */}
      <div
        className={`transition-all duration-500 ease-out transform ${
          isChatBoxVisible || messages.length > 0
            ? 'translate-y-0 opacity-100 max-h-72 pointer-events-auto'
            : 'translate-y-12 opacity-0 max-h-0 pointer-events-none overflow-hidden'
        }`}
      >
        <Composer
          onSendMessage={onSendMessage}
          isLoading={isSendingMessage}
          disabled={isLoadingMessages}
          autoFocus={isChatBoxVisible}
        />
      </div>
    </main>
  );
};
