/**
 * Custom hook for WebSocket management
 */
import { useEffect, useRef, useCallback } from "react";
import { createWebSocket } from "../services/api";

export const useWebSocket = (sessionId, onMessage) => {
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!sessionId) return;

    try {
      const socket = createWebSocket(sessionId);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log("WebSocket connected");
      };

      socket.onmessage = (event) => {
        const text = typeof event.data === "string" ? event.data : "";
        if (onMessage) {
          onMessage(text);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      socket.onclose = () => {
        console.log("WebSocket closed");
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("Attempting to reconnect...");
          connect();
        }, 3000);
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
    }
  }, [sessionId, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socketRef.current) {
      try {
        socketRef.current.close();
      } catch (error) {
        console.error("Error closing WebSocket:", error);
      }
      socketRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(message);
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    socket: socketRef.current,
    sendMessage,
    isConnected: socketRef.current?.readyState === WebSocket.OPEN,
  };
};
