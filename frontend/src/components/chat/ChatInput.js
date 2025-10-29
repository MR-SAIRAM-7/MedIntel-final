/**
 * ChatInput component - Input area for sending messages and uploading files
 */
import React from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Upload, Send, Loader2 } from "lucide-react";

export const ChatInput = ({
  inputMessage,
  setInputMessage,
  onSendMessage,
  onFileUpload,
  isLoading,
  fileInputRef,
}) => {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
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
                onKeyDown={handleKeyDown}
              />
              <Button
                onClick={onSendMessage}
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
  );
};
