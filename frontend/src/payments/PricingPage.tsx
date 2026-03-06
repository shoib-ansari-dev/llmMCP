/**
 * Pricing Page Component
 * Displays subscription plans with pricing.
 */

import { useState, useEffect } from 'react';
import { Check, Loader2, Zap, Building, Rocket, Crown } from 'lucide-react';
import { getPlans, redirectToCheckout, type SubscriptionPlan, type Subscription, getSubscription } from './api';
import { useAuth } from '../auth';

const tierIcons: Record<string, React.ReactNode> = {
  free: <Zap className="h-6 w-6" />,
  pro: <Rocket className="h-6 w-6" />,
  business: <Building className="h-6 w-6" />,
  enterprise: <Crown className="h-6 w-6" />,
};

const tierColors: Record<string, string> = {
  free: 'bg-gray-100 text-gray-600',
  pro: 'bg-blue-100 text-blue-600',
  business: 'bg-purple-100 text-purple-600',
  enterprise: 'bg-amber-100 text-amber-600',
};

interface PricingPageProps {
  onSelectPlan?: (tier: string) => void;
}

export function PricingPage({ onSelectPlan }: PricingPageProps) {
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  useEffect(() => {
    loadData();
  }, [isAuthenticated]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const { plans: fetchedPlans } = await getPlans();
      setPlans(fetchedPlans);

      if (isAuthenticated) {
        const subscription = await getSubscription();
        setCurrentSubscription(subscription);
      }
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPlan = async (tier: string) => {
    if (tier === 'free') return;

    if (!isAuthenticated) {
      // Redirect to login first
      window.location.href = '/login?redirect=/pricing';
      return;
    }

    if (onSelectPlan) {
      onSelectPlan(tier);
      return;
    }

    setCheckoutLoading(tier);
    try {
      await redirectToCheckout(tier);
    } catch (error) {
      console.error('Checkout failed:', error);
      setCheckoutLoading(null);
    }
  };

  const getPrice = (plan: SubscriptionPlan) => {
    if (billingPeriod === 'yearly' && plan.price_yearly) {
      return plan.price_yearly / 12;
    }
    return plan.price_monthly;
  };

  const getSavings = (plan: SubscriptionPlan) => {
    if (plan.price_yearly && plan.price_monthly > 0) {
      const yearlyTotal = plan.price_yearly;
      const monthlyTotal = plan.price_monthly * 12;
      return Math.round(((monthlyTotal - yearlyTotal) / monthlyTotal) * 100);
    }
    return 0;
  };

  const isCurrentPlan = (tier: string) => {
    return currentSubscription?.tier === tier;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            Choose the plan that's right for you
          </p>

          {/* Billing toggle */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <span className={`text-sm ${billingPeriod === 'monthly' ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingPeriod(billingPeriod === 'monthly' ? 'yearly' : 'monthly')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                billingPeriod === 'yearly' ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  billingPeriod === 'yearly' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm ${billingPeriod === 'yearly' ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
              Yearly
              <span className="ml-1 text-green-600 font-medium">Save up to 17%</span>
            </span>
          </div>
        </div>

        {/* Plans grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {plans.map((plan) => {
            const isCurrent = isCurrentPlan(plan.tier);
            const savings = getSavings(plan);

            return (
              <div
                key={plan.tier}
                className={`relative bg-white rounded-2xl shadow-lg overflow-hidden ${
                  plan.tier === 'pro' ? 'ring-2 ring-blue-600' : ''
                }`}
              >
                {/* Popular badge */}
                {plan.tier === 'pro' && (
                  <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                    MOST POPULAR
                  </div>
                )}

                <div className="p-6">
                  {/* Plan header */}
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`p-2 rounded-lg ${tierColors[plan.tier]}`}>
                      {tierIcons[plan.tier]}
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                    </div>
                  </div>

                  <p className="text-gray-600 text-sm mb-6">{plan.description}</p>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline">
                      <span className="text-4xl font-extrabold text-gray-900">
                        ${getPrice(plan).toFixed(0)}
                      </span>
                      <span className="text-gray-500 ml-1">/month</span>
                    </div>
                    {billingPeriod === 'yearly' && savings > 0 && (
                      <p className="text-green-600 text-sm mt-1">
                        Save {savings}% with yearly billing
                      </p>
                    )}
                  </div>

                  {/* CTA Button */}
                  <button
                    onClick={() => handleSelectPlan(plan.tier)}
                    disabled={isCurrent || checkoutLoading === plan.tier || plan.tier === 'free'}
                    className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                      isCurrent
                        ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                        : plan.tier === 'free'
                        ? 'bg-gray-100 text-gray-600'
                        : plan.tier === 'pro'
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                    }`}
                  >
                    {checkoutLoading === plan.tier ? (
                      <Loader2 className="h-5 w-5 animate-spin mx-auto" />
                    ) : isCurrent ? (
                      'Current Plan'
                    ) : plan.tier === 'free' ? (
                      'Free Forever'
                    ) : plan.tier === 'enterprise' ? (
                      'Contact Sales'
                    ) : (
                      'Get Started'
                    )}
                  </button>

                  {/* Features */}
                  <div className="mt-6 pt-6 border-t border-gray-100">
                    <h4 className="text-sm font-medium text-gray-900 mb-4">
                      What's included:
                    </h4>
                    <ul className="space-y-3">
                      {plan.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                          <span className="text-sm text-gray-600">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Limits */}
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="text-xs text-gray-500 space-y-1">
                      <p>{plan.limits.docs_per_month.toLocaleString()} docs/month</p>
                      <p>{plan.limits.pages_per_doc.toLocaleString()} pages/doc</p>
                      <p>{plan.limits.api_calls_per_month.toLocaleString()} API calls/month</p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ or additional info */}
        <div className="mt-16 text-center">
          <p className="text-gray-600">
            All plans include 14-day free trial. No credit card required.
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Need a custom plan?{' '}
            <a href="mailto:sales@docubrief.com" className="text-blue-600 hover:underline">
              Contact our sales team
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

