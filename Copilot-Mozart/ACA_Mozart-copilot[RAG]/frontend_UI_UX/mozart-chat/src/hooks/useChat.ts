/**
 * Custom hook for managing chat state
 */

import { useState, useCallback } from 'react';
import { API_CONFIG } from '../config/api.config';
import type { Message, ChatState } from '../types/gateway';
import { sendMessage, extractDisplayMessage, hasStructuredData } from '../services/gateway';

export function useChat() {
    const [state, setState] = useState<ChatState>(() => ({
        messages: [],
        isTyping: false,
        apiKey: localStorage.getItem(API_CONFIG.STORAGE_KEY) || '',
        isAuthenticated: !!localStorage.getItem(API_CONFIG.STORAGE_KEY),
    }));

    const [jsonData, setJsonData] = useState<Record<string, unknown> | null>(null);

    const setApiKey = useCallback((key: string) => {
        localStorage.setItem(API_CONFIG.STORAGE_KEY, key);
        setState((prev) => ({ ...prev, apiKey: key, isAuthenticated: true }));
    }, []);

    const clearApiKey = useCallback(() => {
        localStorage.removeItem(API_CONFIG.STORAGE_KEY);
        setState((prev) => ({ ...prev, apiKey: '', isAuthenticated: false }));
    }, []);

    const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
        const newMessage: Message = {
            ...message,
            id: crypto.randomUUID(),
            timestamp: new Date(),
        };
        setState((prev) => ({
            ...prev,
            messages: [...prev.messages, newMessage],
        }));
        return newMessage;
    }, []);

    const send = useCallback(
        async (input: string) => {
            if (!input.trim() || state.isTyping) return;

            // Add user message
            addMessage({ role: 'user', content: input });

            // Set typing state
            setState((prev) => ({ ...prev, isTyping: true }));

            try {
                const response = await sendMessage(input, state.apiKey);

                // Extract display message
                const displayContent = extractDisplayMessage(response.data);

                // Check for structured data (for JSON Editor)
                if (hasStructuredData(response.data)) {
                    setJsonData(response.data);
                }

                // Add bot message
                addMessage({
                    role: 'bot',
                    content: displayContent,
                    mode: response.mode,
                    rawData: response.data,
                });
            } catch (error) {
                const errorMessage =
                    error instanceof Error ? error.message : 'Unknown error occurred';
                addMessage({
                    role: 'bot',
                    content: `⚠️ Error: ${errorMessage}\n(Make sure Gateway is running at ${API_CONFIG.GATEWAY_URL})`,
                    mode: 'SYSTEM',
                });
            } finally {
                setState((prev) => ({ ...prev, isTyping: false }));
            }
        },
        [state.apiKey, state.isTyping, addMessage]
    );

    const clearMessages = useCallback(() => {
        setState((prev) => ({ ...prev, messages: [] }));
        setJsonData(null);
    }, []);

    return {
        messages: state.messages,
        isTyping: state.isTyping,
        apiKey: state.apiKey,
        isAuthenticated: state.isAuthenticated,
        jsonData,
        setApiKey,
        clearApiKey,
        send,
        clearMessages,
        setJsonData,
    };
}
