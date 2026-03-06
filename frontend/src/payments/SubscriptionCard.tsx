/**
 * Subscription Management Component
 * Shows current subscription status and management options.
 */

import { useState, useEffect } from 'react';
import {
  CreditCard, Calendar, AlertCircle, CheckCircle,
  Loader2, ExternalLink, RefreshCw, XCircle
} from 'lucide-react';
import {
  getSubscription, redirectToBillingPortal, reactivateSubscription,
  type Subscription
} from './api';

interface SubscriptionCardProps {
  onUpgrade?: () => void;
}

export function SubscriptionCard({ onUpgrade }: SubscriptionCardProps) {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    setIsLoading(true);
    try {
      const data = await getSubscription();
      setSubscription(data);
    } catch {
      setError('Failed to load subscription');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setActionLoading('portal');
    try {
      await redirectToBillingPortal();
    } catch {
      setError('Failed to open billing portal');
      setActionLoading(null);
    }
  };

  const handleReactivate = async () => {
    setActionLoading('reactivate');
    try {
      const updated = await reactivateSubscription();
      setSubscription(updated);
    } catch {
      setError('Failed to reactivate subscription');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'trialing':
        return 'text-blue-600 bg-blue-100';
      case 'past_due':
        return 'text-red-600 bg-red-100';
      case 'cancelled':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">Unable to load subscription details.</p>
      </div>
    );
  }

  const usagePercentage = {
    docs: Math.round((subscription.usage.docs_used / subscription.usage.docs_limit) * 100),
    api: Math.round((subscription.usage.api_calls_used / subscription.usage.api_calls_limit) * 100)
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Subscription</h2>
          <p className="text-sm text-gray-500">Manage your plan and billing</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(subscription.status)}`}>
          {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
        </span>
      </div>

      {/* Error message */}
      {error && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-100 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}

      {/* Cancellation warning */}
      {subscription.cancel_at_period_end && (
        <div className="px-6 py-3 bg-amber-50 border-b border-amber-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-amber-500" />
            <span className="text-sm text-amber-700">
              Subscription will end on {subscription.current_period_end && formatDate(subscription.current_period_end)}
            </span>
          </div>
          <button
            onClick={handleReactivate}
            disabled={actionLoading === 'reactivate'}
            className="text-sm font-medium text-amber-700 hover:text-amber-800"
          >
            {actionLoading === 'reactivate' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Reactivate'
            )}
          </button>
        </div>
      )}

      <div className="p-6 space-y-6">
        {/* Current Plan */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">Current Plan</p>
            <p className="text-2xl font-bold text-gray-900 capitalize">{subscription.tier}</p>
          </div>
          {subscription.tier !== 'enterprise' && (
            <button
              onClick={onUpgrade}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upgrade
            </button>
          )}
        </div>

        {/* Usage */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700">Usage this month</h3>

          {/* Documents usage */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Documents</span>
              <span className="text-gray-900 font-medium">
                {subscription.usage.docs_used} / {subscription.usage.docs_limit}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  usagePercentage.docs > 90 ? 'bg-red-500' : 
                  usagePercentage.docs > 70 ? 'bg-amber-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(usagePercentage.docs, 100)}%` }}
              />
            </div>
          </div>

          {/* API calls usage */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">API Calls</span>
              <span className="text-gray-900 font-medium">
                {subscription.usage.api_calls_used.toLocaleString()} / {subscription.usage.api_calls_limit.toLocaleString()}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  usagePercentage.api > 90 ? 'bg-red-500' : 
                  usagePercentage.api > 70 ? 'bg-amber-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(usagePercentage.api, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Payment method */}
        {subscription.payment_method && (
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <CreditCard className="h-5 w-5 text-gray-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 capitalize">
                {subscription.payment_method.brand} •••• {subscription.payment_method.last4}
              </p>
              <p className="text-xs text-gray-500">
                Expires {subscription.payment_method.exp_month}/{subscription.payment_method.exp_year}
              </p>
            </div>
          </div>
        )}

        {/* Billing period */}
        {subscription.current_period_end && (
          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">
                {subscription.cancel_at_period_end ? 'Access ends' : 'Renews'} on{' '}
                <span className="font-medium text-gray-900">
                  {formatDate(subscription.current_period_end)}
                </span>
              </p>
            </div>
          </div>
        )}

        {/* Trial indicator */}
        {subscription.trial_end && (
          <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
            <CheckCircle className="h-5 w-5 text-blue-500" />
            <p className="text-sm text-blue-700">
              Free trial ends on {formatDate(subscription.trial_end)}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="pt-4 border-t border-gray-200 flex gap-3">
          <button
            onClick={handleManageBilling}
            disabled={actionLoading === 'portal'}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            {actionLoading === 'portal' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <ExternalLink className="h-4 w-4" />
                Manage Billing
              </>
            )}
          </button>
          <button
            onClick={loadSubscription}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

