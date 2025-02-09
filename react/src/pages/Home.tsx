import React, { useState } from 'react';

interface Message {
  content: string;
  timestamp: string;
  isUser: boolean;
}

const Home: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      content: "Hello! It's nice to meet you. How can I assist you today? I'm here to help with any questions or tasks you might have. Feel free to ask about anything, and I'll do my best to provide information or use the available tools to help you.",
      timestamp: new Date().toLocaleString(),
      isUser: false,
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const newMessage: Message = {
      content: inputMessage,
      timestamp: new Date().toLocaleString(),
      isUser: true,
    };

    setMessages([...messages, newMessage]);
    setInputMessage('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-grow overflow-y-auto mb-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-start gap-3 mb-4 ${
              message.isUser ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`w-8 h-8 flex items-center justify-center rounded ${
                message.isUser ? 'bg-gray-700' : 'bg-blue-600'
              }`}
            >
              {message.isUser ? (
                <span className="text-white">U</span>
              ) : (
                <span className="text-white font-serif">α</span>
              )}
            </div>
            <div
              className={`flex-grow p-3 rounded-lg ${
                message.isUser
                  ? 'bg-gray-700 text-white'
                  : 'bg-blue-600 text-white'
              }`}
            >
              <div className="text-sm">{message.content}</div>
              <div className="text-xs mt-1 opacity-70">
                {message.timestamp}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <button
          type="button"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Select Collections
        </button>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type your message here..."
          className="flex-grow p-2 bg-gray-800 text-white rounded border border-gray-700 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          className="p-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 5l7 7m0 0l-7 7m7-7H3"
            />
          </svg>
        </button>
      </form>
    </div>
  );
};

export default Home; 