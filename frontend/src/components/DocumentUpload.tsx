import { useState, useCallback } from 'react';
import { Upload, FileText, Globe, Trash2 } from 'lucide-react';
import { uploadDocument, analyzeUrl, deleteDocument } from '../api/client';
import type { Document } from '../api/client';

interface FileUploadProps {
  onDocumentUploaded: (docId: string) => void;
}

export function FileUpload({ onDocumentUploaded }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await handleUpload(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await handleUpload(files[0]);
    }
  }, []);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadDocument(file);
      onDocumentUploaded(response.document_id);
    } catch (err) {
      setError('Failed to upload document. Please try again.');
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <Upload className="mx-auto h-12 w-12 text-gray-400" />
      <p className="mt-4 text-lg font-medium text-gray-700">
        {isUploading ? 'Uploading...' : 'Drop your document here'}
      </p>
      <p className="mt-2 text-sm text-gray-500">
        or click to select a file
      </p>
      <input
        type="file"
        className="hidden"
        id="file-upload"
        accept=".pdf,.xlsx,.xls,.csv"
        onChange={handleFileSelect}
        disabled={isUploading}
      />
      <label
        htmlFor="file-upload"
        className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-md cursor-pointer hover:bg-blue-700 disabled:opacity-50"
      >
        Select File
      </label>
      <p className="mt-2 text-xs text-gray-400">
        Supports PDF, Excel, and CSV files
      </p>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}

interface UrlInputProps {
  onUrlAnalyzed: (docId: string) => void;
}

export function UrlInput({ onUrlAnalyzed }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await analyzeUrl(url);
      onUrlAnalyzed(response.document_id);
      setUrl('');
    } catch (err) {
      setError('Failed to analyze URL. Please check the URL and try again.');
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center gap-2">
        <Globe className="h-5 w-5 text-gray-400" />
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isAnalyzing}
        />
        <button
          type="submit"
          disabled={isAnalyzing || !url.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </form>
  );
}

interface DocumentListProps {
  documents: Document[];
  onRefresh: () => void;
  onSelect: (docId: string) => void;
}

export function DocumentList({ documents, onRefresh, onSelect }: DocumentListProps) {
  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteDocument(docId);
      onRefresh();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="mx-auto h-8 w-8 mb-2" />
        <p>No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-gray-200">
      {documents.map((doc) => (
        <li
          key={doc.id}
          className="flex items-center justify-between py-3 px-4 hover:bg-gray-50 cursor-pointer rounded-md"
          onClick={() => onSelect(doc.id)}
        >
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-700 truncate max-w-xs">
                {doc.filename}
              </p>
              <p className="text-xs text-gray-500">{doc.status}</p>
            </div>
          </div>
          <button
            onClick={(e) => handleDelete(doc.id, e)}
            className="p-1 text-gray-400 hover:text-red-500"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}

