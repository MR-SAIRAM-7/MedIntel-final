/**
 * ChatSidebar component - Session list and language selector
 */
import React from "react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  Plus,
  MessageSquare,
  Trash2,
  Languages,
  Stethoscope,
} from "lucide-react";
import { SUPPORTED_LANGUAGES } from "../../constants/languages";

export const ChatSidebar = ({
  sessions,
  currentSession,
  selectedLanguage,
  showLanguageSelector,
  onNewSession,
  onLoadSession,
  onDeleteSession,
  onLanguageChange,
  onToggleLanguageSelector,
}) => {
  const selectedLang = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage);

  return (
    <div className="w-80 bg-white border-r border-gray-200 shadow-sm flex flex-col">
      {/* Header */}
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
          onClick={onNewSession}
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
            onClick={onToggleLanguageSelector}
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
                onClick={() => onLanguageChange(lang.code)}
              >
                <span className="mr-1">{lang.flag}</span>
                {lang.name}
              </Button>
            ))}
          </div>
        )}
        {!showLanguageSelector && (
          <Badge variant="secondary" className="text-xs">
            {selectedLang?.flag} {selectedLang?.name}
          </Badge>
        )}
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Sessions</h3>
        <div className="space-y-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onLoadSession(session.id)}
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
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                >
                  <Trash2 className="w-3 h-3 text-red-500" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
