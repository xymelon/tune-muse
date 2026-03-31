/**
 * API client service.
 * Encapsulates all communication with the backend REST API using the native fetch API.
 * All errors are converted to user-friendly messages without exposing technical details.
 */

import type {
  AnalyzeRequest,
  AnalyzeResponse,
  SessionListResponse,
  SessionDetailResponse,
  AuthRequest,
  AuthResponse,
  ApiError,
} from '../types'

const API_BASE = '/api/v1'

/**
 * Retrieve the authentication token stored in localStorage.
 *
 * @returns JWT token string or null
 */
function getToken(): string | null {
  return localStorage.getItem('tunemuse_token')
}

/**
 * Build request headers with Content-Type and optional Authorization.
 *
 * @param includeAuth - Whether to include the Bearer token
 * @param contentType - Content-Type header value, defaults to JSON
 * @returns Headers object
 */
function buildHeaders(includeAuth = false, contentType?: string): HeadersInit {
  const headers: Record<string, string> = {}
  if (contentType) {
    headers['Content-Type'] = contentType
  }
  if (includeAuth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }
  return headers
}

/**
 * Unified error handling: converts HTTP error responses to user-friendly error messages.
 *
 * @param response - The Response object from the fetch API
 * @throws Error with a user-friendly error message
 */
async function handleErrorResponse(response: Response): Promise<never> {
  let errorData: ApiError
  try {
    errorData = await response.json()
  } catch {
    throw new Error('An unexpected error occurred. Please try again.')
  }
  throw new Error(errorData.message || 'An unexpected error occurred.')
}

/**
 * Submit client-extracted audio features for analysis and recommendations.
 * Corresponds to POST /api/v1/analyze endpoint.
 *
 * @param request - Analysis request containing source_type, duration, and features
 * @returns Analysis response (vocal profile + recommendations)
 *
 * @example
 *   const result = await submitFeatures({
 *     source_type: 'recording',
 *     duration_seconds: 28.5,
 *     features: extractedFeatures,
 *   })
 */
export async function submitFeatures(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: buildHeaders(true, 'application/json'),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    await handleErrorResponse(response)
  }

  return response.json()
}

/**
 * Upload an audio file for server-side feature extraction and analysis.
 * Corresponds to POST /api/v1/upload endpoint.
 *
 * @param file - Audio file (MP3, WAV, M4A, OGG), max 10 MB
 * @returns Analysis response (same structure as submitFeatures)
 *
 * @example
 *   const result = await uploadAudio(fileInput.files[0])
 */
export async function uploadAudio(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: buildHeaders(true),
    body: formData,
  })

  if (!response.ok) {
    await handleErrorResponse(response)
  }

  return response.json()
}

/**
 * Retrieve the authenticated user's analysis history list.
 * Corresponds to GET /api/v1/sessions endpoint.
 *
 * @param limit - Number of items per page (default 20)
 * @param offset - Pagination offset (default 0)
 * @param sort - Sort direction "asc" or "desc" (default "desc")
 * @returns List of analysis sessions and total count
 */
export async function getSessionHistory(
  limit = 20,
  offset = 0,
  sort: 'asc' | 'desc' = 'desc',
): Promise<SessionListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    sort,
  })

  const response = await fetch(`${API_BASE}/sessions?${params}`, {
    headers: buildHeaders(true),
  })

  if (!response.ok) {
    await handleErrorResponse(response)
  }

  return response.json()
}

/**
 * Retrieve full details of a specific analysis session (including vocal profile and recommendations).
 * Corresponds to GET /api/v1/sessions/:id endpoint.
 *
 * @param sessionId - UUID of the analysis session
 * @returns Complete session details
 */
export async function getSessionDetail(sessionId: string): Promise<SessionDetailResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    headers: buildHeaders(true),
  })

  if (!response.ok) {
    await handleErrorResponse(response)
  }

  return response.json()
}

/**
 * Register a new user account.
 * Corresponds to POST /api/v1/auth/register endpoint.
 *
 * @param data - Registration info (email, password, optional display_name and locale)
 * @returns User info and JWT token
 */
export async function register(data: AuthRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: buildHeaders(false, 'application/json'),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    await handleErrorResponse(response)
  }

  const result: AuthResponse = await response.json()
  localStorage.setItem('tunemuse_token', result.token)
  return result
}

/**
 * Login to an existing account.
 * Corresponds to POST /api/v1/auth/login endpoint.
 *
 * @param email - User email
 * @param password - User password
 * @returns User info and JWT token
 */
export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: buildHeaders(false, 'application/json'),
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    await handleErrorResponse(response)
  }

  const result: AuthResponse = await response.json()
  localStorage.setItem('tunemuse_token', result.token)
  return result
}

/**
 * Logout the current user and clear the local token.
 */
export function logout(): void {
  localStorage.removeItem('tunemuse_token')
}
