/**
 * Custom hook for chat session management
 */
import { useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import { sessionAPI, messageAPI } from "../services/api";

export const useChat = (userId) => {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const skipNextAssistantRef = useRef(false);

  /**
   * Load user sessions
   */
  const loadSessions = useCallback(async () => {
    try {
      const data = await sessionAPI.getUserSessions(userId);
      setSessions(data || []);
    } catch (error) {
      console.error("Error loading sessions:", error);
      toast.error("Failed to load sessions");
    }
  }, [userId]);

  /**
   * Create new session
   */
  const createSession = useCallback(async (language = "english") => {
    try {
      const session = await sessionAPI.create(userId, language);
      setCurrentSession(session);
      setMessages([]);
      await loadSessions();
      toast.success("New chat session started");
      return session;
    } catch (error) {
      console.error("Error creating session:", error);
      toast.error("Failed to create new session");
      return null;
    }
  }, [userId, loadSessions]);

  /**
   * Load existing session
   */
  const loadSession = useCallback(async (sessionId) => {
    try {
      setIsLoading(true);
      const [session, sessionMessages] = await Promise.all([
        sessionAPI.get(sessionId),
        messageAPI.getMessages(sessionId),
      ]);
      setCurrentSession(session);
      setMessages(sessionMessages || []);
      return session;
    } catch (error) {
      console.error("Error loading session:", error);
      toast.error("Failed to load session");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Delete session
   */
  const deleteSession = useCallback(async (sessionId) => {
    try {
      await sessionAPI.delete(sessionId);
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      await loadSessions();
      toast.success("Session deleted");
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete session");
    }
  }, [currentSession, loadSessions]);

  /**
   * Send message (fallback for non-WebSocket)
   */
  const sendMessage = useCallback(async (message, language) => {
    if (!currentSession?.id) return null;

    try {
      const response = await messageAPI.send(
        currentSession.id,
        message,
        language
      );
      return response;
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
      return null;
    }
  }, [currentSession]);

  /**
   * Upload file
   */
  const uploadFile = useCallback(async (file, message, language) => {
    if (!currentSession?.id) {
      toast.error("Please start a new session first");
      return null;
    }

    try {
      setIsLoading(true);
      const response = await messageAPI.uploadFile(
        currentSession.id,
        file,
        message,
        language
      );
      toast.success("File analyzed successfully");
      return response;
    } catch (error) {
      console.error("Error uploading file:", error);
      const is429 = error.response?.status === 429;
      toast.error(is429 ? "Rate limit reached. Please wait." : "Failed to analyze file");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [currentSession]);

  /**
   * Add message to local state
   */
  const addMessage = useCallback((message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  /**
   * Clear messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    currentSession,
    messages,
    sessions,
    isLoading,
    skipNextAssistantRef,
    setMessages,
    setCurrentSession,
    loadSessions,
    createSession,
    loadSession,
    deleteSession,
    sendMessage,
    uploadFile,
    addMessage,
    clearMessages,
  };
};
