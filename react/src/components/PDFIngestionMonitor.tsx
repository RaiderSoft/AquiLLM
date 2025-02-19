import React, { useEffect, useState, useRef } from 'react';
import { Terminal, ChevronDown, ChevronUp } from 'lucide-react';

interface Message {
  messages?: string[];
  progress?: number;
  exception?: string;
}

interface PDFIngestionMonitorProps {
  websocketUrl: string;
}

const PDFIngestionMonitor: React.FC<PDFIngestionMonitorProps> = ({ websocketUrl }) => {
  const [progress, setProgress] = useState<number>(0);
  const [messages, setMessages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    ws.current = new WebSocket(websocketUrl);

    ws.current.onopen = () => {
      console.log('Connected to WebSocket');
    };

    ws.current.onmessage = (event) => {
      const data: Message = JSON.parse(event.data);
      
      if (data.progress !== undefined) {
        setProgress(data.progress);
      }
      
      if (data.messages) {
        setMessages(prev => [...prev, ...(data.messages ?? [])]);
      }
      
      if (data.exception) {
        setError(data.exception);
      }
    };

    ws.current.onerror = (error) => {
      setError('WebSocket connection error');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [websocketUrl]);

  return (
    <div className="w-full max-w-2xl mx-auto p-6 space-y-6">
      {/* Progress Section */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm font-medium">
          <span>Ingestion Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* Console Output */}
      <div className="border rounded-lg bg-gray-900 text-gray-100">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between gap-2 p-4 hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Terminal size={18} />
            <span className="font-mono text-sm">Ingestion Log</span>
          </div>
          {isExpanded ? (
            <ChevronUp size={18} className="text-gray-400" />
          ) : (
            <ChevronDown size={18} className="text-gray-400" />
          )}
        </button>
        
        {isExpanded && (
          <div className="border-t border-gray-700 p-4">
            <div className="font-mono text-sm h-64 overflow-y-auto space-y-1">
              {messages.map((message, index) => (
                <div key={index} className="text-gray-300">
                  <span className="text-green-400"></span> {message}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
    </div>
  );
};

export default PDFIngestionMonitor;