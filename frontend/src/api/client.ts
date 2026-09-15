import { Session, Message, MessageRole, ApiError, HealthStatus } from '../types/api';

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(status: number, error: ApiError) {
    super(error.message || 'An API error occurred');
    this.name = 'ApiClientError';
    this.status = status;
    this.code = error.code || 'UNKNOWN_ERROR';
    this.details = error.details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (data && data.error) {
      throw new ApiClientError(response.status, data.error);
    }
    throw new ApiClientError(response.status, {
      code: `HTTP_${response.status}`,
      message: response.statusText || 'Request failed',
      details: data,
    });
  }

  return data as T;
}

export const api = {
  checkHealth: async (): Promise<HealthStatus> => {
    return request<HealthStatus>('/api/health');
  },

  createSession: async (title?: string): Promise<Session> => {
    return request<Session>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(title ? { title } : {}),
    });
  },

  getSessions: async (): Promise<Session[]> => {
    return request<Session[]>('/api/sessions');
  },

  getSession: async (sessionId: string): Promise<Session> => {
    return request<Session>(`/api/sessions/${sessionId}`);
  },

  renameSession: async (sessionId: string, title: string): Promise<Session> => {
    return request<Session>(`/api/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    });
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await request<void>(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  getMessages: async (sessionId: string): Promise<Message[]> => {
    return request<Message[]>(`/api/sessions/${sessionId}/messages`);
  },

  createMessage: async (
    sessionId: string,
    content: string,
    role: MessageRole = 'user'
  ): Promise<Message> => {
    return request<Message>(`/api/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ role, content }),
    });
  },

  sendChat: async (
    sessionId: string,
    message: string,
    provider?: string,
    mode?: string
  ): Promise<{ session_id: string; message: Message; artifact?: any }> => {
    return request<{ session_id: string; message: Message; artifact?: any }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message, provider, mode }),
    });
  },

  getArtifact: async (artifactId: string) => {
    return request<any>(`/api/artifacts/${artifactId}`);
  },

  listSessionArtifacts: async (sessionId: string) => {
    return request<any[]>(`/api/artifacts/session/${sessionId}`);
  },

  getConfig: async () => {
    return request<any>('/api/config');
  },
};

