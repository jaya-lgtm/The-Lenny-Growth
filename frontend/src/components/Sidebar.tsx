import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  PanelLeftClose,
  Search,
  Sprout,
  MoreHorizontal,
  FolderOpen,
} from 'lucide-react';
import { Session, HealthStatus, Artifact } from '../types/api';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onRenameSession: (id: string, newTitle: string) => Promise<void>;
  onDeleteSession: (id: string) => Promise<void>;
  health: HealthStatus | null;
  isLoading: boolean;
  activeSessionArtifacts?: Artifact[];
  onOpenArtifact?: (artifact: Artifact) => void;
  isOpen: boolean;
  onToggle: () => void;
}

interface GroupedSessions {
  label: string;
  items: Session[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onRenameSession,
  onDeleteSession,
  health,
  isLoading,
  activeSessionArtifacts = [],
  onOpenArtifact,
  isOpen,
  onToggle,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

  const menuRef = useRef<HTMLDivElement>(null);

  // Close popup menu on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpenId(null);
      }
    };
    if (menuOpenId) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [menuOpenId]);

  const startEditing = (session: Session, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setMenuOpenId(null);
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveRename = async (id: string, e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!editTitle.trim()) {
      setEditingId(null);
      return;
    }
    await onRenameSession(id, editTitle.trim());
    setEditingId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const confirmDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setMenuOpenId(null);
    await onDeleteSession(id);
    setDeletingId(null);
  };

  // Filter sessions by search
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const query = searchQuery.toLowerCase();
    return sessions.filter((s) => s.title.toLowerCase().includes(query));
  }, [sessions, searchQuery]);

  // Group filtered sessions chronologically (Today, Yesterday, Previous 7 Days, Older)
  const groupedSessions = useMemo((): GroupedSessions[] => {
    const now = new Date();
    const todayMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayMidnight = todayMidnight - 24 * 60 * 60 * 1000;
    const sevenDaysAgo = todayMidnight - 7 * 24 * 60 * 60 * 1000;
    const thirtyDaysAgo = todayMidnight - 30 * 24 * 60 * 60 * 1000;

    const groups: Record<string, Session[]> = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      'Older': [],
    };

    filteredSessions.forEach((session) => {
      const updatedTime = new Date(session.updated_at || session.created_at).getTime();
      if (updatedTime >= todayMidnight) {
        groups['Today'].push(session);
      } else if (updatedTime >= yesterdayMidnight) {
        groups['Yesterday'].push(session);
      } else if (updatedTime >= sevenDaysAgo) {
        groups['Previous 7 Days'].push(session);
      } else if (updatedTime >= thirtyDaysAgo) {
        groups['Previous 30 Days'].push(session);
      } else {
        groups['Older'].push(session);
      }
    });

    return Object.entries(groups)
      .filter(([_, items]) => items.length > 0)
      .map(([label, items]) => ({ label, items }));
  }, [filteredSessions]);

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      <div
        className={`fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 md:hidden transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onToggle}
        aria-hidden="true"
      />

      {/* Sidebar Container with Smooth Width Transition */}
      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-50 md:z-auto
          h-full flex-shrink-0
          transition-all duration-300 ease-in-out
          ${isOpen ? 'translate-x-0 w-72 md:w-80' : '-translate-x-full md:translate-x-0 md:w-0'}
          overflow-hidden
        `}
      >
        {/* Inner wrapper */}
        <div className="w-72 md:w-80 h-full flex flex-col bg-[#F9FAFB] border-r border-slate-200/90 select-none flex-shrink-0">
          {/* Header & Controls */}
          <div className="p-4 pb-2.5 border-b border-slate-200/70 bg-white/80">
            {/* Brand Title & Close Button */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-xs flex-shrink-0">
                  <Sprout className="w-4.5 h-4.5" />
                </div>
                <div className="min-w-0">
                  <h1 className="font-bold text-sm text-slate-900 truncate tracking-tight">
                    The Lenny Growth
                  </h1>
                </div>
              </div>

              <button
                onClick={onToggle}
                title="Collapse sidebar (Ctrl+B)"
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors flex-shrink-0 cursor-pointer"
                aria-label="Collapse sidebar"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>

            {/* New Conversation Button */}
            <button
              onClick={onNewSession}
              disabled={isLoading}
              className="w-full flex items-center justify-between bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white py-2.5 px-3.5 rounded-xl text-sm font-semibold shadow-xs transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
            >
              <div className="flex items-center space-x-2">
                <Plus className="w-4 h-4 text-white" />
                <span>New chat</span>
              </div>
              <span className="text-[11px] text-blue-200 bg-blue-700/50 px-1.5 py-0.5 rounded font-mono">
                ⌘N
              </span>
            </button>

            {/* Clean Minimal Search */}
            <div className="relative mt-2.5">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search history..."
                className="w-full bg-slate-100/70 hover:bg-slate-100 focus:bg-white text-slate-800 placeholder-slate-400 text-xs md:text-sm pl-8 pr-7 py-2 rounded-xl border border-transparent focus:border-blue-400 focus:outline-none transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                  title="Clear"
                >
                  <X className="w-2.5 h-2.5" />
                </button>
              )}
            </div>
          </div>

          {/* Clean Streamlined History List */}
          <div className="flex-1 overflow-y-auto px-2 py-2 space-y-3">
            {sessions.length === 0 ? (
              <div className="text-center py-10 px-3 text-slate-400 text-xs">
                No chat history yet.
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="text-center py-8 px-3 text-slate-400 text-xs">
                No conversations found.
              </div>
            ) : (
              groupedSessions.map((group) => (
                <div key={group.label} className="space-y-1">
                  {/* Subtle Date Header */}
                  <div className="px-3 pt-3.5 pb-1.5 text-xs font-bold uppercase tracking-wider text-slate-500 select-none">
                    {group.label}
                  </div>

                  {/* Conversation Rows */}
                  {group.items.map((session) => {
                    const isActive = session.id === activeSessionId;
                    const isEditing = editingId === session.id;
                    const isDeleting = deletingId === session.id;
                    const isMenuOpen = menuOpenId === session.id;

                    return (
                      <div
                        key={session.id}
                        onClick={() => !isEditing && onSelectSession(session.id)}
                        className={`group relative flex items-center justify-between w-full min-h-[42px] py-2 px-3.5 rounded-xl cursor-pointer transition-colors duration-150 ${
                          isActive
                            ? 'bg-blue-100/70 text-blue-900 font-semibold shadow-2xs'
                            : 'text-slate-800 hover:text-slate-950 hover:bg-slate-200/70'
                        }`}
                      >
                        {/* Title or Inline Edit Form */}
                        {isEditing ? (
                          <form
                            onSubmit={(e) => handleSaveRename(session.id, e)}
                            className="flex items-center space-x-1 flex-1 min-w-0"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              autoFocus
                              className="bg-white text-slate-900 px-2.5 py-1.5 rounded-lg border border-blue-500 text-sm w-full focus:outline-none ring-2 ring-blue-100"
                            />
                            <button
                              type="submit"
                              className="p-1 text-blue-600 hover:text-blue-700 cursor-pointer"
                              title="Save"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={handleCancelRename}
                              className="p-1 text-slate-400 hover:text-slate-600 cursor-pointer"
                              title="Cancel"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </form>
                        ) : (
                          <>
                            <div className="flex items-center min-w-0 flex-1 mr-2">
                              {/* Active Blue Dot */}
                              {isActive && (
                                <span className="w-2.5 h-2.5 rounded-full bg-blue-600 mr-2.5 flex-shrink-0" />
                              )}
                              <span
                                className={`truncate text-[14.5px] leading-normal ${
                                  isActive ? 'font-semibold text-blue-900' : 'font-medium text-slate-800 group-hover:text-slate-950'
                                }`}
                              >
                                {session.title}
                              </span>
                            </div>

                            {/* Floating Action Menu Button (...) */}
                            <div
                              className={`flex items-center ${
                                isActive || isMenuOpen
                                  ? 'opacity-100'
                                  : 'opacity-0 group-hover:opacity-100'
                              } transition-opacity flex-shrink-0`}
                              onClick={(e) => e.stopPropagation()}
                            >
                              {isDeleting ? (
                                <div className="flex items-center space-x-1 bg-red-50 px-1.5 py-0.5 rounded border border-red-200 text-[10px] text-red-600">
                                  <span>Delete?</span>
                                  <button
                                    onClick={(e) => confirmDelete(session.id, e)}
                                    className="font-bold text-red-600 hover:text-red-700 p-0.5 cursor-pointer"
                                    title="Confirm"
                                  >
                                    <Check className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setDeletingId(null);
                                    }}
                                    className="text-slate-400 hover:text-slate-600 p-0.5 cursor-pointer"
                                    title="Cancel"
                                  >
                                    <X className="w-3 h-3" />
                                  </button>
                                </div>
                              ) : (
                                <div className="relative">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setMenuOpenId(isMenuOpen ? null : session.id);
                                    }}
                                    className={`p-1 rounded hover:bg-slate-300/60 transition-colors cursor-pointer ${
                                      isMenuOpen
                                        ? 'bg-slate-300/60 text-slate-800'
                                        : 'text-slate-400 hover:text-slate-700'
                                    }`}
                                    title="Options"
                                  >
                                    <MoreHorizontal className="w-3.5 h-3.5" />
                                  </button>

                                  {/* Sleek Popover Dropdown Menu */}
                                  {isMenuOpen && (
                                    <div
                                      ref={menuRef}
                                      className="absolute right-0 top-6 z-50 w-32 bg-white rounded-lg shadow-lg border border-slate-200/90 py-1 text-xs text-slate-700 animate-in fade-in zoom-in-95 duration-100"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <button
                                        onClick={() => startEditing(session)}
                                        className="w-full text-left px-3 py-1.5 hover:bg-slate-50 flex items-center space-x-2 text-slate-700 cursor-pointer"
                                      >
                                        <Edit2 className="w-3 h-3 text-slate-400" />
                                        <span>Rename</span>
                                      </button>
                                      <button
                                        onClick={() => {
                                          setMenuOpenId(null);
                                          setDeletingId(session.id);
                                        }}
                                        className="w-full text-left px-3 py-1.5 hover:bg-red-50 flex items-center space-x-2 text-red-600 cursor-pointer"
                                      >
                                        <Trash2 className="w-3 h-3 text-red-500" />
                                        <span>Delete</span>
                                      </button>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))
            )}

            {/* Active Session Artifacts Section (Compact & Sleek) */}
            {activeSessionArtifacts.length > 0 && (
              <div className="pt-2 border-t border-slate-200/80 mt-2 space-y-1">
                <div className="px-2 pt-1 pb-0.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
                  <FolderOpen className="w-3 h-3 text-blue-500" />
                  <span>Session Artifacts</span>
                </div>
                {activeSessionArtifacts.map((art) => (
                  <div
                    key={art.id}
                    onClick={() => onOpenArtifact && onOpenArtifact(art)}
                    className="w-full h-8 px-2.5 rounded-lg cursor-pointer flex items-center justify-between text-xs text-slate-700 hover:text-blue-700 hover:bg-blue-50/60 transition-colors"
                  >
                    <span className="truncate text-xs font-medium mr-1">{art.title}</span>
                    <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-slate-100 text-slate-500 border border-slate-200/60 flex-shrink-0">
                      {art.content_format}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer User Workspace Status */}
          <div className="p-3 border-t border-slate-200/80 bg-white flex items-center justify-between flex-shrink-0">
            <div className="flex items-center space-x-2 min-w-0">
              <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 border border-blue-200 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                JK
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-800 truncate leading-tight">
                  Jayakrishna
                </div>
                <div className="flex items-center space-x-1.5 text-[10px] text-slate-400">
                  <span
                    className={`inline-block w-1.5 h-1.5 rounded-full ${
                      health?.status === 'ok' ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                  />
                  <span>{health?.database === 'connected' ? 'PostgreSQL 16' : 'PostgreSQL'}</span>
                </div>
              </div>
            </div>

            <span className="px-2 py-0.5 rounded-full bg-blue-50 text-[10px] text-blue-600 font-semibold border border-blue-200/60 flex-shrink-0">
              M3 Skills
            </span>
          </div>
        </div>
      </aside>
    </>
  );
};
