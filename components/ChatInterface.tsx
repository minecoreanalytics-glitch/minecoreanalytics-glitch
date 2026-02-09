import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { ChatMessage } from '../types';
import { sendMessageToMorpheus } from '../services/geminiService';

const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init',
      role: 'model',
      content: 'Morpheus Neural Interface online. LightRAG initialized. How may I assist with your intelligence queries today?',
      timestamp: Date.now()
    }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendMessageToMorpheus(input);
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: response.content || "No response content",
        sql: response.sql,
        data: response.data,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Helper to render data table
  const renderDataTable = (data: any[]) => {
    if (!data || data.length === 0) return null;
    const headers = Object.keys(data[0]);
    return (
      <div className="mt-4 overflow-x-auto rounded-lg border border-morpheus-700 bg-morpheus-900/50">
        <table className="w-full text-xs text-left">
          <thead className="text-gray-400 bg-morpheus-800 uppercase font-mono">
            <tr>
              {headers.map(h => <th key={h} className="px-3 py-2">{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-morpheus-700/50">
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-morpheus-800/50">
                {headers.map(h => (
                  <td key={`${i}-${h}`} className="px-3 py-2 text-gray-300 font-mono whitespace-nowrap">
                    {typeof row[h] === 'object' ? JSON.stringify(row[h]) : String(row[h])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="px-3 py-1 text-[10px] text-gray-500 bg-morpheus-800 text-right">
          {data.length} results
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[600px] bg-morpheus-800 rounded-xl border border-morpheus-700 overflow-hidden shadow-2xl">
      <div className="bg-morpheus-900/50 p-4 border-b border-morpheus-700 flex items-center gap-2">
        <Sparkles className="text-morpheus-accent" size={18} />
        <h3 className="font-semibold text-white tracking-wide text-sm">NEURAL INTERFACE <span className='text-xs font-normal text-gray-500 ml-2'>v2.1 (SQL-Enabled)</span></h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center shrink-0
              ${msg.role === 'model' ? 'bg-morpheus-accent/20 text-morpheus-accent' : 'bg-blue-600 text-white'}
            `}>
              {msg.role === 'model' ? <Bot size={16} /> : <User size={16} />}
            </div>
            <div className={`
              max-w-[90%] p-3 rounded-lg text-sm leading-relaxed overflow-hidden
              ${msg.role === 'model'
                ? 'bg-morpheus-700/50 text-gray-200 border border-morpheus-700'
                : 'bg-blue-600 text-white'}
            `}>
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* SQL Preview */}
              {msg.sql && (
                <div className="mt-3 bg-black/30 rounded p-2 border border-morpheus-700/50">
                  <div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Generated SQL</div>
                  <code className="text-xs text-emerald-400 font-mono block overflow-x-auto">
                    {msg.sql}
                  </code>
                </div>
              )}

              {/* Data Table */}
              {msg.data && renderDataTable(msg.data)}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-morpheus-accent/20 flex items-center justify-center">
              <Bot size={16} className="text-morpheus-accent animate-pulse" />
            </div>
            <div className="bg-morpheus-700/50 p-3 rounded-lg border border-morpheus-700">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-morpheus-accent rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-morpheus-accent rounded-full animate-bounce delay-100"></span>
                <span className="w-2 h-2 bg-morpheus-accent rounded-full animate-bounce delay-200"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-morpheus-900 border-t border-morpheus-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Morpheus about platform status or specific customers..."
            className="flex-1 bg-morpheus-800 border border-morpheus-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-morpheus-accent focus:ring-1 focus:ring-morpheus-accent transition-all"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-morpheus-accent hover:bg-cyan-400 text-morpheus-900 px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;