/**
 * Frontend Validation Utilities
 * Validates all user inputs before sending to the API
 */

// =================================
// File Validation
// =================================

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
export const ALLOWED_EXTENSIONS = ['.pdf', '.xlsx', '.xls', '.csv'];
export const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/csv',
];

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export function validateFile(file: File): ValidationResult {
  const errors: string[] = [];

  // Check if file exists
  if (!file) {
    return { isValid: false, errors: ['No file selected'] };
  }

  // Validate file name
  if (!file.name || file.name.trim() === '') {
    errors.push('Invalid file name');
  }

  // Validate file extension
  const extension = file.name.toLowerCase().split('.').pop();
  const fullExtension = extension ? `.${extension}` : '';
  if (!ALLOWED_EXTENSIONS.includes(fullExtension)) {
    errors.push(`Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
  }

  // Validate MIME type
  if (!ALLOWED_MIME_TYPES.includes(file.type)) {
    errors.push(`Invalid file format. Please upload PDF, Excel, or CSV files.`);
  }

  // Validate file size
  if (file.size <= 0) {
    errors.push('File is empty');
  } else if (file.size > MAX_FILE_SIZE) {
    const maxMB = MAX_FILE_SIZE / (1024 * 1024);
    errors.push(`File size exceeds ${maxMB}MB limit`);
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// =================================
// URL Validation
// =================================

const URL_PATTERN = /^https?:\/\/(?:(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:\/\S*)?$/i;
const MAX_URL_LENGTH = 2048;

export function validateUrl(url: string): ValidationResult {
  const errors: string[] = [];

  // Check if URL exists
  if (!url || url.trim() === '') {
    return { isValid: false, errors: ['URL is required'] };
  }

  const trimmedUrl = url.trim();

  // Check length
  if (trimmedUrl.length > MAX_URL_LENGTH) {
    errors.push(`URL exceeds maximum length of ${MAX_URL_LENGTH} characters`);
  }

  // Check if starts with http:// or https://
  if (!trimmedUrl.toLowerCase().startsWith('http://') && !trimmedUrl.toLowerCase().startsWith('https://')) {
    errors.push('URL must start with http:// or https://');
    return { isValid: false, errors };
  }

  // Check URL pattern format
  if (!URL_PATTERN.test(trimmedUrl)) {
    errors.push('Invalid URL format');
  }

  // Block localhost and internal URLs
  const blockedHosts = ['localhost', '127.0.0.1', '0.0.0.0'];
  const lowerUrl = trimmedUrl.toLowerCase();
  for (const host of blockedHosts) {
    if (lowerUrl.includes(host)) {
      errors.push('Local URLs are not allowed');
      break;
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// =================================
// Question Validation
// =================================

const MIN_QUESTION_LENGTH = 3;
const MAX_QUESTION_LENGTH = 1000;

export function validateQuestion(question: string): ValidationResult {
  const errors: string[] = [];

  // Check if question exists
  if (!question || question.trim() === '') {
    return { isValid: false, errors: ['Question is required'] };
  }

  const trimmedQuestion = question.trim();

  // Check minimum length
  if (trimmedQuestion.length < MIN_QUESTION_LENGTH) {
    errors.push(`Question must be at least ${MIN_QUESTION_LENGTH} characters`);
  }

  // Check maximum length
  if (trimmedQuestion.length > MAX_QUESTION_LENGTH) {
    errors.push(`Question exceeds maximum length of ${MAX_QUESTION_LENGTH} characters`);
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// =================================
// Document ID Validation
// =================================

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function validateDocumentId(documentId: string): ValidationResult {
  const errors: string[] = [];

  if (!documentId || documentId.trim() === '') {
    return { isValid: false, errors: ['Document ID is required'] };
  }

  if (!UUID_PATTERN.test(documentId.trim())) {
    errors.push('Invalid document ID format');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// =================================
// Sanitization
// =================================

export function sanitizeString(text: string, maxLength: number = 1000): string {
  if (!text) return '';

  // Trim whitespace
  let sanitized = text.trim();

  // Remove null bytes
  sanitized = sanitized.replace(/\0/g, '');

  // Limit length
  if (sanitized.length > maxLength) {
    sanitized = sanitized.substring(0, maxLength);
  }

  return sanitized;
}

// =================================
// Form Field Helpers
// =================================

export function getFileErrorMessage(file: File | null): string | null {
  if (!file) return null;

  const result = validateFile(file);
  if (!result.isValid) {
    return result.errors[0];
  }
  return null;
}

export function getUrlErrorMessage(url: string): string | null {
  if (!url) return null;

  const result = validateUrl(url);
  if (!result.isValid) {
    return result.errors[0];
  }
  return null;
}

export function getQuestionErrorMessage(question: string): string | null {
  if (!question) return null;

  const result = validateQuestion(question);
  if (!result.isValid) {
    return result.errors[0];
  }
  return null;
}

