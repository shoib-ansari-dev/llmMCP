/**
 * DocuBrief Landing Page
 * Marketing page for document summarization SaaS.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Zap, Shield, Clock, Upload, MessageSquare,
  BarChart3, Check, ChevronDown, ChevronUp, ArrowRight,
  Globe
} from 'lucide-react';
import { PricingPage } from '../payments';

interface LandingPageProps {
  onGetStarted?: () => void;
  onLogin?: () => void;
}

export function LandingPage({ onGetStarted, onLogin }: LandingPageProps) {
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [showPricing, setShowPricing] = useState(false);

  const handleGetStarted = () => {
    if (onGetStarted) {
      onGetStarted();
    } else {
      navigate('/register');
    }
  };

  const handleLogin = () => {
    if (onLogin) {
      onLogin();
    } else {
      navigate('/login');
    }
  };

  if (showPricing) {
    return (
      <div>
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <button
              onClick={() => setShowPricing(false)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
            >
              ← Back
            </button>
            <button
              onClick={handleLogin}
              className="px-4 py-2 text-blue-600 hover:text-blue-700 font-medium"
            >
              Sign In
            </button>
          </div>
        </nav>
        <PricingPage onSelectPlan={() => handleGetStarted()} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">DocuBrief</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <button
              onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
              className="text-gray-600 hover:text-gray-900"
            >
              Features
            </button>
            <button
              onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
              className="text-gray-600 hover:text-gray-900"
            >
              How it Works
            </button>
            <button
              onClick={() => setShowPricing(true)}
              className="text-gray-600 hover:text-gray-900"
            >
              Pricing
            </button>
            <button
              onClick={() => document.getElementById('testimonials')?.scrollIntoView({ behavior: 'smooth' })}
              className="text-gray-600 hover:text-gray-900"
            >
              Testimonials
            </button>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleLogin}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium"
            >
              Sign In
            </button>
            <button
              onClick={handleGetStarted}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Get Started Free
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4 bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-6">
                <Zap className="h-4 w-4" />
                AI-Powered Document Analysis
              </div>
              <h1 className="text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
                Summarize any document in{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                  seconds
                </span>
              </h1>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                Upload PDFs, spreadsheets, or web pages. Get instant AI summaries,
                key insights, and answers to your questions. Save hours of reading time.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <button
                  onClick={handleGetStarted}
                  className="px-8 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-semibold text-lg flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25"
                >
                  Start Free Trial
                  <ArrowRight className="h-5 w-5" />
                </button>
                <button
                  onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
                  className="px-8 py-4 border-2 border-gray-300 text-gray-700 rounded-xl hover:border-gray-400 font-semibold text-lg"
                >
                  Watch Demo
                </button>
              </div>
              <div className="mt-8 flex items-center gap-6 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-500" />
                  No credit card required
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-500" />
                  5 free documents/month
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="bg-white rounded-2xl shadow-2xl p-6 border border-gray-100">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-400"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                  <div className="w-3 h-3 rounded-full bg-green-400"></div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                    <Upload className="h-5 w-5 text-blue-600" />
                    <span className="text-gray-700">annual-report-2025.pdf uploaded</span>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm font-medium text-gray-700 mb-2">AI Summary</div>
                    <p className="text-gray-600 text-sm">
                      Revenue increased 23% YoY to $4.2B. Key growth drivers:
                      cloud services (+45%), international expansion (+32%).
                      Operating margin improved 2.3 points to 18.7%...
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                      📈 Revenue Growth
                    </span>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                      🌍 Market Expansion
                    </span>
                    <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                      💰 Profitability
                    </span>
                  </div>
                </div>
              </div>
              {/* Floating elements */}
              <div className="absolute -top-4 -right-4 bg-white rounded-lg shadow-lg p-3 border border-gray-100">
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span className="text-gray-700">2.3s processing</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Logos Section */}
      {/*<section className="py-12 bg-gray-50 border-y border-gray-100">*/}
      {/*  <div className="max-w-7xl mx-auto px-4">*/}
      {/*    <p className="text-center text-gray-500 text-sm mb-8">Trusted by teams at</p>*/}
      {/*    <div className="flex flex-wrap justify-center items-center gap-12 opacity-60">*/}
      {/*      <Building className="h-8 w-auto text-gray-400" />*/}
      {/*      <span className="text-2xl font-bold text-gray-400">TechCorp</span>*/}
      {/*      <span className="text-2xl font-bold text-gray-400">LawFirm LLP</span>*/}
      {/*      <span className="text-2xl font-bold text-gray-400">ConsultCo</span>*/}
      {/*      <span className="text-2xl font-bold text-gray-400">FinanceHub</span>*/}
      {/*    </div>*/}
      {/*  </div>*/}
      {/*</section>*/}

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Everything you need to analyze documents faster
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Powerful AI features that save you hours of reading and help you extract key insights instantly.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-50 to-white border border-blue-100">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-4">
                <Upload className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Multi-Format Support</h3>
              <p className="text-gray-600">
                Upload PDFs, Excel spreadsheets, Word docs, CSV files, or paste any URL.
                We handle it all seamlessly.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-50 to-white border border-purple-100">
              <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Instant Summaries</h3>
              <p className="text-gray-600">
                Get comprehensive summaries in seconds. Our AI extracts the most
                important information automatically.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-green-50 to-white border border-green-100">
              <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center mb-4">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Ask Questions</h3>
              <p className="text-gray-600">
                Chat with your documents. Ask specific questions and get accurate
                answers with source citations.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-orange-50 to-white border border-orange-100">
              <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center mb-4">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Key Insights</h3>
              <p className="text-gray-600">
                Automatically extract key metrics, trends, and insights.
                Perfect for financial reports and research.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-red-50 to-white border border-red-100">
              <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Enterprise Security</h3>
              <p className="text-gray-600">
                Your documents are encrypted and never used for training.
                SOC 2 compliant with data residency options.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-50 to-white border border-indigo-100">
              <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center mb-4">
                <Globe className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">API Access</h3>
              <p className="text-gray-600">
                Integrate document analysis into your workflow with our
                powerful REST API. Full documentation included.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="py-24 px-4 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              How it works
            </h2>
            <p className="text-xl text-gray-600">
              Three simple steps to transform your documents
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-2xl font-bold">
                1
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Upload</h3>
              <p className="text-gray-600">
                Drag and drop your PDF, spreadsheet, or paste a URL.
                We support documents up to 200 pages.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-2xl font-bold">
                2
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Analyze</h3>
              <p className="text-gray-600">
                Our AI processes your document in seconds, extracting
                summaries, key points, and insights.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-2xl font-bold">
                3
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Interact</h3>
              <p className="text-gray-600">
                Ask questions, get answers, and export your findings.
                Save hours of manual reading.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="py-24 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              See it in action
            </h2>
            <p className="text-xl text-gray-600">
              Watch how DocuBrief transforms a 50-page report into actionable insights
            </p>
          </div>
          <div className="aspect-video bg-gray-900 rounded-2xl flex items-center justify-center">
            <div className="text-center text-white">
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 cursor-pointer hover:bg-white/30 transition-colors">
                <svg className="w-8 h-8 ml-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <p className="text-gray-400">Click to play demo video</p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      {/*<section id="testimonials" className="py-24 px-4 bg-gray-50">*/}
      {/*  <div className="max-w-7xl mx-auto">*/}
      {/*    <div className="text-center mb-16">*/}
      {/*      <h2 className="text-4xl font-bold text-gray-900 mb-4">*/}
      {/*        Loved by professionals worldwide*/}
      {/*      </h2>*/}
      {/*      <p className="text-xl text-gray-600">*/}
      {/*        See what our customers have to say*/}
      {/*      </p>*/}
      {/*    </div>*/}

      {/*    <div className="grid md:grid-cols-3 gap-8">*/}
      {/*      /!* Testimonial 1 *!/*/}
      {/*      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">*/}
      {/*        <div className="flex gap-1 mb-4">*/}
      {/*          {[...Array(5)].map((_, i) => (*/}
      {/*            <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />*/}
      {/*          ))}*/}
      {/*        </div>*/}
      {/*        <p className="text-gray-700 mb-6">*/}
      {/*          "DocuBrief has transformed how our legal team reviews contracts.*/}
      {/*          What used to take hours now takes minutes. The accuracy is incredible."*/}
      {/*        </p>*/}
      {/*        <div className="flex items-center gap-3">*/}
      {/*          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">*/}
      {/*            <span className="text-blue-600 font-semibold">SK</span>*/}
      {/*          </div>*/}
      {/*          <div>*/}
      {/*            <div className="font-semibold text-gray-900">Sarah Kim</div>*/}
      {/*            <div className="text-sm text-gray-500">Legal Counsel, TechCorp</div>*/}
      {/*          </div>*/}
      {/*        </div>*/}
      {/*      </div>*/}

      {/*      /!* Testimonial 2 *!/*/}
      {/*      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">*/}
      {/*        <div className="flex gap-1 mb-4">*/}
      {/*          {[...Array(5)].map((_, i) => (*/}
      {/*            <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />*/}
      {/*          ))}*/}
      {/*        </div>*/}
      {/*        <p className="text-gray-700 mb-6">*/}
      {/*          "As a consultant, I analyze dozens of reports weekly. DocuBrief*/}
      {/*          helps me extract key insights instantly. It's like having a research assistant."*/}
      {/*        </p>*/}
      {/*        <div className="flex items-center gap-3">*/}
      {/*          <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">*/}
      {/*            <span className="text-green-600 font-semibold">MR</span>*/}
      {/*          </div>*/}
      {/*          <div>*/}
      {/*            <div className="font-semibold text-gray-900">Michael Roberts</div>*/}
      {/*            <div className="text-sm text-gray-500">Senior Consultant, McKinsey</div>*/}
      {/*          </div>*/}
      {/*        </div>*/}
      {/*      </div>*/}

      {/*      /!* Testimonial 3 *!/*/}
      {/*      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">*/}
      {/*        <div className="flex gap-1 mb-4">*/}
      {/*          {[...Array(5)].map((_, i) => (*/}
      {/*            <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />*/}
      {/*          ))}*/}
      {/*        </div>*/}
      {/*        <p className="text-gray-700 mb-6">*/}
      {/*          "I use DocuBrief for my MBA research papers. It summarizes academic*/}
      {/*          papers perfectly and helps me find relevant quotes quickly."*/}
      {/*        </p>*/}
      {/*        <div className="flex items-center gap-3">*/}
      {/*          <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">*/}
      {/*            <span className="text-purple-600 font-semibold">JP</span>*/}
      {/*          </div>*/}
      {/*          <div>*/}
      {/*            <div className="font-semibold text-gray-900">Jessica Park</div>*/}
      {/*            <div className="text-sm text-gray-500">MBA Student, Stanford GSB</div>*/}
      {/*          </div>*/}
      {/*        </div>*/}
      {/*      </div>*/}
      {/*    </div>*/}
      {/*  </div>*/}
      {/*</section>*/}

      {/* Pricing Preview */}
      <section className="py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, transparent pricing
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Start free, upgrade when you need more
          </p>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="p-6 bg-white rounded-xl border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Free</h3>
              <div className="text-3xl font-bold text-gray-900 my-2">$0</div>
              <p className="text-gray-500 text-sm">5 docs/month</p>
            </div>
            <div className="p-6 bg-blue-600 rounded-xl text-white relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded-full">
                POPULAR
              </div>
              <h3 className="text-lg font-semibold">Pro</h3>
              <div className="text-3xl font-bold my-2">$19<span className="text-lg font-normal">/mo</span></div>
              <p className="text-blue-100 text-sm">100 docs/month</p>
            </div>
            <div className="p-6 bg-white rounded-xl border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Business</h3>
              <div className="text-3xl font-bold text-gray-900 my-2">$49<span className="text-lg font-normal">/mo</span></div>
              <p className="text-gray-500 text-sm">1000 docs/month</p>
            </div>
          </div>

          <button
            onClick={() => setShowPricing(true)}
            className="px-8 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 font-medium"
          >
            View Full Pricing
          </button>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-24 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Frequently asked questions
            </h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div
                key={index}
                className="bg-white rounded-lg border border-gray-200 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                  className="w-full px-6 py-4 text-left flex items-center justify-between"
                >
                  <span className="font-medium text-gray-900">{faq.question}</span>
                  {openFaq === index ? (
                    <ChevronUp className="h-5 w-5 text-gray-500" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-500" />
                  )}
                </button>
                {openFaq === index && (
                  <div className="px-6 pb-4 text-gray-600">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to save hours on document analysis?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of professionals who trust DocuBrief
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGetStarted}
              className="px-8 py-4 bg-white text-blue-600 rounded-xl hover:bg-gray-100 font-semibold text-lg"
            >
              Start Free Trial
            </button>
            <button
              onClick={() => setShowPricing(true)}
              className="px-8 py-4 border-2 border-white text-white rounded-xl hover:bg-white/10 font-semibold text-lg"
            >
              View Pricing
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-6 w-6 text-blue-400" />
                <span className="text-lg font-bold text-white">DocuBrief</span>
              </div>
              <p className="text-sm">
                AI-powered document analysis for professionals.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><button onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })} className="hover:text-white">Features</button></li>
                <li><button onClick={() => setShowPricing(true)} className="hover:text-white">Pricing</button></li>
                <li><a href="#" className="hover:text-white">API</a></li>
                <li><a href="#" className="hover:text-white">Integrations</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Careers</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white">Terms of Service</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
                <li><a href="#" className="hover:text-white">GDPR</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm">© 2026 DocuBrief. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <a href="#" className="hover:text-white">Twitter</a>
              <a href="#" className="hover:text-white">LinkedIn</a>
              <a href="#" className="hover:text-white">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// FAQ Data
const faqs = [
  {
    question: "What types of documents can I upload?",
    answer: "DocuBrief supports PDFs, Excel spreadsheets (.xlsx, .xls), CSV files, Word documents (.docx), and web URLs. We can process documents up to 200 pages or 50MB in size."
  },
  {
    question: "How accurate are the AI summaries?",
    answer: "Our AI is powered by state-of-the-art language models and achieves over 95% accuracy on factual extraction. We also provide source citations so you can verify any information."
  },
  {
    question: "Is my data secure?",
    answer: "Absolutely. All documents are encrypted in transit and at rest. We never use your data for training AI models. We're SOC 2 Type II compliant and offer data residency options for enterprise customers."
  },
  {
    question: "Can I cancel my subscription anytime?",
    answer: "Yes, you can cancel your subscription at any time. You'll continue to have access until the end of your billing period. No hidden fees or cancellation charges."
  },
  {
    question: "Do you offer team plans?",
    answer: "Yes! Our Business and Enterprise plans include team collaboration features. You can invite team members, share documents, and manage permissions from a central dashboard."
  },
  {
    question: "What languages are supported?",
    answer: "DocuBrief currently supports documents in English, Spanish, French, German, Portuguese, Italian, Dutch, and Japanese. We're adding more languages regularly."
  },
  {
    question: "Is there an API available?",
    answer: "Yes, Pro and Business plans include API access. You can integrate DocuBrief into your existing workflows, automate document processing, and build custom applications."
  },
  {
    question: "What's included in the free plan?",
    answer: "The free plan includes 5 documents per month, up to 10 pages each. You get full access to summaries, key insights, and Q&A features. Perfect for trying out the service."
  }
];

