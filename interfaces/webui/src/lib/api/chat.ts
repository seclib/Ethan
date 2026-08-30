/**
 * ETHAN WebUI — Chat API service
 *
 * Maps Open-WebUI chat patterns to ETHAN API endpoints:
 *   OWUI: POST /api/v1/chat/completions
 *   ETHAN: POST /v1/chat/completions  (non-streaming)
 *   ETHAN: POST /v1/chat/completions/stream  (SSE streaming)
 *
 * Conversation persistence lives in ChatStore Core (/chats).
 */

import { apiFetch, streamEvents, ApiError } from '@/lib/api/client';

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	created_at?: string;
	parent_id?: string | null;
	children_ids?: string[];
	status?: string;
	done?: boolean;
	metadata?: Record<string, unknown>;
}

export interface ChatCompletionRequest {
	message: string;
	chat_id?: string;
	user_id?: string;
	provider_id?: string;
	model?: string;
	parent_id?: string;
	skill_ids?: string[];
	collection_ids?: string[];
	tool_ids?: string[];
	file_ids?: string[];
	/** Routage Chat → Agent (résolu par le Core). */
	agent_id?: string;
	metadata?: Record<string, unknown>;
	knowledge_ids?: string[];
}

export interface ChatCompletionResponse {
	id: string;
	chat_id: string;
	message: string;
	role: string;
	timestamp: string;
	metadata: {
		provider?: string;
		model?: string;
		usage?: Record<string, unknown>;
	};
}

export interface ChatHistoryEntry {
	id: string;
	role: string;
	content: string;
	created_at: string;
	chat_id: string;
}

/**
 * Send a chat message (non-streaming).
 * Maps to POST /v1/chat/completions
 */
export async function sendChatMessage(
	request: ChatCompletionRequest,
): Promise<ChatCompletionResponse> {
	return apiFetch<ChatCompletionResponse>('/v1/chat/completions', {
		method: 'POST',
		body: JSON.stringify(request),
	});
}

/**
 * Send a chat message with SSE streaming.
 * Maps to POST /v1/chat/completions/stream
 *
 * @param signal Optional AbortSignal to stop generation mid-stream.
 *
 * Yields events: { type: 'content', content: string, chat_id: string }
 *                { type: 'done', chat_id: string, message_id: string }
 *                { type: 'error', error: string }
 */
export async function* streamChatMessage(
	request: ChatCompletionRequest,
	signal?: AbortSignal,
): AsyncGenerator<Record<string, unknown>, void, unknown> {
	yield* streamEvents(
		'/v1/chat/completions/stream',
		request as unknown as Record<string, unknown>,
		signal,
	);
}

/**
 * Fetch chat history (all conversations).
 * Maps to GET /v1/chat/history
 */
export async function getChatHistory(
	limit: number = 50,
): Promise<ChatHistoryEntry[]> {
	return apiFetch<ChatHistoryEntry[]>('/v1/chat/history', {
		method: 'GET',
	});
}

/**
 * Fetch messages for a specific chat.
 * Maps to GET /chats/{chat_id}/messages
 */
export async function getChatMessages(
	chatId: string,
): Promise<ChatMessage[]> {
	return apiFetch<ChatMessage[]>(`/chats/${chatId}/messages`, {
		method: 'GET',
	});
}

/**
 * Create a new chat.
 * Maps to POST /chats
 */
export async function createChat(
	title: string,
	userId: string = 'anonymous',
): Promise<{ id: string; title: string; user_id: string }> {
	return apiFetch<{ id: string; title: string; user_id: string }>('/chats', {
		method: 'POST',
		body: JSON.stringify({ title, user_id: userId }),
	});
}

export { ApiError };