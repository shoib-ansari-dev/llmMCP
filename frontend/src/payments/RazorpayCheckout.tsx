/**
 * Razorpay Checkout Component
 * Handles Razorpay payment flow using Razorpay.js
 */

import { useEffect, useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    Razorpay: any;
  }
}

interface RazorpayCheckoutProps {
  subscriptionId: string;
  onSuccess: (paymentId: string) => void;
  onError: (error: string) => void;
  onCancel: () => void;
}

interface RazorpayOptions {
  key: string;
  subscription_id: string;
  name: string;
  description: string;
  image?: string;
  handler: (response: any) => void;
  modal: {
    ondismiss: () => void;
  };
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  theme?: {
    color?: string;
  };
}

export function RazorpayCheckout({
  subscriptionId,
  onSuccess,
  onError,
  onCancel
}: RazorpayCheckoutProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  const openRazorpay = () => {
    const razorpayKeyId = import.meta.env.VITE_RAZORPAY_KEY_ID;

    if (!razorpayKeyId) {
      setError('Payment gateway not configured');
      onError('Razorpay key not configured');
      return;
    }

    const options: RazorpayOptions = {
      key: razorpayKeyId,
      subscription_id: subscriptionId,
      name: 'DocuBrief',
      description: 'Subscription Payment',
      image: '/logo.png',
      handler: function(response: { razorpay_payment_id: string }) {
        // Payment successful
        onSuccess(response.razorpay_payment_id);
      },
      modal: {
        ondismiss: function() {
          onCancel();
        }
      },
      theme: {
        color: '#2563eb'
      }
    };

    try {
      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch {
      setError('Failed to open payment gateway');
      onError('Failed to initialize Razorpay');
    }
  };

  useEffect(() => {
    // Check if already loaded
    if (window.Razorpay) {
      setIsLoading(false);
      openRazorpay();
      return;
    }

    // Load Razorpay script
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => {
      setIsLoading(false);
      openRazorpay();
    };
    script.onerror = () => {
      setIsLoading(false);
      setError('Failed to load payment gateway');
      onError('Failed to load Razorpay');
    };
    document.body.appendChild(script);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading payment gateway...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Payment Error</h2>
          <p className="mt-2 text-gray-600">{error}</p>
          <button
            onClick={() => window.history.back()}
            className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto" />
        <p className="mt-4 text-gray-600">Opening payment gateway...</p>
      </div>
    </div>
  );
}

/**
 * Razorpay Checkout Page
 * Wrapper component that extracts subscription_id from URL
 */
export function RazorpayCheckoutPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'cancelled'>('loading');
  const [message, setMessage] = useState('');

  // Get subscription_id from URL params
  const params = new URLSearchParams(window.location.search);
  const subscriptionId = params.get('subscription_id');

  if (!subscriptionId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Invalid Request</h2>
          <p className="mt-2 text-gray-600">No subscription ID provided.</p>
        </div>
      </div>
    );
  }

  const handleSuccess = (paymentId: string) => {
    setStatus('success');
    setMessage(`Payment successful! ID: ${paymentId}`);
    // Redirect to success page after delay
    setTimeout(() => {
      window.location.href = '/payment/success';
    }, 2000);
  };

  const handleError = (error: string) => {
    setStatus('error');
    setMessage(error);
  };

  const handleCancel = () => {
    setStatus('cancelled');
    setMessage('Payment was cancelled');
    // Redirect to cancel page after delay
    setTimeout(() => {
      window.location.href = '/payment/cancel';
    }, 2000);
  };

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-green-50">
        <div className="text-center">
          <div className="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
            <svg className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Payment Successful!</h2>
          <p className="mt-2 text-gray-600">Redirecting to your account...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Payment Failed</h2>
          <p className="mt-2 text-gray-600">{message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (status === 'cancelled') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Payment Cancelled</h2>
          <p className="mt-2 text-gray-600">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <RazorpayCheckout
      subscriptionId={subscriptionId}
      onSuccess={handleSuccess}
      onError={handleError}
      onCancel={handleCancel}
    />
  );
}

