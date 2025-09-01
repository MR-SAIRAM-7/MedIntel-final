import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { Toaster, toast } from "sonner";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Avatar, AvatarFallback } from "./components/ui/avatar";
import {
  MessageSquare,
  Upload,
  Send,
  FileText,
  Image as ImageIcon,
  Loader2,
  Stethoscope,
  Brain,
  Shield,
  Languages,
  Trash2,
  Plus
} from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, "") || "http://localhost:8001";
const API = `${BACKEND_URL}/api`;

const SUPPORTED_LANGUAGES = [
  { code: "english", name: "English", flag: "🇺🇸" },
  { code: "spanish", name: "Español", flag: "🇪🇸" },
  { code: "french", name: "Français", flag: "🇫🇷" },
  { code: "german", name: "Deutsch", flag: "🇩🇪" },
  { code: "italian", name: "Italiano", flag: "🇮🇹" },
  { code: "portuguese", name: "Português", flag: "🇵🇹" },
  { code: "hindi", name: "हिंदी", flag: "🇮🇳" },
  { code: "telugu", name: "తెలుగు", flag: "🇮🇳" },
  { code: "tamil", name: "தமிழ்", flag: "🇮🇳" },
  { code: "bengali", name: "বাংলা", flag: "🇮🇳" },
  { code: "marathi", name: "मराठी", flag: "🇮🇳" },
  { code: "gujarati", name: "ગુજરાતી", flag: "🇮🇳" },
  { code: "kannada", name: "ಕನ್ನಡ", flag: "🇮🇳" },
  { code: "malayalam", name: "മലയാളം", flag: "🇮🇳" },
  { code: "punjabi", name: "ਪੰਜਾਬੀ", flag: "🇮🇳" },
  { code: "urdu", name: "اردو", flag: "🇵🇰" },
  { code: "chinese", name: "中文", flag: "🇨🇳" },
  { code: "arabic", name: "العربية", flag: "🇸🇦" },
  { code: "japanese", name: "日本語", flag: "🇯🇵" }
];

function App() {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("english");
  const [userSessions, setUserSessions] = useState([]);
  const [showLanguageSelector, setShowLanguageSelector] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const socketRef = useRef(null);
  const skipNextAssistantRef = useRef(false); // used only for language-change ack suppression

  const userIdRef = useRef(`user_${Math.random().toString(36).slice(2)}_${Date.now()}`);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadUserSessions();
    return () => {
      if (socketRef.current) {
        try {
          socketRef.current.close();
        } catch {}
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Setup websocket whenever a session is selected
  useEffect(() => {
    if (!currentSession?.id) return;

    const wsUrl = `${BACKEND_URL.replace("http", "ws")}/ws/${currentSession.id}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      // console.log("WS connected");
    };

    socket.onmessage = (event) => {
      const text = typeof event.data === "string" ? event.data : "";
      // Suppress a single incoming assistant message if we flagged it (used for language ack)
      if (skipNextAssistantRef.current) {
        skipNextAssistantRef.current = false;
        return;
      }
      const msg = {
        id: `${Date.now()}_${Math.random()}`,
        session_id: currentSession.id,
        role: "assistant",
        content: text,
        timestamp: new Date().toISOString()
      };
      setMessages((prev) => [...prev, msg]);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    socket.onclose = () => {
      // console.log("WS closed");
    };

    return () => {
      try {
        socket.close();
      } catch {}
    };
  }, [currentSession?.id]);

  const loadUserSessions = async () => {
    try {
      const response = await axios.get(`${API}/chat/sessions/${userIdRef.current}`);
      setUserSessions(response.data || []);
    } catch (err) {
      console.error("Error loading sessions:", err);
      toast.error("Failed to load sessions");
    }
  };

  const createNewSession = async () => {
    try {
      const response = await axios.post(`${API}/chat/session`, {
        user_id: userIdRef.current,
        language: selectedLanguage
      });
      setCurrentSession(response.data);
      setMessages([]);
      await loadUserSessions();
      toast.success("New chat session started");
    } catch (error) {
      console.error("Error creating session:", error);
      toast.error("Failed to create new session");
    }
  };

  const loadSession = async (sessionId) => {
    try {
      setIsLoading(true);
      const [sessionResponse, messagesResponse] = await Promise.all([
        axios.get(`${API}/chat/session/${sessionId}`),
        axios.get(`${API}/chat/session/${sessionId}/messages`)
      ]);
      setCurrentSession(sessionResponse.data);
      setMessages(messagesResponse.data || []);
      setSelectedLanguage(sessionResponse.data?.language || "english");
    } catch (error) {
      console.error("Error loading session:", error);
      toast.error("Failed to load session");
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId, e) => {
    e?.stopPropagation?.();
    try {
      await axios.delete(`${API}/chat/session/${sessionId}`);
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
        try {
          socketRef.current?.close();
        } catch {}
      }
      await loadUserSessions();
      toast.success("Session deleted");
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete session");
    }
  };

  // Sync language to backend; suppress the next WebSocket assistant message (which is the server ack)
  const syncLanguagePreference = async (langCode) => {
    if (!currentSession?.id) return;
    try {
      skipNextAssistantRef.current = true; // expect ack broadcast from server; suppress it
      await axios.post(`${API}/chat/message`, {
        session_id: currentSession.id,
        message: langCode,
        language: langCode
      });
      toast.success("Language updated");
    } catch (error) {
      skipNextAssistantRef.current = false;
      console.error("Failed to update language:", error);
      toast.error("Could not update language");
    }
  };

  // Send chat message (prefers WebSocket; falls back to REST)
  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentSession?.id) return;

    const userMsg = {
      id: `${Date.now()}_${Math.random()}`,
      session_id: currentSession.id,
      role: "user",
      content: inputMessage,
      timestamp: new Date().toISOString()
    };
    // show user message immediately
    setMessages((prev) => [...prev, userMsg]);

    try {
      // If socket open, send via WS (server will broadcast assistant response)
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(inputMessage);
      } else {
        // fallback to REST: the server will insert messages and return assistant response.
        const res = await axios.post(`${API}/chat/message`, {
          session_id: currentSession.id,
          message: inputMessage,
          language: selectedLanguage
        });

        // If websocket is open (race), we rely on WS broadcast; otherwise append assistant from REST
        const wsOpen = socketRef.current?.readyState === WebSocket.OPEN;
        if (!wsOpen) {
          if (res?.data?.assistant_message) {
            // assistant_message is an object shaped like ChatMessage dict
            const assistantObj = {
              id: res.data.assistant_message.id || `${Date.now()}_${Math.random()}`,
              session_id: currentSession.id,
              role: "assistant",
              content: res.data.assistant_message.content,
              timestamp: res.data.assistant_message.timestamp || new Date().toISOString()
            };
            setMessages((prev) => [...prev, assistantObj]);
          }
        }
      }
    } catch (error) {
      const is429 = axios.isAxiosError(error) && error.response && error.response.status === 429;
      console.error("sendMessage error:", error);
      toast.error(is429 ? "Rate limit reached. Please wait a bit." : "Failed to send message");
    } finally {
      setInputMessage("");
    }
  };

  // File upload handler: append a local user message immediately (so user sees upload), then rely on WS for assistant if available
  const handleFileUpload = async (file) => {
    if (!currentSession?.id) {
      toast.error("Please start a new session first");
      return;
    }

    // Local user message describing the upload
    const localUserMsg = {
      id: `${Date.now()}_${Math.random()}`,
      session_id: currentSession.id,
      role: "user",
      content: `Uploaded file: ${file.name}`,
      file_info: { filename: file.name, content_type: file.type, size: file.size },
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, localUserMsg]);

    try {
      setIsLoading(true);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("session_id", currentSession.id);
      formData.append(
        "message",
        `Please analyze this ${file.type.startsWith("image/") ? "medical image" : "medical report"}.`
      );
      formData.append("language", selectedLanguage);

      const response = await axios.post(`${API}/chat/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      // If WS is open, server will broadcast assistant response to us.
      // So only append assistant_message from REST if WS is not open.
      const wsOpen = socketRef.current?.readyState === WebSocket.OPEN;
      if (!wsOpen) {
        const { assistant_message } = response.data || {};
        if (assistant_message) {
          const assistantObj = {
            id: assistant_message.id || `${Date.now()}_${Math.random()}`,
            session_id: currentSession.id,
            role: "assistant",
            content: assistant_message.content,
            timestamp: assistant_message.timestamp || new Date().toISOString()
          };
          setMessages((prev) => [...prev, assistantObj]);
        }
      }

      toast.success("File analyzed successfully");
    } catch (error) {
      const is429 = axios.isAxiosError(error) && error.response && error.response.status === 429;
      console.error("Error uploading file:", error);
      toast.error(is429 ? "Rate limit reached. Please wait." : "Failed to analyze file");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileUpload(files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const renderMessage = (message) => {
    const isUser = message.role === "user";
    const isAssistant = message.role === "assistant";

    return (
      <div key={message.id} className={`flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : ""}`}>
        <Avatar className={`w-8 h-8 ${isAssistant ? "bg-emerald-500" : "bg-blue-500"}`}>
          <AvatarFallback className="text-white text-sm">
            {isAssistant ? <Stethoscope className="w-4 h-4" /> : "U"}
          </AvatarFallback>
        </Avatar>

        <div className={`flex flex-col max-w-[70%] ${isUser ? "items-end" : "items-start"}`}>
          <div
            className={`rounded-2xl px-4 py-3 ${
              isUser
                ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white"
                : "bg-white border border-gray-200 text-gray-800 shadow-sm"
            }`}
          >
            {message.file_info && (
              <div
                className={`flex items-center gap-2 mb-2 text-xs ${
                  isUser ? "text-blue-100" : "text-gray-500"
                }`}
              >
                {message.file_info.content_type?.startsWith("image/") ? (
                  <ImageIcon className="w-3 h-3" />
                ) : (
                  <FileText className="w-3 h-3" />
                )}
                {message.file_info.filename}
              </div>
            )}
            <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
          </div>
          <div className={`text-xs text-gray-400 mt-1 px-1 ${isUser ? "text-right" : ""}`}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  const WelcomeScreen = () => (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-2xl">
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="w-20 h-20 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Stethoscope className="w-10 h-10 text-white" />
            </div>
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
              <Brain className="w-3 h-3 text-white" />
            </div>
          </div>
        </div>

        <h1 className="text-4xl font-bold text-gray-800 mb-4 tracking-tight">
          MedIntel AI Health Assistant
        </h1>

        <p className="text-lg text-gray-600 mb-8 leading-relaxed">
          Your intelligent medical companion for analyzing reports, images, and answering health questions.
          Get professional insights in your preferred language with advanced AI technology.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="border-2 border-gray-100 hover:border-emerald-200 transition-all duration-300">
            <CardContent className="p-4 text-center">
              <FileText className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-800 mb-1">Medical Reports</h3>
              <p className="text-sm text-gray-600">
                Upload and analyze lab results, prescriptions, and medical documents
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 border-gray-100 hover:border-blue-200 transition-all duration-300">
            <CardContent className="p-4 text-center">
              <ImageIcon className="w-8 h-8 text-blue-500 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-800 mb-1">Medical Images</h3>
              <p className="text-sm text-gray-600">Analyze X-rays, MRIs, CT scans and other medical imaging</p>
            </CardContent>
          </Card>

          <Card className="border-2 border-gray-100 hover:border-purple-200 transition-all duration-300">
            <CardContent className="p-4 text-center">
              <Languages className="w-8 h-8 text-purple-500 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-800 mb-1">Multilingual Support</h3>
              <p className="text-sm text-gray-600">Get explanations in your preferred language</p>
            </CardContent>
          </Card>
        </div>

        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Shield className="w-5 h-5 text-red-500" />
            <span className="font-semibold text-red-700">Medical Disclaimer</span>
          </div>
          <p className="text-sm text-red-600 leading-relaxed">
            This AI analysis is for informational purposes only and should not replace professional medical advice,
            diagnosis, or treatment. Always consult with qualified healthcare professionals for proper medical care.
          </p>
        </div>

        <Button
          onClick={createNewSession}
          size="lg"
          className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
        >
          <Plus className="w-5 h-5 mr-2" />
          Start New Consultation
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
      <Toaster position="top-right" richColors />

      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-80 bg-white border-r border-gray-200 shadow-sm flex flex-col">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
                <Stethoscope className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-gray-800">MedIntel</h2>
                <p className="text-xs text-gray-500">AI Health Assistant</p>
              </div>
            </div>

            <Button
              onClick={createNewSession}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white rounded-xl shadow-sm"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Consultation
            </Button>
          </div>

          {/* Language Selector */}
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Language</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowLanguageSelector((v) => !v)}
              >
                <Languages className="w-4 h-4" />
              </Button>
            </div>
            {showLanguageSelector && (
              <div className="grid grid-cols-2 gap-1 max-h-40 overflow-y-auto">
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <Button
                    key={lang.code}
                    variant={selectedLanguage === lang.code ? "secondary" : "ghost"}
                    size="sm"
                    className="justify-start text-xs p-2"
                    onClick={async () => {
                      setSelectedLanguage(lang.code);
                      setShowLanguageSelector(false);
                      await syncLanguagePreference(lang.code);
                    }}
                  >
                    <span className="mr-1">{lang.flag}</span>
                    {lang.name}
                  </Button>
                ))}
              </div>
            )}
            {!showLanguageSelector && (
              <Badge variant="secondary" className="text-xs">
                {
                  SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage)?.flag
                }{" "}
                {SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage)?.name}
              </Badge>
            )}
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Sessions</h3>
            <div className="space-y-2">
              {userSessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => loadSession(session.id)}
                  className={`p-3 rounded-xl cursor-pointer transition-all duration-200 group border ${
                    currentSession?.id === session.id
                      ? "bg-emerald-50 border-emerald-200"
                      : "hover:bg-gray-50 border-gray-100"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {new Date(session.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 truncate">
                        Session {session.id.slice(0, 8)}...
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-auto w-auto"
                      onClick={(e) => deleteSession(session.id, e)}
                    >
                      <Trash2 className="w-3 h-3 text-red-500" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {!currentSession ? (
            <WelcomeScreen />
          ) : (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-200 bg-white shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                      <Stethoscope className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-800">Dr. MedIntel</h3>
                      <p className="text-xs text-gray-500">AI Health Assistant</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {
                      SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage)?.flag
                    }{" "}
                    {SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage)?.name}
                  </Badge>
                </div>
              </div>

              {/* Messages */}
              <div
                className={`flex-1 overflow-y-auto p-6 ${dragActive ? "bg-emerald-50" : ""}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center text-gray-500">
                      <Stethoscope className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p className="text-lg font-medium mb-2">Ready to assist you</p>
                      <p className="text-sm">
                        Upload a medical report or ask a health question to get started
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="max-w-4xl mx-auto">
                    {messages.map(renderMessage)}
                    {isLoading && (
                      <div className="flex gap-3 mb-4">
                        <Avatar className="w-8 h-8 bg-emerald-500">
                          <AvatarFallback className="text-white">
                            <Stethoscope className="w-4 h-4" />
                          </AvatarFallback>
                        </Avatar>
                        <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                          <div className="flex items-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
                            <span className="text-sm text-gray-600">Analyzing...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-4 border-t border-gray-200 bg-white">
                <div className="max-w-4xl mx-auto">
                  <div className="flex gap-3 items-end">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => fileInputRef.current?.click()}
                          disabled={isLoading}
                          className="hover:bg-emerald-50 hover:border-emerald-200"
                        >
                          <Upload className="w-4 h-4 mr-1" />
                          Upload File
                        </Button>
                        <span className="text-xs text-gray-500">
                          Supports: Images (JPG, PNG), PDFs, Text files
                        </span>
                      </div>
                      <div className="relative">
                        <Input
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          placeholder="Ask a health question or describe your symptoms..."
                          disabled={isLoading}
                          className="pr-12 py-3 rounded-xl border-gray-200 focus:border-emerald-300"
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                              e.preventDefault();
                              sendMessage();
                            }
                          }}
                        />
                        <Button
                          onClick={sendMessage}
                          disabled={isLoading || !inputMessage.trim()}
                          size="sm"
                          className="absolute right-2 top-1/2 -translate-y-1/2 bg-emerald-500 hover:bg-emerald-600 rounded-lg p-2"
                        >
                          {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf,.txt"
        onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
        className="hidden"
      />
    </div>
  );
}

export default App;
