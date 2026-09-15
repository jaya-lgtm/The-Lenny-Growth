export interface Session {
  id: string;
  title: string;
  user_metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  provider?: string | null;
  message_metadata?: Record<string, any> | null;
  created_at: string;
}

export interface SourceCitation {
  title: string;
  source_type: string;
  source_url?: string | null;
  guest?: string | null;
  relative_path?: string | null;
  publish_date?: string | null;
  chunk_index: number;
  excerpt: string;
  similarity: number;
  metadata?: Record<string, any>;
}

export type ArtifactType =
  | 'growth_action_plan'
  | 'ship30_essay'
  | 'framework'
  | 'checklist'
  | 'experiment_plan'
  | 'strategy_doc'
  | 'html_css_component'
  | 'grounded_qa'
  | 'auto';

export interface Artifact {
  id: string;
  session_id: string;
  message_id?: string | null;
  artifact_type: string;
  content_format: 'markdown' | 'html' | 'text' | 'json';
  schema_version: string;
  title: string;
  content: string;
  artifact_metadata?: Record<string, any> | null;
  created_at: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  provider?: string;
  mode?: string;
}

export interface ChatResponse {
  session_id: string;
  message: Message;
  artifact?: Artifact | null;
}

export interface ProviderStatus {
  provider: string;
  model: string;
  is_available: boolean;
  status_message: string;
}

export interface ConfigStatus {
  app_name: string;
  environment: string;
  active_llm_provider: string;
  active_llm_model: string;
  active_embedding_provider: string;
  active_embedding_model: string;
  retrieval_top_k: number;
  available_providers: ProviderStatus[];
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface HealthStatus {
  status: string;
  service: string;
  environment: string;
  database: string;
}
