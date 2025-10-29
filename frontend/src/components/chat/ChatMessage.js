/**
 * ChatMessage component - Displays individual chat messages
 */
import React from "react";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Stethoscope, FileText, Image as ImageIcon } from "lucide-react";

export const ChatMessage = ({ message }) => {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : ""}`}>
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
