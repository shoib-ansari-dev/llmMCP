import { useState, useEffect } from 'react';
import { FileText, MessageSquare, BarChart3, LayoutDashboard, LogOut, User, Scale, TrendingUp } from 'lucide-react';
import { FileUpload, UrlInput, DocumentList, ChatInterface, SummaryDisplay, InsightsDashboard } from '../components';
import { listDocuments, analyzeDocument } from '../api/client';
import type { Document, SummaryResponse } from '../api/client';
import { useAuth } from '../auth';
import { useNavigate } from 'react-router-dom';

type Tab = 'dashboard' | 'upload' | 'chat' | 'summary';

export function DashboardPage() {
  const { user, isAuthenticated, isDevMode, logout } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
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
    if (isAuthenticated) {
      fetchDocuments();
    }
  }, [isAuthenticated]);

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

  const handleLogout = async () => {
    await logout();
    navigate('/');
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
            {isDevMode && (
              <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                Dev Mode
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <User className="h-4 w-4" />
              <span>{user?.name || user?.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Product Navigation */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-3 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <FileText className="h-8 w-8 text-blue-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">DocuBrief</h3>
              <p className="text-xs text-gray-500">Document Summarization</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/contracts')}
            className="flex items-center gap-3 p-4 bg-purple-50 border-2 border-purple-200 rounded-lg hover:bg-purple-100 transition-colors"
          >
            <Scale className="h-8 w-8 text-purple-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">ContractIQ</h3>
              <p className="text-xs text-gray-500">Contract Analysis</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/finance')}
            className="flex items-center gap-3 p-4 bg-green-50 border-2 border-green-200 rounded-lg hover:bg-green-100 transition-colors"
          >
            <TrendingUp className="h-8 w-8 text-green-600" />
            <div className="text-left">
              <h3 className="font-semibold text-gray-800">FinanceDigest</h3>
              <p className="text-xs text-gray-500">Financial Analysis</p>
            </div>
          </button>
        </div>

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
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'dashboard'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <LayoutDashboard className="h-4 w-4" />
                    Dashboard
                  </span>
                </button>
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
              {activeTab === 'dashboard' && (
                <InsightsDashboard
                  onSelectDocument={(docId) => {
                    handleSelectDocument(docId);
                  }}
                />
              )}

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

