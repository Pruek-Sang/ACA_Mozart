
// src/hooks/useChat.ts
/**
 * Custom hook for managing chat state
 * Version 3: Integrated with Floor Plan data + Chat Memory
 */

import { useState, useCallback, useEffect } from 'react';
import { API_CONFIG } from '../config/api.config';
import type { Message, ChatState } from '../types/gateway';
import { sendMessage, extractDisplayMessage } from '../services/gateway';
import { saveMessages, loadMessages, clearMessages as clearStoredMessages } from '../services/chatMemory';
import type { RoomData } from '../features/floorplan/layout.logic';

// Helper function to extract room data from the raw response
const extractRoomData = (data: Record<string, unknown>): RoomData[] => {
    // Logic to find room data in the complex nested object from Gateway
    const result = data?.result as Record<string, unknown> | undefined;
    const projectReq = result?.project_requirements as Record<string, unknown> | undefined;
    const topLevelProjectReq = data?.project_requirements as Record<string, unknown> | undefined;

    if (projectReq?.rooms) {
        return projectReq.rooms as RoomData[];
    }
    if (topLevelProjectReq?.rooms) {
        return topLevelProjectReq.rooms as RoomData[];
    }
    if (data?.rooms) {
        return data.rooms as RoomData[];
    }
    return [];
};

export function useChat() {
    const [state, setState] = useState<ChatState>(() => ({
        messages: loadMessages(), // **[NEW]** Load saved messages on init
        isTyping: false,
        apiKey: localStorage.getItem(API_CONFIG.STORAGE_KEY) || '',
        isAuthenticated: !!localStorage.getItem(API_CONFIG.STORAGE_KEY),
    }));

    // State for the Floor Plan Visualizer
    const [rooms, setRooms] = useState<RoomData[]>([]);

    // **[NEW]** Save messages to localStorage whenever they change
    useEffect(() => {
        if (state.messages.length > 0) {
            saveMessages(state.messages);
        }
    }, [state.messages]);

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

            addMessage({ role: 'user', content: input });
            setState((prev) => ({ ...prev, isTyping: true }));

            try {
                const response = await sendMessage(input, state.apiKey);

                const displayContent = extractDisplayMessage(response.data);

                // Extract room data for the visualizer
                const roomData = extractRoomData(response.data);
                if (roomData.length > 0) {
                    setRooms(roomData);
                }

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
        setRooms([]);
        clearStoredMessages(); // **[NEW]** Clear localStorage as well
    }, []);

    return {
        // Existing state and functions
        messages: state.messages,
        isTyping: state.isTyping,
        apiKey: state.apiKey,
        isAuthenticated: state.isAuthenticated,
        setApiKey,
        clearApiKey,
        send,
        clearMessages,

        // State for the Floor Plan
        rooms,
    };
}
