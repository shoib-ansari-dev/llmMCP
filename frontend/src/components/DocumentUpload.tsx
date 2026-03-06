import { useState, useCallback } from 'react';
import { Upload, FileText, Globe, Trash2, AlertCircle } from 'lucide-react';
import { uploadDocument, analyzeUrl, deleteDocument } from '../api/client';
import type { Document } from '../api/client';
import { validateFile, validateUrl, ALLOWED_EXTENSIONS, MAX_FILE_SIZE } from '../utils/validation';

interface FileUploadProps {
  onDocumentUploaded: (docId: string) => void;
}

export function FileUpload({ onDocumentUploaded }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

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
    setValidationErrors([]);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await handleUpload(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    setValidationErrors([]);
    const files = e.target.files;
    if (files && files.length > 0) {
      await handleUpload(files[0]);
    }
  }, []);

  const handleUpload = async (file: File) => {
    // Validate file before uploading
    const validation = validateFile(file);
    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      setError(null);
      return;
    }

    setIsUploading(true);
    setError(null);
    setValidationErrors([]);

    try {
      const response = await uploadDocument(file);
      onDocumentUploaded(response.document_id);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail?.message
        || err?.response?.data?.detail
        || 'Failed to upload document. Please try again.';
      setError(errorMessage);
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const maxSizeMB = MAX_FILE_SIZE / (1024 * 1024);

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        isDragging ? 'border-blue-500 bg-blue-50' : 
        validationErrors.length > 0 ? 'border-red-300 bg-red-50' :
        'border-gray-300 hover:border-gray-400'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <Upload className={`mx-auto h-12 w-12 ${validationErrors.length > 0 ? 'text-red-400' : 'text-gray-400'}`} />
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
        accept={ALLOWED_EXTENSIONS.join(',')}
        onChange={handleFileSelect}
        disabled={isUploading}
      />
      <label
        htmlFor="file-upload"
        className={`mt-4 inline-block px-4 py-2 rounded-md cursor-pointer disabled:opacity-50 ${
          isUploading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
        } text-white`}
      >
        {isUploading ? 'Uploading...' : 'Select File'}
      </label>
      <p className="mt-2 text-xs text-gray-400">
        Supports: {ALLOWED_EXTENSIONS.join(', ')} (max {maxSizeMB}MB)
      </p>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="text-left">
              {validationErrors.map((err, index) => (
                <p key={index} className="text-sm text-red-600">{err}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Server Error */}
      {error && !validationErrors.length && (
        <p className="mt-2 text-sm text-red-500">{error}</p>
      )}
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
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newUrl = e.target.value;
    setUrl(newUrl);

    // Clear validation error while typing
    if (validationError) {
      setValidationError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate URL before submitting
    const validation = validateUrl(url);
    if (!validation.isValid) {
      setValidationError(validation.errors[0]);
      setError(null);
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setValidationError(null);

    try {
      const response = await analyzeUrl(url);
      onUrlAnalyzed(response.document_id);
      setUrl('');
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail?.message
        || err?.response?.data?.detail
        || 'Failed to analyze URL. Please check the URL and try again.';
      setError(errorMessage);
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const hasError = validationError || error;

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="flex items-center gap-2">
        <Globe className={`h-5 w-5 ${hasError ? 'text-red-400' : 'text-gray-400'}`} />
        <input
          type="text"
          value={url}
          onChange={handleUrlChange}
          placeholder="https://example.com/article"
          className={`flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 ${
            hasError 
              ? 'border-red-300 focus:ring-red-500' 
              : 'border-gray-300 focus:ring-blue-500'
          }`}
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
      {validationError && (
        <p className="text-sm text-red-500 flex items-center gap-1">
          <AlertCircle className="h-4 w-4" />
          {validationError}
        </p>
      )}
      {error && !validationError && <p className="text-sm text-red-500">{error}</p>}
      <p className="text-xs text-gray-400">
        Enter a valid URL starting with http:// or https://
      </p>
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

