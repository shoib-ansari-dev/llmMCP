import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Document {
  id: string;
  filename: string;
  status: string;
}

export interface DocumentResponse {
  document_id: string;
  status: string;
  message: string;
}

export interface SummaryResponse {
  document_id: string;
  summary: string;
  insights: string[];
}

export interface AnswerResponse {
  question: string;
  answer: string;
  sources: string[];
}

// Upload a document
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<DocumentResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Analyze a URL
export const analyzeUrl = async (url: string) => {
  const response = await api.post<DocumentResponse>('/analyze/url', { url });
  return response.data;
};

// Analyze a document
export const analyzeDocument = async (documentId: string) => {
  const response = await api.post<SummaryResponse>(`/analyze/${documentId}`);
  return response.data;
};

// Get document summary
export const getSummary = async (documentId: string) => {
  const response = await api.get<SummaryResponse>(`/summarize/${documentId}`);
  return response.data;
};

// Ask a question
export const askQuestion = async (question: string, documentId?: string) => {
  const response = await api.post<AnswerResponse>('/ask', { question, document_id: documentId });
  return response.data;
};

// List all documents
export const listDocuments = async () => {
  const response = await api.get<{ documents: Document[] }>('/documents');
  return response.data;
};

// Delete a document
export const deleteDocument = async (documentId: string) => {
  await api.delete(`/documents/${documentId}`);
};

export default api;

