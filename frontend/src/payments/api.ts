/**
 * Payment API Client
 * Handles all payment-related API calls.
 */

import { apiClient } from '../api/client';

// ============================================================================
// TYPES
// ============================================================================

export interface SubscriptionPlan {
  tier: 'free' | 'pro' | 'business' | 'enterprise';
  name: string;
  description: string;
  price_monthly: number;
  price_yearly?: number;
  features: string[];
  limits: {
    docs_per_month: number;
    pages_per_doc: number;
    api_calls_per_month: number;
  };
}

export interface Subscription {
  tier: string;
  status: string;
  plan?: SubscriptionPlan;
  usage: {
    docs_used: number;
    docs_limit: number;
    api_calls_used: number;
    api_calls_limit: number;
  };
  current_period_end?: string;
  cancel_at_period_end: boolean;
  payment_method?: PaymentMethod;
  trial_end?: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  brand?: string;
  last4?: string;
  exp_month?: number;
  exp_year?: number;
  is_default: boolean;
}

export interface Invoice {
  id: string;
  number?: string;
  amount_due: number;
  amount_paid: number;
  currency: string;
  status: string;
  paid: boolean;
  created_at: string;
  due_date?: string;
  pdf_url?: string;
  hosted_invoice_url?: string;
}

export interface CheckoutSession {
  id: string;
  url: string;
  expires_at: string;
}

export interface PortalSession {
  id: string;
  url: string;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Get all available subscription plans
 */
export async function getPlans(): Promise<{ plans: SubscriptionPlan[] }> {
  const response = await apiClient.get('/payments/plans');
  return response.data;
}

/**
 * Get a specific plan by tier
 */
export async function getPlan(tier: string): Promise<SubscriptionPlan> {
  const response = await apiClient.get(`/payments/plans/${tier}`);
  return response.data;
}

/**
 * Get current user's subscription
 */
export async function getSubscription(): Promise<Subscription> {
  const response = await apiClient.get('/payments/subscription');
  return response.data;
}

/**
 * Create a checkout session for subscription
 */
export async function createCheckout(tier: string): Promise<CheckoutSession> {
  const response = await apiClient.post('/payments/checkout', { tier });
  return response.data;
}

/**
 * Create a billing portal session
 */
export async function createBillingPortal(): Promise<PortalSession> {
  const response = await apiClient.post('/payments/portal', {});
  return response.data;
}

/**
 * Upgrade subscription to a new tier
 */
export async function upgradeSubscription(tier: string): Promise<Subscription> {
  const response = await apiClient.post('/payments/subscription/upgrade', { tier });
  return response.data;
}

/**
 * Cancel subscription
 */
export async function cancelSubscription(cancelAtPeriodEnd: boolean = true): Promise<Subscription> {
  const response = await apiClient.post('/payments/subscription/cancel', {
    cancel_at_period_end: cancelAtPeriodEnd
  });
  return response.data;
}

/**
 * Reactivate a cancelled subscription
 */
export async function reactivateSubscription(): Promise<Subscription> {
  const response = await apiClient.post('/payments/subscription/reactivate');
  return response.data;
}

/**
 * Get user's invoices
 */
export async function getInvoices(limit: number = 10): Promise<Invoice[]> {
  const response = await apiClient.get(`/payments/invoices?limit=${limit}`);
  return response.data;
}

/**
 * Get user's payment methods
 */
export async function getPaymentMethods(): Promise<PaymentMethod[]> {
  const response = await apiClient.get('/payments/payment-methods');
  return response.data;
}

/**
 * Redirect to Stripe Checkout
 */
export async function redirectToCheckout(tier: string): Promise<void> {
  const session = await createCheckout(tier);
  window.location.href = session.url;
}

/**
 * Redirect to Stripe Billing Portal
 */
export async function redirectToBillingPortal(): Promise<void> {
  const session = await createBillingPortal();
  window.location.href = session.url;
}

