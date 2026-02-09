import { DataService } from "./dataService";

import { ChatMessage } from "../types";

export const sendMessageToMorpheus = async (message: string): Promise<Partial<ChatMessage>> => {
  try {
    // Call the backend intelligence API
    const response = await DataService.request<{ answer: string; sql?: string; data?: any[] }>(
      '/platform/intelligence/query',
      {
        answer: "Morpheus Neural Interface is offline. Please check backend connection.",
        sql: "-- No connection"
      },
      'POST',
      { message }
    );

    return {
      role: 'model',
      content: response.answer,
      sql: response.sql,
      data: response.data,
      timestamp: Date.now()
    };

  } catch (error) {
    console.error("Intelligence API Error:", error);
    return {
      role: 'model',
      content: "Connection to Neural Core interrupted. Please verify backend is running.",
      timestamp: Date.now()
    };
  }
};