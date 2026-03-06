import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, FileText, Clock, Lightbulb } from 'lucide-react';
import { listDocuments } from '../api/client';
import type { Document } from '../api/client';

interface InsightsDashboardProps {
  onSelectDocument?: (docId: string) => void;
}

interface DashboardStats {
  totalDocuments: number;
  analyzedDocuments: number;
  pendingDocuments: number;
  recentDocuments: Document[];
}

export function InsightsDashboard({ onSelectDocument }: InsightsDashboardProps) {
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    analyzedDocuments: 0,
    pendingDocuments: 0,
    recentDocuments: []
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const response = await listDocuments();
      const docs = response.documents;

      setStats({
        totalDocuments: docs.length,
        analyzedDocuments: docs.filter(d => d.status === 'analyzed' || d.status === 'completed').length,
        pendingDocuments: docs.filter(d => d.status === 'uploaded' || d.status === 'queued' || d.status === 'processing').length,
        recentDocuments: docs.slice(-5).reverse()
      });
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
        <div className="h-48 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Total Documents</p>
              <p className="text-3xl font-bold">{stats.totalDocuments}</p>
            </div>
            <FileText className="h-10 w-10 text-blue-200" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Analyzed</p>
              <p className="text-3xl font-bold">{stats.analyzedDocuments}</p>
            </div>
            <TrendingUp className="h-10 w-10 text-green-200" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-100 text-sm">Pending</p>
              <p className="text-3xl font-bold">{stats.pendingDocuments}</p>
            </div>
            <Clock className="h-10 w-10 text-yellow-200" />
          </div>
        </div>
      </div>

      {/* Recent Documents */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-blue-500" />
          Recent Documents
        </h3>

        {stats.recentDocuments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="mx-auto h-12 w-12 mb-2 text-gray-300" />
            <p>No documents yet</p>
            <p className="text-sm">Upload your first document to get started</p>
          </div>
        ) : (
          <div className="space-y-2">
            {stats.recentDocuments.map(doc => (
              <div
                key={doc.id}
                onClick={() => onSelectDocument?.(doc.id)}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <span className="text-gray-700 truncate max-w-xs">
                    {doc.filename}
                  </span>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  doc.status === 'analyzed' || doc.status === 'completed'
                    ? 'bg-green-100 text-green-700'
                    : doc.status === 'processing'
                    ? 'bg-blue-100 text-blue-700'
                    : doc.status === 'error'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Tips */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-100 p-4">
        <h3 className="text-lg font-semibold text-purple-800 mb-3 flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-purple-500" />
          Quick Tips
        </h3>
        <ul className="space-y-2 text-sm text-purple-700">
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            Upload PDFs, Excel files, or CSV documents for analysis
          </li>
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            Enter a URL to analyze web page content
          </li>
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            Use the Chat tab to ask questions about your documents
          </li>
          <li className="flex items-start gap-2">
            <span className="text-purple-400">•</span>
            Large files (5MB+) are processed in the background
          </li>
        </ul>
      </div>

      {/* Refresh Button */}
      <div className="text-center">
        <button
          onClick={fetchStats}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
        >
          Refresh Dashboard
        </button>
      </div>
    </div>
  );
}

