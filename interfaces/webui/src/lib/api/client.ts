/**
 * ETHAN WebUI — API client
 *
 * Thin HTTP gateway over ETHAN Core.  All business logic lives in core/;
 * this client only serialises requests and deserialises responses.
 *
 * Endpoints are mapped from Open-WebUI patterns to ETHAN API (/v1/*).
 * See docs/architecture/OPENWEBUI_ETHAN_MAPPING.md for the full mapping.
 */

const API_BASE = process.env.NEXT_PUBLIC_ETHAN_API_URL || '/api';

export interface ApiResponse<T = unknown> {
	data: T;
	status: number;
}

export class ApiError extends Error {
	constructor(
		message: string,
		public status: number,
		public body?: unknown,
	) {
		super(message);
		this.name = 'ApiError';
	}
}

/**
 * Base fetch wrapper with JWT cookie support.
 * Credentials are sent automatically (HttpOnly cookie).
 */
export async function apiFetch<T = unknown>(
	path: string,
	options: RequestInit = {},
): Promise<T> {
	const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
	const response = await fetch(url, {
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json',
			...options.headers,
		},
		...options,
	});

	if (!response.ok) {
		let body: unknown;
		try {
			body = await response.json();
		} catch {
			body = await response.text();
		}
		const message =
			(body as { detail?: string })?.detail ||
			`HTTP ${response.status}`;
		throw new ApiError(message, response.status, body);
	}

	// Handle empty responses (e.g. 204 No Content)
	if (response.status === 204 || response.headers.get('content-length') === '0') {
		return undefined as T;
	}

	return response.json() as Promise<T>;
}

/**
 * SSE streaming helper for chat completions.
 *
 * @param signal Optional AbortSignal — allows the UI to stop generation
 *               mid-stream (the reader throws AbortError on abort).
 */
export async function* streamEvents(
	path: string,
	body: Record<string, unknown>,
	signal?: AbortSignal,
): AsyncGenerator<Record<string, unknown>, void, unknown> {
	const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
	const response = await fetch(url, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
		signal,
	});

	if (!response.ok) {
		throw new ApiError(`HTTP ${response.status}`, response.status);
	}

	const reader = response.body?.getReader();
	if (!reader) {
		throw new ApiError('No response body', 500);
	}

	const decoder = new TextDecoder();
	let buffer = '';

	try {
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });

			const lines = buffer.split('\n');
			buffer = lines.pop() || '';

			for (const line of lines) {
				const trimmed = line.trim();
				if (trimmed.startsWith('data: ')) {
					const json = trimmed.slice(6);
					try {
						yield JSON.parse(json);
					} catch {
						// Skip malformed SSE lines
					}
				}
			}
		}
	} finally {
		reader.releaseLock();
	}
}
