
import React, { useState, useEffect, KeyboardEvent } from 'react';
import { User, Bot, Wrench, Loader } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'tool';
  content?: string;
  tool_call_input?: any;
  tool_call_name?: string;
  result_dict?: any;
  rating?: number;
  message_uuid?: string;
  usage?: number;
  for_whom?: string;
}

interface Conversation {
  messages: Message[];
}

interface Collection {
  id: number;
  name: string;
}

interface ChatComponentProps {
  convoId: string;
  collectionsUrl: string;
}

const MAX_RECONNECTION_ATTEMPTS = 5;
const CONNECTION_TIMEOUT = 5000;

const ChatComponent: React.FC<ChatComponentProps> = ({ convoId, collectionsUrl }) => {
  const [conversation, setConversation] = useState<Conversation>({ messages: [] });
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [messageInput, setMessageInput] = useState('');
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollections, setSelectedCollections] = useState<Set<number>>(new Set());
  const [collectionSearch, setCollectionSearch] = useState('');
  const [usage, setUsage] = useState(0);

  // Fetch collections from the provided URL
  useEffect(() => {
    fetch(collectionsUrl)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        setCollections(data.collections);
        const initialSelection = new Set<number>(data.collections.map((col: Collection) => col.id));
        setSelectedCollections(initialSelection);
      })
      .catch((error) => {
        console.error('Error fetching collections:', error);
      });
  }, [collectionsUrl]);

  // Establish a WebSocket connection and implement reconnection logic
  useEffect(() => {
    let attempts = connectionAttempts;
    let socket: WebSocket;

    const connect = () => {
      if (attempts >= MAX_RECONNECTION_ATTEMPTS) {
        setErrorMessage('Maximum reconnection attempts reached. Please refresh the page.');
        return;
      }
      attempts++;
      setConnectionAttempts(attempts);
      setErrorMessage(
        `Attempting to connect... (Attempt ${attempts} of ${MAX_RECONNECTION_ATTEMPTS})`
      );

      const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
      socket = new WebSocket(`${protocol}${window.location.host}/ws/convo/${convoId}/`);

      const timeoutId = setTimeout(() => {
        if (socket.readyState !== WebSocket.OPEN) {
          socket.close();
          setErrorMessage('Connection timeout. Retrying...');
          setTimeout(connect, 2000);
        }
      }, CONNECTION_TIMEOUT);

      socket.onopen = () => {
        clearTimeout(timeoutId);
        setConnectionAttempts(0);
        setErrorMessage('');
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.exception) {
            console.error('Server error:', data.exception);
            setErrorMessage(data.exception);
            return;
          }
          setErrorMessage('');
          if (data.conversation) {
            setConversation(data.conversation);
            // Update usage from the most recent assistant message (if any)
            const reversed = [...data.conversation.messages].reverse();
            const lastAssistant = reversed.find(
              (msg: Message) => msg.role === 'assistant' && !msg.tool_call_input
            );
            if (lastAssistant && lastAssistant.usage) {
              setUsage(lastAssistant.usage);
            }
          }
        } catch (err: any) {
          setErrorMessage('Error processing message: ' + err.message);
        }
      };

      socket.onclose = (event) => {
        clearTimeout(timeoutId);
        let msg = 'Disconnected from server. ';
        if (event.code === 1006) msg += 'Abnormal closure. ';
        else if (event.code === 1015) msg += 'TLS handshake failed. ';
        msg += 'Attempting to reconnect...';
        setErrorMessage(msg);
        setTimeout(connect, 2000);
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setErrorMessage('Connection error occurred. Retrying...');
      };

      setWs(socket);
    };

    connect();

    return () => {
      if (socket) socket.close();
    };
  }, [convoId]);

  const sendMessage = () => {
    if (!messageInput.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
    const userMessage: Message = { role: 'user', content: messageInput.trim() };
    const newConversation = { messages: [...conversation.messages, userMessage] };
    setConversation(newConversation);
    const payload = {
      action: 'append',
      message: userMessage,
      collections: Array.from(selectedCollections),
    };
    ws.send(JSON.stringify(payload));
    setMessageInput('');
  };

  const rateMessage = (uuid: string | undefined, rating: number) => {
    if (!ws || !uuid) return;
    const payload = { action: 'rate', uuid, rating };
    ws.send(JSON.stringify(payload));
  };

  const handleInputKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  const shouldShowSpinner = () => {
    if (conversation.messages.length === 0) return false;
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    return (
      lastMessage.role === 'user' ||
      (lastMessage.role === 'assistant' && lastMessage.tool_call_input) ||
      (lastMessage.role === 'tool' && lastMessage.for_whom === 'assistant')
    );
  };

  // Recursive component to render nested tool result objects
  const RenderToolResult: React.FC<{ data: any; level?: number }> = ({ data, level = 0 }) => {
    if (typeof data === 'object' && data !== null) {
      if (Array.isArray(data)) {
        return (
          <details open={level < 1} className="mt-1">
            <summary className="cursor-pointer font-mono hover:text-blue-600">Array</summary>
            <div className="pl-4 border-l-2 border-gray-300 mt-1">
              {data.map((item, idx) => (
                <RenderToolResult key={idx} data={item} level={level + 1} />
              ))}
            </div>
          </details>
        );
      } else {
        return (
          <div>
            {Object.entries(data).map(([key, value]) =>
              typeof value === 'object' && value !== null ? (
                <details key={key} open={level < 1} className="mt-1">
                  <summary className="cursor-pointer font-mono hover:text-blue-600">{key}</summary>
                  <div className="pl-4 border-l-2 border-gray-300 mt-1">
                    <RenderToolResult data={value} level={level + 1} />
                  </div>
                </details>
              ) : (
                <div key={key} className="mt-1">
                  <span className="font-mono text-blue-600">{key}: </span>
                  <span className="font-mono text-green-200">{String(value)}</span>
                </div>
              )
            )}
          </div>
        );
      }
    }
    return <span className="font-mono text-green-200">{String(data)}</span>;
  };

  // Component for rating buttons
  const RatingButtons: React.FC<{ message: Message }> = ({ message }) => {
    const emojis = ['😞', '😕', '😐', '🙂', '😊'];
    return (
      <div className="flex items-center gap-1 mt-2">
        <span className="text-sm mr-2">Rate:</span>
        {emojis.map((emoji, i) => (
          <button
            key={i}
            className={`p-1 rounded transition-colors ${
              message.rating === i + 1 ? 'bg-gray-200' : 'hover:bg-gray-200'
            }`}
            onClick={() => {
              message.rating = i + 1;
              rateMessage(message.message_uuid, i + 1);
              // Trigger a re-render by updating conversation state
              setConversation({ ...conversation });
            }}
          >
            {emoji}
          </button>
        ))}
      </div>
    );
  };

  // Render a single message bubble
  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';
    const isTool = message.role === 'tool';

    const messageClasses = `w-4/5 p-2.5 rounded shadow-md whitespace-pre-wrap break-words font-sans ${
      isUser
        ? 'bg-gray-400 text-white self-end'
        : isAssistant
        ? 'bg-blue-500 text-white'
        : 'bg-green-500 border border-green-300 text-white'
    }`;

    return (
      <div key={index} className={`flex items-center gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
        {!isUser && (
          <div className="mr-2">
            {isAssistant ? <Bot className="w-6 h-6" /> : isTool ? <Wrench className="w-6 h-6" /> : null}
          </div>
        )}
        <div className={messageClasses}>
          {message.content && <p className="whitespace-pre-wrap break-words">{message.content}</p>}
          {isAssistant && message.tool_call_input && (
            <div className="mt-2.5 text-sm">
              <strong>Called Tool: {message.tool_call_name}</strong>
              <details className="mt-1.5">
                <summary className="cursor-pointer text-gray-100">View Tool Arguments</summary>
                <pre className="whitespace-pre-wrap break-words bg-blue-700 p-2 rounded text-white">
                  {JSON.stringify(message.tool_call_input, null, 2)}
                </pre>
              </details>
            </div>
          )}
          {isTool && (
            <>
              <div className="mb-2 font-bold text-white">Tool Output: {message.tool_call_name}</div>
              <details className="mt-1.5" open>
                <summary className="cursor-pointer text-white">
                  {message.result_dict && message.result_dict.exception ? 'View Exception' : 'View Results'}
                </summary>
                <div className="bg-green-700 p-2 rounded text-white">
                  {message.result_dict && (
                    <RenderToolResult
                      data={message.result_dict.exception || message.result_dict.result}
                    />
                  )}
                </div>
              </details>
            </>
          )}
          {(isAssistant || isTool) && <RatingButtons message={message} />}
          <p className="text-xs mt-1.5 text-right">{new Date().toLocaleString()}</p>
        </div>
        {isUser && (
          <div className="ml-2">
            <User className="w-6 h-6" />
          </div>
        )}
      </div>
    );
  };

  // Render collections selection panel
  const renderCollections = () => {
    const filtered = collections.filter((col) =>
      col.name.toLowerCase().includes(collectionSearch.toLowerCase())
    );
    return filtered.map((col) => (
      <div key={col.id} className="flex items-center p-2 hover:bg-gray-300 rounded">
        <input
          type="checkbox"
          id={`collection-${col.id}`}
          className="h-4 w-4"
          checked={selectedCollections.has(col.id)}
          onChange={(e) => {
            const newSet = new Set(selectedCollections);
            if (e.target.checked) newSet.add(col.id);
            else newSet.delete(col.id);
            setSelectedCollections(newSet);
          }}
        />
        <label htmlFor={`collection-${col.id}`} className="ml-2 text-sm">
          {col.name}
        </label>
      </div>
    ));
  };

  return (
    <div className="flex flex-col h-full max-h-full items-center">
      <div className="border-t border-gray-300 w-4/5 mb-8 flex flex-col items-center">
        {errorMessage && (
          <div
            id="exception-box"
            className="sticky top-0 z-50 font-mono text-red-700 p-4 mb-4 bg-red-100 rounded"
          >
            {errorMessage}
          </div>
        )}
        <div className="flex items-center justify-center mt-8 w-full gap-8">
          <div className="flex flex-col gap-2 bg-gray-200 py-2 px-4 rounded-full w-full">
            <input
              type="text"
              id="message-input"
              style={{ color: '#eeeeee', fontFamily: 'sans-serif' }}
              className="px-2 py-2 mr-4 flex-grow w-full rounded-lg bg-gray-200 placeholder:text-gray-500"
              placeholder="Type your message here..."
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={handleInputKeyPress}
              disabled={!ws || ws.readyState !== WebSocket.OPEN}
            />
            <button
              id="send-button"
              className="p-4 bg-blue-500 text-white rounded-full -mr-2 disabled:cursor-not-allowed"
              title="Send Message"
              onClick={sendMessage}
              disabled={!ws || ws.readyState !== WebSocket.OPEN}
            >
              <Loader className="w-4 h-4 animate-spin" />
            </button>
          </div>
          <div>
            <details className="w-full text-gray-800">
              <summary className="cursor-pointer w-max px-4 py-2 bg-blue-500 h-9 rounded-full flex items-center">
                <span>Select Collections</span>
                <span className="ml-2 text-sm">
                  {selectedCollections.size ? `(${selectedCollections.size} selected)` : ''}
                </span>
              </summary>
              <div className="p-2">
                <input
                  type="text"
                  id="collection-search"
                  placeholder="Search..."
                  className="text-sm h-9 w-full p-2 border rounded-lg mt-2"
                  value={collectionSearch}
                  onChange={(e) => setCollectionSearch(e.target.value)}
                />
              </div>
              <div className="mt-2 p-2 border rounded-lg max-h-40 overflow-y-auto">
                {renderCollections()}
              </div>
            </details>
          </div>
        </div>
      </div>
      <div
        className="w-4/5 overflow-y-auto h-full max-h-full px-8 pt-8 mt-8"
        style={{
          maskImage: 'linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 1) 5%)',
          WebkitMaskImage:
            'linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 1) 5%)',
        }}
      >
        {conversation.messages.map((msg, idx) => renderMessage(msg, idx))}
        {shouldShowSpinner() && (
          <div className="flex justify-center my-4">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent" />
          </div>
        )}
      </div>
      <div id="usage-bar-container" className="w-4/5 mb-4">
        <div id="usage-text" className="text-center mt-1 text-sm text-gray-700">
          {usage} / 200,000
        </div>
      </div>
    </div>
  );
};

export default ChatComponent;
