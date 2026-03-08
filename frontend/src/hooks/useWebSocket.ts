import { useCallback, useEffect, useRef, useState } from 'react';
import { WebSocketMessage, Language } from '@/types';

interface UseWebSocketOptions {
  sessionId: string;
  language: Language;
  onMessage?: (message: WebSocketMessage) => void;
  onTranscript?: (text: string) => void;
  onResponse?: (text: string, audioUrl?: string) => void;
  onError?: (error: string) => void;
}

export function useWebSocket({
  sessionId,
  language,
  onMessage,
  onTranscript,
  onResponse,
  onError,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/voice/${sessionId}?language=${language}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(message);

          switch (message.type) {
            case 'transcript':
              onTranscript?.(message.data as string);
              break;
            case 'response':
              const responseData = message.data as { text: string; audioUrl?: string };
              onResponse?.(responseData.text, responseData.audioUrl);
              setIsProcessing(false);
              break;
            case 'error':
              onError?.(message.data as string);
              setIsProcessing(false);
              break;
            case 'status':
              if (message.data === 'processing') {
                setIsProcessing(true);
              }
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
        // Attempt reconnection after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.('Connection error. Please try again.');
      };
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
      onError?.('Failed to connect. Please refresh the page.');
    }
  }, [sessionId, language, onMessage, onTranscript, onResponse, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendAudio = useCallback((audioData: ArrayBuffer | Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData);
    }
  }, []);

  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', data: text }));
      setIsProcessing(true);
    }
  }, []);

  const sendLanguageChange = useCallback((newLanguage: Language) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'language', data: newLanguage }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    isProcessing,
    sendAudio,
    sendText,
    sendLanguageChange,
    connect,
    disconnect,
  };
}
