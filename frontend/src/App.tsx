import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ArtifactViewer } from './components/ArtifactViewer';
import { ErrorBanner } from './components/ErrorBanner';
import { api, ApiClientError } from './api/client';
import { Session, Message, HealthStatus, ApiError, Artifact, SourceCitation } from './types/api';

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionArtifacts, setSessionArtifacts] = useState<Record<string, Artifact>>({});
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [activeViewerCitations, setActiveViewerCitations] = useState<SourceCitation[]>([]);

  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('mock');

  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [isSendingMessage, setIsSendingMessage] = useState<boolean>(false);

  // Sidebar initially closed by default so the user gets the full-screen right-side view on startup
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  useEffect(() => {
    localStorage.setItem('lenny_sidebar_open', String(isSidebarOpen));
  }, [isSidebarOpen]);

  // Global keyboard shortcut (Ctrl+B or Cmd+B) to toggle sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setIsSidebarOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleApiError = (err: unknown, defaultMessage: string) => {
    console.error('API Error:', err);
    if (err instanceof ApiClientError) {
      setError({
        code: err.code,
        message: err.message,
        details: err.details,
      });
    } else if (err instanceof Error) {
      setError({
        code: 'CLIENT_ERROR',
        message: err.message,
      });
    } else {
      setError({
        code: 'UNKNOWN_ERROR',
        message: defaultMessage,
      });
    }
  };

  // 1. Initial Health Check, Config & Session Loading
  const loadInitialData = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      // Check health
      try {
        const healthData = await api.checkHealth();
        setHealth(healthData);
      } catch (hErr) {
        console.warn('Health check reported degraded status:', hErr);
      }

      // Check config & determine default provider
      try {
        const configData = await api.getConfig();
        const ollamaAvail = configData.available_providers?.find(
          (p: any) => p.provider === 'ollama' && p.is_available
        );
        if (configData.active_llm_provider === 'ollama' && !ollamaAvail) {
          // If ollama configured but unavailable, default to mock for responsive experience
          setSelectedProvider('mock');
        } else {
          setSelectedProvider(configData.active_llm_provider || 'mock');
        }
      } catch (cErr) {
        console.warn('Failed to load runtime config:', cErr);
      }

      // Load sessions
      const sessionList = await api.getSessions();

      // Check if the top session is already a clean session with 0 messages
      let startingSession: Session | null = null;
      if (sessionList.length > 0 && sessionList[0].title === 'New Conversation') {
        const firstMsgs = await api.getMessages(sessionList[0].id).catch(() => []);
        if (firstMsgs.length === 0) {
          startingSession = sessionList[0];
          setSessions(sessionList);
        }
      }

      // If no clean session exists at the top, create a fresh one so the user ALWAYS lands on the welcome screen
      if (!startingSession) {
        startingSession = await api.createSession('New Conversation');
        setSessions([startingSession, ...sessionList]);
      }

      setActiveSessionId(startingSession.id);
    } catch (err) {
      handleApiError(err, 'Failed to connect to backend service.');
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // 2. Fetch Messages and Artifacts when Active Session changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      setSessionArtifacts({});
      return;
    }

    let isMounted = true;
    const fetchSessionData = async () => {
      setIsLoadingMessages(true);
      try {
        const [msgs, artifacts] = await Promise.all([
          api.getMessages(activeSessionId),
          api.listSessionArtifacts(activeSessionId).catch(() => []),
        ]);

        if (isMounted) {
          setMessages(msgs);
          const artMap: Record<string, Artifact> = {};
          (artifacts || []).forEach((art) => {
            artMap[art.id] = art;
          });
          setSessionArtifacts(artMap);
        }
      } catch (err) {
        if (isMounted) {
          handleApiError(err, 'Failed to load conversation history.');
        }
      } finally {
        if (isMounted) {
          setIsLoadingMessages(false);
        }
      }
    };

    fetchSessionData();
    return () => {
      isMounted = false;
    };
  }, [activeSessionId]);

  // 3. Create New Session
  const handleNewSession = async () => {
    setError(null);
    try {
      const newSession = await api.createSession('New Conversation');
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
      setSessionArtifacts({});
      setSelectedArtifact(null);
    } catch (err) {
      handleApiError(err, 'Failed to create new session.');
    }
  };

  // 4. Rename Session
  const handleRenameSession = async (sessionId: string, newTitle: string) => {
    setError(null);
    try {
      const updated = await api.renameSession(sessionId, newTitle);
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s))
      );
    } catch (err) {
      handleApiError(err, 'Failed to rename session.');
    }
  };

  // 5. Delete Session (Cascades to its artifacts only, preserves other data)
  const handleDeleteSession = async (sessionId: string) => {
    setError(null);
    try {
      await api.deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);

      if (activeSessionId === sessionId) {
        setSelectedArtifact(null);
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          const fresh = await api.createSession('New Conversation');
          setSessions([fresh]);
          setActiveSessionId(fresh.id);
        }
      }
    } catch (err) {
      handleApiError(err, 'Failed to delete session.');
    }
  };

  const generateClientSessionTitle = (text: string): string => {
    if (!text || !text.trim()) return 'New Conversation';
    let clean = text.trim().replace(/^[#>\s*`-]+/, '');
    const prefixes = [
      /^can you please\s+/i,
      /^can you\s+/i,
      /^could you\s+/i,
      /^please\s+/i,
      /^tell me about\s+/i,
      /^what did\s+/i,
      /^what are (the |some )?/i,
      /^what is (the |an? )?/i,
      /^how (do|can|should|would) (i|we|you)\s+/i,
      /^how to\s+/i,
      /^explain\s+/i,
    ];
    for (const prefix of prefixes) {
      if (prefix.test(clean)) {
        clean = clean.replace(prefix, '');
        break;
      }
    }
    clean = clean.trim().replace(/^[ .?!,;:"']+|[ .?!,;:"']+$/g, '');
    if (clean.length > 0) {
      clean = clean.charAt(0).toUpperCase() + clean.slice(1);
    }
    if (clean.length > 40) {
      const spaceIdx = clean.slice(0, 40).lastIndexOf(' ');
      clean = (spaceIdx > 20 ? clean.slice(0, spaceIdx) : clean.slice(0, 40)) + '...';
    }
    return clean || 'New Conversation';
  };

  // 6. Send Message with Growth Skill Mode Support
  const handleSendMessage = async (content: string, mode: string = 'auto') => {
    if (!activeSessionId) return;
    setError(null);
    setIsSendingMessage(true);

    // Optimistically title session if it currently has default "New Conversation" title
    const currentSession = sessions.find((s) => s.id === activeSessionId);
    if (currentSession && (currentSession.title === 'New Conversation' || !currentSession.title)) {
      const quickTitle = generateClientSessionTitle(content);
      setSessions((prev) =>
        prev.map((s) => (s.id === activeSessionId ? { ...s, title: quickTitle } : s))
      );
    }

    // Optimistically show user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: activeSessionId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const chatRes = await api.sendChat(activeSessionId, content, selectedProvider, mode);

      if (chatRes.artifact) {
        setSessionArtifacts((prev) => ({
          ...prev,
          [chatRes.artifact!.id]: chatRes.artifact!,
        }));
      }

      // Refresh messages from server to get persisted user & assistant records with sources & artifact_id
      const msgs = await api.getMessages(activeSessionId);
      setMessages(msgs);

      // Re-fetch sessions so updated_at sorting bubbles this session to top
      const refreshedSessions = await api.getSessions();
      setSessions(refreshedSessions);
    } catch (err) {
      handleApiError(err, 'Failed to generate assistant response.');
      try {
        const msgs = await api.getMessages(activeSessionId);
        setMessages(msgs);
      } catch {}
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleOpenArtifact = (artifact: Artifact, citations: SourceCitation[] = []) => {
    setSelectedArtifact(artifact);
    setActiveViewerCitations(citations);
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;
  const activeSessionArtifactList = Object.values(sessionArtifacts);

  return (
    <div className="flex h-screen w-screen bg-[#F8FAFC] overflow-hidden text-slate-900 antialiased font-sans">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewSession={handleNewSession}
        onRenameSession={handleRenameSession}
        onDeleteSession={handleDeleteSession}
        health={health}
        isLoading={isLoadingSessions}
        activeSessionArtifacts={activeSessionArtifactList}
        onOpenArtifact={(art) => handleOpenArtifact(art)}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen((prev) => !prev)}
      />

      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
        <ErrorBanner error={error} onDismiss={() => setError(null)} />
        <ChatArea
          session={activeSession}
          messages={messages}
          isLoadingMessages={isLoadingMessages}
          isSendingMessage={isSendingMessage}
          onSendMessage={handleSendMessage}
          selectedProvider={selectedProvider}
          onSelectProvider={setSelectedProvider}
          onOpenArtifact={handleOpenArtifact}
          sessionArtifacts={sessionArtifacts}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
          onNewSession={handleNewSession}
        />

        {/* Slide-over Artifact Viewer */}
        {selectedArtifact && (
          <ArtifactViewer
            artifact={selectedArtifact}
            onClose={() => setSelectedArtifact(null)}
            citations={activeViewerCitations}
          />
        )}
      </div>
    </div>
  );
};

export default App;
