/**
 * Main App Component - Modular Architecture
 * MedIntel AI Health Assistant
 */
import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { Toaster, toast } from "sonner";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Avatar, AvatarFallback } from "./components/ui/avatar";
import { Stethoscope, Loader2 } from "lucide-react";

// Modular components
import { ChatSidebar } from "./components/chat/ChatSidebar";
import { ChatMessage } from "./components/chat/ChatMessage";
import { ChatInput } from "./components/chat/ChatInput";
import { WelcomeScreen } from "./components/chat/WelcomeScreen";

// Hooks and services
import { useChat } from "./hooks/useChat";
import { useWebSocket } from "./hooks/useWebSocket";
import { SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE } from "./constants/languages";
import { messageAPI } from "./services/api";

function App() {
  const [inputMessage, setInputMessage] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState(DEFAULT_LANGUAGE);
  const [showLanguageSelector, setShowLanguageSelector] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const userIdRef = useRef(`user_${Math.random().toString(36).slice(2)}_${Date.now()}`);

  // Use custom hooks
  const {
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
  } = useChat(userIdRef.current);

  // WebSocket handler
  const handleWebSocketMessage = (text) => {
    if (skipNextAssistantRef.current) {
      skipNextAssistantRef.current = false;
      return;
    }
    const msg = {
      id: `${Date.now()}_${Math.random()}`,
      session_id: currentSession?.id,
      role: "assistant",
      content: text,
      timestamp: new Date().toISOString(),
    };
    addMessage(msg);
  };

  const { sendMessage: sendViaWebSocket, isConnected } = useWebSocket(
    currentSession?.id,
    handleWebSocketMessage
  );

  // Scroll to bottom on new messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Update language when session changes
  useEffect(() => {
    if (currentSession?.language) {
      setSelectedLanguage(currentSession.language);
    }
  }, [currentSession]);

  /**
   * Handle new session creation
   */
  const handleNewSession = async () => {
    await createSession(selectedLanguage);
  };

  /**
   * Handle language change
   */
  const handleLanguageChange = async (langCode) => {
    setSelectedLanguage(langCode);
    setShowLanguageSelector(false);

    if (currentSession?.id) {
      try {
        skipNextAssistantRef.current = true;
        await messageAPI.send(currentSession.id, langCode, langCode);
        toast.success("Language updated");
      } catch (error) {
        skipNextAssistantRef.current = false;
        console.error("Failed to update language:", error);
        toast.error("Could not update language");
      }
    }
  };

  /**
   * Handle sending message
   */
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !currentSession?.id) return;

    const userMsg = {
      id: `${Date.now()}_${Math.random()}`,
      session_id: currentSession.id,
      role: "user",
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };
    
    addMessage(userMsg);
    const messageToSend = inputMessage;
    setInputMessage("");

    try {
      // Try WebSocket first
      if (isConnected && sendViaWebSocket(messageToSend)) {
        return;
      }

      // Fallback to REST API
      const response = await sendMessage(messageToSend, selectedLanguage);
      if (response?.assistant_message && !isConnected) {
        addMessage({
          id: response.assistant_message.id || `${Date.now()}_${Math.random()}`,
          session_id: currentSession.id,
          role: "assistant",
          content: response.assistant_message.content,
          timestamp: response.assistant_message.timestamp || new Date().toISOString(),
        });
      }
    } catch (error) {
      const is429 = error.response?.status === 429;
      toast.error(is429 ? "Rate limit reached. Please wait a bit." : "Failed to send message");
    }
  };

  /**
   * Handle file upload
   */
  const handleFileUpload = async (file) => {
    if (!currentSession?.id) {
      toast.error("Please start a new session first");
      return;
    }

    // Add local user message
    const localUserMsg = {
      id: `${Date.now()}_${Math.random()}`,
      session_id: currentSession.id,
      role: "user",
      content: `Uploaded file: ${file.name}`,
      file_info: { filename: file.name, content_type: file.type, size: file.size },
      timestamp: new Date().toISOString(),
    };
    addMessage(localUserMsg);

    const message = `Please analyze this ${file.type.startsWith("image/") ? "medical image" : "medical report"}.`;
    const response = await uploadFile(file, message, selectedLanguage);

    if (response?.assistant_message && !isConnected) {
      addMessage({
        id: response.assistant_message.id || `${Date.now()}_${Math.random()}`,
        session_id: currentSession.id,
        role: "assistant",
        content: response.assistant_message.content,
        timestamp: response.assistant_message.timestamp || new Date().toISOString(),
      });
    }
  };

  /**
   * File input change handler
   */
  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  /**
   * Drag and drop handlers
   */
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

  const selectedLang = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage);

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
      <Toaster position="top-right" richColors />

      <div className="flex h-screen">
        {/* Sidebar */}
        <ChatSidebar
          sessions={sessions}
          currentSession={currentSession}
          selectedLanguage={selectedLanguage}
          showLanguageSelector={showLanguageSelector}
          onNewSession={handleNewSession}
          onLoadSession={loadSession}
          onDeleteSession={deleteSession}
          onLanguageChange={handleLanguageChange}
          onToggleLanguageSelector={() => setShowLanguageSelector((v) => !v)}
        />

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {!currentSession ? (
            <WelcomeScreen onNewSession={handleNewSession} />
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
                    {selectedLang?.flag} {selectedLang?.name}
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
                    {messages.map((message) => (
                      <ChatMessage key={message.id} message={message} />
                    ))}
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
              <ChatInput
                inputMessage={inputMessage}
                setInputMessage={setInputMessage}
                onSendMessage={handleSendMessage}
                onFileUpload={() => fileInputRef.current?.click()}
                isLoading={isLoading}
                fileInputRef={fileInputRef}
              />
            </>
          )}
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf,.txt"
        onChange={handleFileInputChange}
        className="hidden"
      />
    </div>
  );
}

export default App;
