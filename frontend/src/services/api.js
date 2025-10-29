/**
 * API service for MedIntel backend communication
 */
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, "") || "http://localhost:8001";
const API_BASE = `${BACKEND_URL}/api`;

/**
 * API client configuration
 */
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Session API
 */
export const sessionAPI = {
  /**
   * Create a new chat session
   */
  create: async (userId, language = "english") => {
    const response = await apiClient.post("/chat/session", {
      user_id: userId,
      language,
    });
    return response.data;
  },

  /**
   * Get session details
   */
  get: async (sessionId) => {
    const response = await apiClient.get(`/chat/session/${sessionId}`);
    return response.data;
  },

  /**
   * Get user sessions
   */
  getUserSessions: async (userId) => {
    const response = await apiClient.get(`/chat/sessions/${userId}`);
    return response.data;
  },

  /**
   * Delete a session
   */
  delete: async (sessionId) => {
    const response = await apiClient.delete(`/chat/session/${sessionId}`);
    return response.data;
  },
};

/**
 * Message API
 */
export const messageAPI = {
  /**
   * Send a text message
   */
  send: async (sessionId, message, language) => {
    const response = await apiClient.post("/chat/message", {
      session_id: sessionId,
      message,
      language,
    });
    return response.data;
  },

  /**
   * Get session messages
   */
  getMessages: async (sessionId) => {
    const response = await apiClient.get(`/chat/session/${sessionId}/messages`);
    return response.data;
  },

  /**
   * Upload and analyze file
   */
  uploadFile: async (sessionId, file, message, language) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);
    formData.append("message", message);
    formData.append("language", language);

    const response = await apiClient.post("/chat/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};

/**
 * Language API
 */
export const languageAPI = {
  /**
   * Change session language
   */
  change: async (sessionId, language) => {
    const response = await apiClient.post(`/chat/language/${sessionId}`, null, {
      params: { language },
    });
    return response.data;
  },
};

/**
 * WebSocket connection
 */
export const createWebSocket = (sessionId) => {
  const wsUrl = `${BACKEND_URL.replace("http", "ws")}/ws/${sessionId}`;
  return new WebSocket(wsUrl);
};

export default {
  sessionAPI,
  messageAPI,
  languageAPI,
  createWebSocket,
};
