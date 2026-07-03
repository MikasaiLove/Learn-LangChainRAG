import client from './client';

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  char_count: number;
  chunk_count: number;
  uploaded_by: string;
  error_message?: string;
  created_at?: string;
  updated_at?: string;
}

export async function getDocuments(params: {
  page?: number;
  size?: number;
  status?: string;
  search?: string;
}): Promise<{ items: Document[]; total: number }> {
  const res = await client.get('/api/knowledge/documents', { params });
  return res.data;
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await client.post('/api/knowledge/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function deleteDocument(docId: string): Promise<void> {
  await client.delete(`/api/knowledge/documents/${docId}`);
}

export async function getDocumentStatus(docId: string): Promise<{
  id: string;
  status: string;
  char_count: number;
  chunk_count: number;
}> {
  const res = await client.get(`/api/knowledge/documents/${docId}/status`);
  return res.data;
}

export async function getStats(): Promise<{
  document_count: number;
  total_chunks: number;
  total_chars: number;
}> {
  const res = await client.get('/api/knowledge/stats');
  return res.data;
}
