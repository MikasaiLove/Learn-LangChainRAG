import client from './client';

export interface Session {
  id: string;
  user_id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  tokens?: { input: number; output: number; total: number };
  created_at?: string;
}

export interface Citation {
  index: number;
  doc_id: string;
  doc_name: string;
  chunk_text: string;
  score: number;
}

export async function getSessions(page = 1, size = 20): Promise<{ items: Session[]; total: number }> {
  const res = await client.get('/api/chat/sessions', { params: { page, size } });
  return res.data;
}

export async function createSession(title?: string): Promise<Session> {
  const res = await client.post('/api/chat/sessions', title ? { title } : {});
  return res.data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await client.delete(`/api/chat/sessions/${sessionId}`);
}

export async function getMessages(sessionId: string, page = 1, size = 50): Promise<{ items: Message[]; total: number }> {
  const res = await client.get(`/api/chat/sessions/${sessionId}/messages`, { params: { page, size } });
  return res.data;
}

export function sendMessage(sessionId: string, content: string): EventSource {
  const token = localStorage.getItem('access_token');
  const url = `http://localhost:8000/api/chat/sessions/${sessionId}/send`;
  // Use fetch for POST with SSE
  const params = new URLSearchParams();
  return new EventSource(`${url}?token=${token}`); // fallback - SSE via GET not ideal
}

export function regenerateMessage(sessionId: string): EventSource {
  const token = localStorage.getItem('access_token');
  const url = `http://localhost:8000/api/chat/sessions/${sessionId}/regenerate`;
  return new EventSource(`${url}?token=${token}`);
}

// SSE via fetch (proper POST)
export async function* streamChat(sessionId: string, content: string): AsyncGenerator<any> {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`http://localhost:8000/api/chat/sessions/${sessionId}/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) throw new Error('Request failed');

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        try {
          yield JSON.parse(data);
        } catch {
          // skip parse errors
        }
      }
    }
  }
}

export async function* regenerateStream(sessionId: string): AsyncGenerator<any> {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`http://localhost:8000/api/chat/sessions/${sessionId}/regenerate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) throw new Error('Request failed');

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        try {
          yield JSON.parse(data);
        } catch {
          // skip
        }
      }
    }
  }
}
