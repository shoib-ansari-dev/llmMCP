import { useState, useEffect } from 'react';
import { FileText, MessageSquare, BarChart3 } from 'lucide-react';
import { FileUpload, UrlInput, DocumentList, ChatInterface, SummaryDisplay } from './components';
import { listDocuments, analyzeDocument } from './api/client';
import type { Document, SummaryResponse } from './api/client';
import './App.css';

type Tab = 'upload' | 'chat' | 'summary';

function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);

  const fetchDocuments = async () => {
    try {
      const response = await listDocuments();
      setDocuments(response.documents);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDocumentUploaded = (docId: string) => {
    fetchDocuments();
    setSelectedDocId(docId);
  };

  const handleSelectDocument = async (docId: string) => {
    setSelectedDocId(docId);
    setIsLoadingSummary(true);
    try {
      const response = await analyzeDocument(docId);
      setSummary(response);
      setActiveTab('summary');
    } catch (err) {
      console.error('Failed to analyze document:', err);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-800">
              Document Analysis Agent
            </h1>
          </div>
          <p className="text-sm text-gray-500">Powered by Claude AI</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="col-span-3 bg-white rounded-lg shadow-sm p-4">
            <h2 className="font-semibold text-gray-800 mb-4">Documents</h2>
            <DocumentList
              documents={documents}
              onRefresh={fetchDocuments}
              onSelect={handleSelectDocument}
            />
          </aside>

          {/* Main Content */}
          <main className="col-span-9 bg-white rounded-lg shadow-sm">
            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="flex">
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'upload'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Upload
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'chat'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Chat
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'summary'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Summary
                  </span>
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-6 min-h-[500px]">
              {activeTab === 'upload' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800 mb-4">
                      Upload Document
                    </h2>
                    <FileUpload onDocumentUploaded={handleDocumentUploaded} />
                  </div>
                  <div className="border-t border-gray-200 pt-6">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4">
                      Analyze Web Page
                    </h2>
                    <UrlInput onUrlAnalyzed={handleDocumentUploaded} />
                  </div>
                </div>
              )}

              {activeTab === 'chat' && (
                <div className="h-[500px]">
                  <ChatInterface selectedDocumentId={selectedDocId || undefined} />
                </div>
              )}

              {activeTab === 'summary' && (
                <SummaryDisplay
                  summary={summary?.summary || ''}
                  insights={summary?.insights || []}
                  isLoading={isLoadingSummary}
                />
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
