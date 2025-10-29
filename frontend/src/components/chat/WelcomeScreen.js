/**
 * WelcomeScreen component - Initial landing screen
 */
import React from "react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import {
  Stethoscope,
  FileText,
  Image as ImageIcon,
  Languages,
  Shield,
  Brain,
  Plus,
} from "lucide-react";

export const WelcomeScreen = ({ onNewSession }) => {
  return (
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
          onClick={onNewSession}
          size="lg"
          className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105"
        >
          <Plus className="w-5 h-5 mr-2" />
          Start New Consultation
        </Button>
      </div>
    </div>
  );
};
