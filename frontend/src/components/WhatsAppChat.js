import React, { useState } from "react";
import { sendWhatsAppMessage } from "../lib/api";

function WhatsAppChat() {
  const [to, setTo] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");

  const handleSend = async () => {
    if (!to || !message) {
      setStatus("⚠️ Please enter both number and message");
      return;
    }

    try {
      setStatus("Sending...");
      const res = await sendWhatsAppMessage(to, message);
      setStatus(`✅ Message sent! SID: ${res.sid}`);
    } catch {
      setStatus("❌ Failed to send message. Check backend logs.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <div className="bg-white shadow-lg rounded-2xl p-6 w-full max-w-md">
        <h1 className="text-2xl font-bold text-green-700 mb-4 text-center">
          WhatsApp AI Integration
        </h1>

        <input
          type="text"
          placeholder="+91XXXXXXXXXX"
          className="border border-gray-300 rounded-lg p-2 w-full mb-3"
          value={to}
          onChange={(e) => setTo(e.target.value)}
        />

        <textarea
          placeholder="Enter your message..."
          className="border border-gray-300 rounded-lg p-2 w-full mb-3 min-h-[100px]"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />

        <button
          onClick={handleSend}
          className="bg-green-600 text-white rounded-lg py-2 w-full hover:bg-green-700 transition"
        >
          Send Message
        </button>

        {status && (
          <p className="text-center text-sm mt-3 text-gray-700">{status}</p>
        )}
      </div>
    </div>
  );
}

export default WhatsAppChat;
