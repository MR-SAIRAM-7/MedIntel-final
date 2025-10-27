import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";

export const sendWhatsAppMessage = async (to, message) => {
  try {
    const res = await axios.post(`${API_URL}/api/send-whatsapp`, {
      to,
      message,
    });
    return res.data;
  } catch (err) {
    console.error("Error sending WhatsApp message:", err);
    throw err;
  }
};
