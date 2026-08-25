/**
 * ETHAN WebUI — use-chats hook
 *
 * Orchestrates chat state: conversation list, message tree, streaming.
 * All persistence and generation logic lives in ChatPipeline Core.
 * The WebUI only manages UI state (optimistic rendering, streaming buffer).
 */

import { useState, useCallback, useRef } from 'react';
import { apiFetch } from '@/lib/api/client';
import {
	sendChatMessage,
	streamChatMessage,
	getChatMessages,
	createChat as apiCreateChat,
	type ChatCompletionRequest,
	type ChatCompletionResponse,
	type ChatMessage,
} from '@/lib/api/chat';

/** Chat entry as expected by the sidebar component (Open-WebUI style). */
export interface EthChat {
	id: string;
	title: string;
	pinned: boolean;
	archived: boolean;
	created_at: string;
	updated_at: string;
}

/** Message entry as expected by the assistant page (Open-WebUI style). */
export interface EthMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	created_at: string;
	parent_id?: string | null;
	children_ids?: string[];
	status?: string;
	done?: boolean;
	metadata?: Record<string, unknown>;
}

export interface UseChatsState {
	chats: EthChat[];
	pinnedChats: EthChat[];
	regularChats: EthChat[];
	currentChatId: string | null;
	messages: EthMessage[];
	isLoading: boolean;
	isStreaming: boolean;
	error: string | null;
}

export interface UseChatsActions {
	loadChats: () => Promise<void>;
	loadChat: (chatId: string) => Promise<void>;
	selectChat: (chatId: string) => void;
	createChat: (title?: string) => Promise<EthChat>;
	deleteChat: (chatId: string) => Promise<void>;
	renameChat: (chatId: string, title: string) => Promise<void>;
	togglePin: (chatId: string, currentPinned: boolean) => Promise<void>;
	addMessage: (chatId: string, role: string, content: string) => Promise<void>;
	sendMessage: (request: ChatCompletionRequest) => Promise<void>;
	sendMessageStream: (request: ChatCompletionRequest) => AsyncGenerator<Record<string, unknown>>;
	/** Stoppe la génération en cours (AbortController sur le flux SSE). */
	stopGeneration: () => void;
	clearError: () => void;
}

export function useChats(): UseChatsState & UseChatsActions {
	const [chats, setChats] = useState<EthChat[]>([]);
	const [currentChatId, setCurrentChatId] = useState<string | null>(null);
	const [messages, setMessages] = useState<EthMessage[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [isStreaming, setIsStreaming] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const streamingBufferRef = useRef<string>('');
	/** Contrôleur du flux en cours — permet l'arrêt réel de la génération. */
	const abortRef = useRef<AbortController | null>(null);

	const pinnedChats = chats.filter((c) => c.pinned && !c.archived);
	const regularChats = chats.filter((c) => !c.pinned && !c.archived);

	const loadChats = useCallback(async () => {
		try {
			// ChatStore Core (/chats) est la source de vérité des conversations.
			const records = await apiFetch<Array<Record<string, unknown>>>('/chats');
			const mapped: EthChat[] = (records || []).map((r) => ({
				id: String(r.id || ''),
				title: String(r.title || 'Conversation'),
				pinned: Boolean(r.pinned),
				archived: Boolean(r.archived),
				created_at: String(r.created_at || new Date().toISOString()),
				updated_at: String(r.updated_at || r.created_at || new Date().toISOString()),
			}));
			setChats(mapped);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to load chats');
		}
	}, []);

	const selectChat = useCallback((chatId: string) => {
		setCurrentChatId(chatId);
	}, []);

	const loadChat = useCallback(async (chatId: string) => {
		setCurrentChatId(chatId);
		setIsLoading(true);
		setError(null);
		try {
			const msgs = await getChatMessages(chatId);
			setMessages(msgs as EthMessage[]);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to load chat');
		} finally {
			setIsLoading(false);
		}
	}, []);

	const createChat = useCallback(async (title: string = 'Nouvelle conversation'): Promise<EthChat> => {
		try {
			const chat = await apiCreateChat(title);
			const ethChat: EthChat = {
				id: chat.id,
				title: chat.title,
				pinned: false,
				archived: false,
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString(),
			};
			setChats((prev) => [ethChat, ...prev]);
			setCurrentChatId(chat.id);
			setMessages([]);
			return ethChat;
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to create chat');
			throw err;
		}
	}, []);

	const deleteChat = useCallback(async (chatId: string) => {
		try {
			await apiFetch<{ status: string }>(`/chats/${chatId}`, { method: 'DELETE' });
			setChats((prev) => prev.filter((c) => c.id !== chatId));
			if (currentChatId === chatId) {
				setCurrentChatId(null);
				setMessages([]);
			}
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to delete chat');
		}
	}, [currentChatId]);

	/** Renomme une conversation (PUT /chats/{id} — ChatStore Core). */
	const renameChat = useCallback(async (chatId: string, title: string) => {
		const trimmed = title.trim();
		if (!trimmed) return;
		// Mise à jour optimiste, puis persistance Core.
		setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, title: trimmed } : c)));
		try {
			await apiFetch<EthChat>(`/chats/${chatId}`, {
				method: 'PUT',
				body: JSON.stringify({ title: trimmed }),
			});
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to rename chat');
			// Rollback en cas d'échec : on recharge l'état Core.
			loadChats();
		}
	}, [loadChats]);

	const togglePin = useCallback(async (chatId: string, currentPinned: boolean) => {
		try {
			await apiFetch<EthChat>(`/chats/${chatId}`, {
				method: 'PUT',
				body: JSON.stringify({ pinned: !currentPinned }),
			});
			setChats((prev) =>
				prev.map((c) =>
					c.id === chatId ? { ...c, pinned: !currentPinned } : c,
				),
			);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to toggle pin');
		}
	}, []);

	const addMessage = useCallback(async (chatId: string, role: string, content: string) => {
		try {
			await apiFetch<Record<string, unknown>>(`/chats/${chatId}/messages`, {
				method: 'POST',
				body: JSON.stringify({ role, content }),
			});
			// Recharger les messages pour refléter l'arbre Core.
			const msgs = await getChatMessages(chatId);
			setMessages(msgs as EthMessage[]);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to add message');
		}
	}, []);

	const sendMessage = useCallback(async (request: ChatCompletionRequest) => {
		setIsLoading(true);
		setError(null);

		// Optimistically add the user message
		const userMessage: EthMessage = {
			id: `temp-${Date.now()}`,
			role: 'user',
			content: request.message,
			created_at: new Date().toISOString(),
		};
		setMessages((prev) => [...prev, userMessage]);

		try {
			const response = await sendChatMessage(request);
			const assistantMessage: EthMessage = {
				id: response.id,
				role: 'assistant',
				content: response.message,
				created_at: response.timestamp,
				metadata: response.metadata,
			};
			setMessages((prev) => [...prev, assistantMessage]);
			setCurrentChatId(response.chat_id);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to send message');
		} finally {
			setIsLoading(false);
		}
	}, []);

	const sendMessageStream = useCallback(async function* (
		request: ChatCompletionRequest,
	): AsyncGenerator<Record<string, unknown>> {
		setIsStreaming(true);
		setError(null);

		// Contrôleur d'arrêt : stopGeneration() avorte le fetch SSE sous-jacent.
		const controller = new AbortController();
		abortRef.current = controller;

		// Optimistically add the user message
		const userMessage: EthMessage = {
			id: `temp-${Date.now()}`,
			role: 'user',
			content: request.message,
			created_at: new Date().toISOString(),
		};
		setMessages((prev) => [...prev, userMessage]);

		// Placeholder for the streaming assistant message
		const assistantId = `temp-assistant-${Date.now()}`;
		const assistantMessage: EthMessage = {
			id: assistantId,
			role: 'assistant',
			content: '',
			created_at: new Date().toISOString(),
			status: 'pending',
			done: false,
		};
		setMessages((prev) => [...prev, assistantMessage]);

		streamingBufferRef.current = '';

		/** Met à jour le message assistant en cours de streaming. */
		const patchAssistant = (patch: Partial<EthMessage>) =>
			setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)));

		try {
			for await (const event of streamChatMessage(request, controller.signal)) {
				const eventType = event.type as string;

				if (eventType === 'content') {
					const chunk = event.content as string;
					streamingBufferRef.current += chunk;
					patchAssistant({ content: streamingBufferRef.current });
					yield event;
				} else if (eventType === 'done') {
					const messageId = (event.message_id as string) || assistantId;
					patchAssistant({ status: 'done', done: true, id: messageId });
					setCurrentChatId(event.chat_id as string);
					yield event;
				} else if (eventType === 'error') {
					const message = String(event.error ?? 'Generation failed');
					setError(message);
					patchAssistant({
						status: 'error',
						done: true,
						content: streamingBufferRef.current || '',
						metadata: { error: message },
					});
					yield event;
				}
			}
			// Flux terminé sans événement done (connexion coupée) : figer l'état.
			patchAssistant({ status: 'done', done: true });
		} catch (err) {
			if (controller.signal.aborted || (err instanceof DOMException && err.name === 'AbortError')) {
				// Arrêt demandé par l'utilisateur : contenu partiel conservé,
				// pas d'erreur globale affichée.
				patchAssistant({ status: 'stopped', done: true });
			} else {
				const message = err instanceof Error ? err.message : 'Streaming failed';
				setError(message);
				patchAssistant({
					status: 'error',
					done: true,
					metadata: { error: message },
				});
			}
		} finally {
			abortRef.current = null;
			setIsStreaming(false);
		}
	}, []);

	/**
	 * Arrêt réel de la génération : avorte le flux SSE. Le contenu déjà
	 * reçu est conservé et marqué « stopped » (voir sendMessageStream).
	 */
	const stopGeneration = useCallback(() => {
		abortRef.current?.abort();
	}, []);

	const clearError = useCallback(() => setError(null), []);

	return {
		chats,
		pinnedChats,
		regularChats,
		currentChatId,
		messages,
		isLoading,
		isStreaming,
		error,
		loadChats,
		loadChat,
		selectChat,
		createChat,
		deleteChat,
		renameChat,
		togglePin,
		addMessage,
		sendMessage,
		sendMessageStream,
		stopGeneration,
		clearError,
	};
}