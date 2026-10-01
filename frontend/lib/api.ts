/**
 * Recall Backend Client API.
 * Interacts with Django REST endpoints:
 * - POST /api/ask/ (Phase 4 Groq synthesis)
 * - POST /api/search/ (Phase 2 hybrid retrieval)
 * - GET/POST /api/memories/ (Phase 1 ingest & list)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

function getToken(): string | null {
  return typeof window === 'undefined' ? null : localStorage.getItem('recall_token');
}

function authHeaders(headers: Record<string, string> = {}): Record<string, string> {
  const token = getToken();
  return token ? { ...headers, Authorization: `Token ${token}` } : headers;
}

export interface AuthResponse {
  token: string;
  user: { id: number; username: string; email: string };
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.non_field_errors?.[0] || 'Login failed.');
  localStorage.setItem('recall_token', data.token);
  localStorage.setItem('recall_user', JSON.stringify(data.user));
  return data;
}

export async function register(username: string, email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.username?.[0] || data.password?.[0] || data.detail || 'Registration failed.';
    throw new Error(message);
  }
  localStorage.setItem('recall_token', data.token);
  localStorage.setItem('recall_user', JSON.stringify(data.user));
  return data;
}

export function logout(): void {
  localStorage.removeItem('recall_token');
  localStorage.removeItem('recall_user');
}

export interface Citation {
  id: string;
  title: string;
  source_type: 'text' | 'webpage' | 'screenshot' | 'pdf';
  source_url?: string;
  media_url?: string;
  raw_content?: string;
  created_at?: string;
  metadata?: Record<string, any>;
  score: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  has_relevant_memories: boolean;
  top_score: number;
  threshold: number;
  citations: Citation[];
  model: string;
  retrieved_count: number;
}

export interface MemoryItem {
  id: string;
  source_type: 'text' | 'webpage' | 'screenshot' | 'pdf';
  title: string;
  raw_content: string;
  source_url?: string;
  created_at: string;
  chunk_index: number;
  parent_id?: string;
  metadata?: Record<string, any>;
  media_url?: string;
  has_embedding: boolean;
  vector_score?: number;
  keyword_score?: number;
  hybrid_score?: number;
}

export interface SearchResponse {
  query: string;
  mode: string;
  alpha: number;
  threshold: number;
  count: number;
  results: MemoryItem[];
}

export function getMediaUrl(rawUrl?: string): string | null {
  if (!rawUrl) return null;
  return rawUrl.startsWith('http') ? rawUrl : `${API_BASE}${rawUrl}`;
}

export interface MemoriesListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: MemoryItem[];
}

export async function askRecall(
  question: string,
  options?: { top_k?: number; threshold?: number; alpha?: number; mode?: string }
): Promise<AskResponse> {
  const res = await fetch(API_BASE + '/api/ask/', {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      question,
      top_k: options?.top_k ?? 5,
      threshold: options?.threshold ?? 0.45,
      alpha: options?.alpha ?? 0.6,
      mode: options?.mode ?? 'hybrid',
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || ('Error ' + res.status + ': Failed to synthesize answer'));
  }
  return res.json();
}

export async function searchMemories(
  query: string,
  options?: { top_k?: number; alpha?: number; mode?: string; source_type?: string; threshold?: number }
): Promise<SearchResponse> {
  const res = await fetch(API_BASE + '/api/search/', {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      query,
      top_k: options?.top_k ?? 10,
      alpha: options?.alpha ?? 0.6,
      mode: options?.mode ?? 'hybrid',
      source_type: options?.source_type || undefined,
      threshold: options?.threshold ?? 0.45,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || ('Error ' + res.status + ': Search failed'));
  }
  return res.json();
}

export async function getMemories(
  pageOrOptions: number | { page?: number; source_type?: string; q?: string } = 1,
  sourceType?: string
): Promise<MemoriesListResponse> {
  let page = 1;
  let source = sourceType;
  let q: string | undefined = undefined;

  if (typeof pageOrOptions === 'object' && pageOrOptions !== null) {
    page = pageOrOptions.page ?? 1;
    source = pageOrOptions.source_type;
    q = pageOrOptions.q;
  } else if (typeof pageOrOptions === 'number') {
    page = pageOrOptions;
  }

  let url = API_BASE + '/api/memories/?page=' + page;
  if (source && source !== 'all') {
    url += '&source_type=' + encodeURIComponent(source);
  }
  if (q && q.trim()) {
    url += '&q=' + encodeURIComponent(q.trim());
  }

  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    throw new Error('Failed to load memories: ' + res.statusText);
  }
  return res.json();
}

export async function createMemory(payload: {
  title?: string;
  raw_content?: string;
  source_type?: string;
  source_url?: string;
  file?: File;
}): Promise<any> {
  let body: any;
  let headers: Record<string, string> = {};

  if (payload.file) {
    const formData = new FormData();
    if (payload.title) formData.append('title', payload.title);
    if (payload.source_type) formData.append('source_type', payload.source_type);
    if (payload.source_url) formData.append('source_url', payload.source_url);
    formData.append('file', payload.file);
    body = formData;
  } else {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify({
      title: payload.title,
      raw_content: payload.raw_content,
      source_type: payload.source_type || 'text',
      source_url: payload.source_url,
    });
  }

  const res = await fetch(API_BASE + '/api/memories/', {
    method: 'POST',
    headers: authHeaders(headers),
    body,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(JSON.stringify(err) || 'Failed to save memory');
  }
  return res.json();
}

export async function deleteMemory(id: string): Promise<void> {
  const res = await fetch(API_BASE + '/api/memories/' + id + '/', {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok && res.status !== 204) {
    throw new Error('Failed to delete memory ' + id);
  }
}

