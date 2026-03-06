/**
 * FinanceDigest Page
 * Financial report analysis interface
 */

import { useState } from 'react';
import { TrendingUp, Upload, AlertTriangle, DollarSign, ArrowLeft, Search, Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RevenueMetrics {
  total_revenue?: number;
  revenue_growth?: number;
  currency: string;
}

interface ProfitabilityMetrics {
  gross_margin?: number;
  operating_margin?: number;
  net_margin?: number;
  net_income?: number;
}

interface RiskFactor {
  category: string;
  severity: string;
  description: string;
}

interface RedFlag {
  flag_type: string;
  severity: string;
  description: string;
}

interface InvestmentThesis {
  recommendation?: string;
  thesis_summary?: string;
  bull_case?: string;
  bear_case?: string;
}

interface FinancialAnalysis {
  document_id: string;
  company_name?: string;
  ticker?: string;
  filing_type: string;
  filing_date?: string;
  period: string;
  analyzed_at: string;
  summary: string;
  key_highlights: string[];
  overall_sentiment: string;
  revenue?: RevenueMetrics;
  profitability?: ProfitabilityMetrics;
  cash_flow?: { operating?: number; investing?: number; financing?: number };
  valuation?: { pe_ratio?: number; pb_ratio?: number; market_cap?: number };
  ratios?: { current_ratio?: number; debt_to_equity?: number };
  risk_factors: RiskFactor[];
  management_outlook?: { tone?: string; guidance?: string };
  investment_thesis?: InvestmentThesis;
  red_flags: RedFlag[];
  yoy_changes: Record<string, number>;
  qoq_changes: Record<string, number>;
  action_items: string[];
}

interface WatchlistItem {
  ticker: string;
  company_name: string;
  last_filing: string;
}

export function FinanceDigestPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<FinancialAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ticker, setTicker] = useState('');
  const [inputMode, setInputMode] = useState<'upload' | 'ticker'>('ticker');
  const [watchlist] = useState<WatchlistItem[]>([
    { ticker: 'AAPL', company_name: 'Apple Inc.', last_filing: '10-K 2025' },
    { ticker: 'MSFT', company_name: 'Microsoft Corp.', last_filing: '10-Q Q3 2025' },
    { ticker: 'GOOGL', company_name: 'Alphabet Inc.', last_filing: '10-K 2025' },
  ]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const analyzeReport = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      let response;

      if (inputMode === 'upload' && file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_id', crypto.randomUUID());
        formData.append('include_thesis', 'true');

        response = await fetch(`${API_BASE_URL}/finance/analyze`, {
          method: 'POST',
          body: formData,
        });
      } else if (inputMode === 'ticker' && ticker) {
        response = await fetch(`${API_BASE_URL}/finance/sec/filings/${ticker}/10k`, {
          method: 'GET',
        });
      } else {
        setError('Please provide a report file or ticker symbol');
        setIsAnalyzing(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to analyze report');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatCurrency = (value: number) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return `$${value.toLocaleString()}`;
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
            <TrendingUp className="h-8 w-8 text-green-600" />
            <h1 className="text-xl font-bold text-gray-800">FinanceDigest</h1>
            <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
              Financial Analysis
            </span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Input Section */}
          <div className="col-span-4">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">
                Analyze Financial Report
              </h2>

              {/* Input Mode Toggle */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setInputMode('ticker')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
                    inputMode === 'ticker'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Search className="h-4 w-4 inline mr-1" />
                  Ticker
                </button>
                <button
                  onClick={() => setInputMode('upload')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
                    inputMode === 'upload'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Upload className="h-4 w-4 inline mr-1" />
                  Upload
                </button>
              </div>

              {inputMode === 'ticker' ? (
                <div>
                  <input
                    type="text"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    placeholder="Enter ticker (e.g., AAPL)"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-lg font-mono"
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    We'll fetch the latest SEC filings for analysis
                  </p>
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    {file ? file.name : 'Drop financial report here'}
                  </p>
                  <input
                    type="file"
                    accept=".pdf,.xlsx,.csv"
                    onChange={handleFileChange}
                    className="hidden"
                    id="report-upload"
                  />
                  <label
                    htmlFor="report-upload"
                    className="cursor-pointer text-green-600 hover:text-green-700 font-medium"
                  >
                    Select File
                  </label>
                </div>
              )}

              {error && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  {error}
                </div>
              )}

              <button
                onClick={analyzeReport}
                disabled={isAnalyzing || (inputMode === 'upload' ? !file : !ticker)}
                className="mt-4 w-full px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-5 w-5" />
                    Analyze Report
                  </>
                )}
              </button>
            </div>

            {/* Watchlist */}
            <div className="mt-6 bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-800">Watchlist</h3>
                <Bell className="h-4 w-4 text-gray-400" />
              </div>
              <div className="space-y-2">
                {watchlist.map((item) => (
                  <button
                    key={item.ticker}
                    onClick={() => {
                      setTicker(item.ticker);
                      setInputMode('ticker');
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 rounded-lg flex items-center justify-between"
                  >
                    <div>
                      <span className="font-mono font-medium text-gray-800">{item.ticker}</span>
                      <p className="text-xs text-gray-500">{item.company_name}</p>
                    </div>
                    <span className="text-xs text-gray-400">{item.last_filing}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="col-span-8">
            {analysis ? (
              <div className="space-y-6">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-800">{analysis.company_name || 'Financial Report'}</h2>
                      <p className="text-gray-500">{analysis.filing_type} • {analysis.period || 'N/A'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-gray-800">
                        {analysis.revenue?.total_revenue ? formatCurrency(analysis.revenue.total_revenue) : 'N/A'}
                      </p>
                      {analysis.revenue?.revenue_growth !== undefined && (
                        <p className={`text-sm ${analysis.revenue.revenue_growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {analysis.revenue.revenue_growth >= 0 ? '↑' : '↓'} {Math.abs(analysis.revenue.revenue_growth).toFixed(1)}% YoY
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Summary</h2>
                  <p className="text-gray-700">{analysis.summary || 'No summary available'}</p>
                </div>

                {/* Key Highlights */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Key Highlights</h2>
                  <div className="space-y-2">
                    {(analysis.key_highlights || []).map((highlight, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                        {highlight}
                      </div>
                    ))}
                    {(!analysis.key_highlights || analysis.key_highlights.length === 0) && (
                      <p className="text-gray-500">No key highlights available</p>
                    )}
                  </div>
                </div>

                {/* Profitability Metrics */}
                {analysis.profitability && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4">Profitability</h2>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-800">
                          {analysis.profitability.gross_margin?.toFixed(1) || 'N/A'}%
                        </p>
                        <p className="text-sm text-gray-500">Gross Margin</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-800">
                          {analysis.profitability.operating_margin?.toFixed(1) || 'N/A'}%
                        </p>
                        <p className="text-sm text-gray-500">Operating Margin</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-800">
                          {analysis.profitability.net_margin?.toFixed(1) || 'N/A'}%
                        </p>
                        <p className="text-sm text-gray-500">Net Margin</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Risk Factors */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-semibold text-gray-800 mb-4">Risk Factors</h2>
                  <div className="space-y-3">
                    {(analysis.risk_factors || []).map((risk, idx) => (
                      <div key={idx} className="p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-800">{risk.category}</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            risk.severity === 'high' ? 'bg-red-100 text-red-800' :
                            risk.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {risk.severity}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{risk.description}</p>
                      </div>
                    ))}
                    {(!analysis.risk_factors || analysis.risk_factors.length === 0) && (
                      <p className="text-gray-500">No risk factors identified</p>
                    )}
                  </div>
                </div>

                {/* Investment Thesis */}
                {analysis.investment_thesis && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4">Investment Thesis</h2>
                    <p className="text-gray-700">{analysis.investment_thesis.thesis_summary || 'No thesis available'}</p>
                    {analysis.investment_thesis.recommendation && (
                      <p className="mt-2 font-medium text-blue-600">Recommendation: {analysis.investment_thesis.recommendation}</p>
                    )}
                  </div>
                )}

                {/* Red Flags */}
                {(analysis.red_flags || []).length > 0 && (
                  <div className="bg-red-50 rounded-lg shadow-sm p-6 border border-red-200">
                    <h2 className="text-lg font-semibold text-red-800 mb-4 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      Red Flags
                    </h2>
                    <ul className="space-y-2">
                      {analysis.red_flags.map((flag, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-red-700">
                          <span className="text-red-500">•</span>
                          <div>
                            <span className="font-medium">{flag.flag_type}: </span>
                            {flag.description}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <DollarSign className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-800 mb-2">No Report Analyzed</h2>
                <p className="text-gray-500 mb-4">
                  Enter a ticker symbol to fetch SEC filings, or upload a financial report
                  for AI-powered analysis.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">Revenue Analysis</span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">Profit Margins</span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">Risk Factors</span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">Red Flags</span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">Investment Thesis</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

