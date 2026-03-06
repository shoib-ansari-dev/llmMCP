/**
 * ContractIQ Page
 * Contract analysis and management interface
 */

import { useState } from 'react';
import { FileText, Upload, AlertTriangle, Scale, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ContractParty {
  name: string;
  role: string;
  address?: string;
  contact?: string;
  entity_type?: string;
}

interface RiskFlag {
  risk_type: string;
  severity: string;
  description: string;
  clause_reference?: string;
  recommendation?: string;
}

interface PaymentTerm {
  amount?: number;
  currency: string;
  frequency?: string;
  due_date?: string;
  description?: string;
}

interface TerminationClause {
  termination_type: string;
  notice_period?: string;
  original_text?: string;
}

interface ConfidentialityClause {
  scope: string;
  duration?: string;
  original_text?: string;
}

interface ContractAnalysis {
  document_id: string;
  contract_type: string;
  contract_title?: string;
  analyzed_at: string;
  summary: string;
  key_points: string[];
  parties: ContractParty[];
  effective_date?: string;
  expiration_date?: string;
  key_dates: { date_type: string; date_text: string }[];
  payment_terms: PaymentTerm[];
  total_value?: number;
  termination_clauses: TerminationClause[];
  liability_clauses: { liability_type: string; original_text: string }[];
  confidentiality?: ConfidentialityClause;
  intellectual_property: { ip_type: string; scope: string }[];
  dispute_resolution?: { method: string; venue?: string };
  risk_level: string;
  risk_score: number;
  risk_flags: RiskFlag[];
  recommendations: string[];
  missing_clauses: string[];
  extracted_sections: Record<string, string>;
}

export function ContractIQPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ContractAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [contractText, setContractText] = useState('');
  const [inputMode, setInputMode] = useState<'upload' | 'text'>('upload');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const analyzeContract = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      let response;

      if (inputMode === 'upload' && file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_id', crypto.randomUUID());
        formData.append('analysis_depth', 'full');

        response = await fetch(`${API_BASE_URL}/contracts/analyze`, {
          method: 'POST',
          body: formData,
        });
      } else if (inputMode === 'text' && contractText) {
        response = await fetch(`${API_BASE_URL}/contracts/analyze/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: contractText }),
        });
      } else {
        setError('Please provide a contract file or text');
        setIsAnalyzing(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to analyze contract');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getRiskColor = (score: number) => {
    if (score < 30) return 'text-green-600 bg-green-100';
    if (score < 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      case 'critical': return 'bg-red-200 text-red-900';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <Scale className="h-8 w-8 text-purple-600" />
            <h1 className="text-xl font-bold text-gray-800">ContractIQ</h1>
            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
              Contract Analysis
            </span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Input Section */}
          <div className="col-span-5">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">
                Analyze Contract
              </h2>

              {/* Input Mode Toggle */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setInputMode('upload')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
                    inputMode === 'upload'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Upload File
                </button>
                <button
                  onClick={() => setInputMode('text')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
                    inputMode === 'text'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Paste Text
                </button>
              </div>

              {inputMode === 'upload' ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    {file ? file.name : 'Drop your contract here or click to browse'}
                  </p>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileChange}
                    className="hidden"
                    id="contract-upload"
                  />
                  <label
                    htmlFor="contract-upload"
                    className="cursor-pointer text-purple-600 hover:text-purple-700 font-medium"
                  >
                    Select File
                  </label>
                </div>
              ) : (
                <textarea
                  value={contractText}
                  onChange={(e) => setContractText(e.target.value)}
                  placeholder="Paste your contract text here..."
                  className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              )}

              {error && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  {error}
                </div>
              )}

              <button
                onClick={analyzeContract}
                disabled={isAnalyzing || (inputMode === 'upload' ? !file : !contractText)}
                className="mt-4 w-full px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <FileText className="h-5 w-5" />
                    Analyze Contract
                  </>
                )}
              </button>
            </div>

            {/* Quick Actions */}
            <div className="mt-6 bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
                  📋 View Templates
                </button>
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
                  📊 Compare Contracts
                </button>
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
                  📥 Export Report
                </button>
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="col-span-7">
            {analysis ? (
              <div className="space-y-6">
                {/* Risk Score */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-800">Risk Assessment</h2>
                    <div className={`px-4 py-2 rounded-full font-bold ${getRiskColor(analysis.risk_score)}`}>
                      Risk Score: {analysis.risk_score}/100
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${
                        analysis.risk_score < 30 ? 'bg-green-500' :
                        analysis.risk_score < 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${analysis.risk_score}%` }}
                    />
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Summary</h2>
                  <p className="text-gray-700">{analysis.summary}</p>
                </div>

                {/* Key Details */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Contract Details</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Contract Type</p>
                      <p className="font-medium">{analysis.contract_type}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Parties</p>
                      <p className="font-medium">
                        {analysis.parties?.map(p => p.name).join(', ') || 'Not specified'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Effective Date</p>
                      <p className="font-medium">{analysis.effective_date || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Expiration Date</p>
                      <p className="font-medium">{analysis.expiration_date || 'Not specified'}</p>
                    </div>
                  </div>
                </div>

                {/* Key Points */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Key Points</h2>
                  <div className="space-y-2">
                    {(analysis.key_points || []).map((point, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                        {point}
                      </div>
                    ))}
                    {(!analysis.key_points || analysis.key_points.length === 0) && (
                      <p className="text-gray-500">No key points extracted</p>
                    )}
                  </div>
                </div>

                {/* Risk Flags */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Identified Risks</h2>
                  <div className="space-y-3">
                    {(analysis.risk_flags || []).map((risk, idx) => (
                      <div key={idx} className="p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-800">{risk.risk_type}</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(risk.severity)}`}>
                            {risk.severity}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{risk.description}</p>
                      </div>
                    ))}
                    {(!analysis.risk_flags || analysis.risk_flags.length === 0) && (
                      <p className="text-gray-500">No significant risks identified</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <Scale className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-800 mb-2">No Contract Analyzed</h2>
                <p className="text-gray-500">
                  Upload a contract document or paste contract text to get AI-powered analysis,
                  risk scoring, and key term extraction.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

