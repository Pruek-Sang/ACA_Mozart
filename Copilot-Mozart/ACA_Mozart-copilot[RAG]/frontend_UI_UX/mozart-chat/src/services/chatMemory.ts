// src/services/chatMemory.ts
/**
 * Chat Memory Service
 * Handles saving/loading chat history to localStorage (client-side)
 * Data can be exported to JSON files manually or synced with backend later
 */

import type { Message } from '../types/gateway';

const STORAGE_KEY = 'aca_mozart_chat_history';
const MAX_MESSAGES = 100; // Limit to prevent localStorage overflow

export interface ChatSession {
    id: string;
    createdAt: string;
    updatedAt: string;
    messages: Message[];
}

/**
 * Save messages to localStorage
 */
export function saveMessages(messages: Message[]): void {
    try {
        const session: ChatSession = {
            id: 'default',
            createdAt: localStorage.getItem(`${STORAGE_KEY}_created`) || new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            messages: messages.slice(-MAX_MESSAGES), // Keep only last N messages
        };

        localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
        localStorage.setItem(`${STORAGE_KEY}_created`, session.createdAt);
    } catch (error) {
        console.error('[ChatMemory] Failed to save messages:', error);
    }
}

/**
 * Load messages from localStorage
 */
export function loadMessages(): Message[] {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return [];

        const session: ChatSession = JSON.parse(stored);

        // Restore Date objects (JSON.parse converts dates to strings)
        return session.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
        }));
    } catch (error) {
        console.error('[ChatMemory] Failed to load messages:', error);
        return [];
    }
}

/**
 * Clear all saved messages
 */
export function clearMessages(): void {
    try {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(`${STORAGE_KEY}_created`);
    } catch (error) {
        console.error('[ChatMemory] Failed to clear messages:', error);
    }
}

/**
 * Export chat history as JSON string (for file download)
 */
export function exportAsJSON(): string {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored || JSON.stringify({ messages: [] });
}
