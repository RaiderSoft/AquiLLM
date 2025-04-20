import React, { useEffect, useState, useCallback } from 'react';
// Keep PDFIngestionMonitorProps for now if PDF monitor is separate, or remove if unified
import { PDFIngestionMonitorProps, IngestionDashboardProps } from '../types';
import PDFIngestionMonitor from './PDFIngestionMonitor'; // Keep for now

// Define a more generic status interface
interface IngestionTaskStatus {
  taskId: string; // Celery task ID or unique identifier for the job
  type: 'pdf' | 'crawl' | 'unknown'; // Type of ingestion
  status: 'pending' | 'progress' | 'success' | 'error';
  progress: number; // 0-100
  message: string; // Current status message or error
  documentId?: string; // Available on success
  documentTitle?: string; // Available on success
  initialUrl?: string; // For crawls
  // Add any other relevant fields, e.g., from PDFIngestionMonitorProps if merging
  documentName?: string; // From PDFIngestionMonitorProps
  websocketUrl?: string; // From PDFIngestionMonitorProps (might become redundant)
}

const IngestionDashboard: React.FC<IngestionDashboardProps> = ({ wsUrl, onNewDocument }) => {
  // Use the new generic state type
  const [tasks, setTasks] = useState<IngestionTaskStatus[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);
      console.log("WS Message Received:", message); // Debugging

      // Check if it's the new crawl status update format
      if (message.type === 'crawl.task.update' && message.payload) {
        const { task_id, message_type, ...payload } = message.payload;

        setTasks(prevTasks => {
          const existingTaskIndex = prevTasks.findIndex(task => task.taskId === task_id);
          let updatedTasks = [...prevTasks];

          if (existingTaskIndex !== -1) {
            // Update existing task
            const updatedTask = { ...updatedTasks[existingTaskIndex] };
            updatedTask.status = message_type === 'crawl.success' ? 'success' : (message_type === 'crawl.error' ? 'error' : 'progress');
            if (payload.progress !== undefined) updatedTask.progress = payload.progress;
            if (payload.message) updatedTask.message = payload.message;
            if (payload.error) updatedTask.message = `Error: ${payload.error}`; // Overwrite message with error
            if (payload.document_id) updatedTask.documentId = payload.document_id;
            if (payload.title) updatedTask.documentTitle = payload.title;

            updatedTasks[existingTaskIndex] = updatedTask;
            console.log("Updated Task:", updatedTask); // Debugging
          } else if (message_type === 'crawl.start') {
            // Add new task if it's a start message and not already present
            const newTask: IngestionTaskStatus = {
              taskId: task_id,
              type: 'crawl',
              status: 'progress', // Start implies progress begins
              progress: payload.progress || 0,
              message: payload.message || 'Crawl started...',
              initialUrl: payload.initial_url,
            };
            updatedTasks.push(newTask);
            console.log("Added New Task:", newTask); // Debugging
            if (onNewDocument) onNewDocument(); // Notify parent if needed
          } else {
             // Fix typo: use 'payload' instead of 'message_payload'
             console.warn("Received non-start message for unknown task:", task_id, payload);
          }
          return updatedTasks;
        });

      }
      // TODO: Add handling for existing PDF monitor messages if needed,
      // or migrate PDF status updates to the new format/consumer.
      // Example for existing PDF start message:
      else if (message.type === 'document.ingestion.start') {
         // This assumes the message format matches PDFIngestionMonitorProps
         // You might need to adapt this based on the actual message content
         const pdfProps: PDFIngestionMonitorProps = message; // Adjust parsing if needed
         setTasks(prevTasks => {
            // Avoid adding duplicates if already handled
            if (prevTasks.some(task => task.documentId === pdfProps.documentId)) {
                return prevTasks;
            }
            const newTask: IngestionTaskStatus = {
                taskId: pdfProps.documentId, // Use documentId as taskId for PDFs for now
                type: 'pdf',
                status: 'pending', // Or 'progress' if start implies progress
                progress: 0,
                message: `Ingesting PDF: ${pdfProps.documentName}`,
                documentId: pdfProps.documentId,
                documentName: pdfProps.documentName,
                // Remove websocketUrl as it's not in the type definition
                // websocketUrl: pdfProps.websocketUrl,
            };
            console.log("Added New PDF Task:", newTask); // Debugging
             if (onNewDocument) onNewDocument();
            return [...prevTasks, newTask];
         });
      }
       else {
         console.log("Ignoring unknown message type:", message.type);
       }

    } catch (err: any) {
      console.error("Error processing WebSocket message:", err);
      setError(err.message || 'An error occurred while processing the message.');
    }
  }, [onNewDocument]); // Include dependencies

  useEffect(() => {
    // Construct the full WebSocket URL for crawl status
    // Assumes wsUrl is the base path like 'ws://localhost:8000' or 'wss://yourdomain.com'
    // Adjust if wsUrl prop provides the full path already
    let crawlStatusWsUrl = '';
    if (wsUrl) {
        try {
            const url = new URL(wsUrl); // Use URL constructor for robust handling
            crawlStatusWsUrl = `${url.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.host}/ws/crawl_status/`;
            console.log("Connecting to WebSocket:", crawlStatusWsUrl);
        } catch (e) {
            console.error("Invalid wsUrl provided:", wsUrl);
            setError('Invalid WebSocket base URL provided');
            return;
        }
    } else {
        setError('WebSocket base URL not provided');
        console.error("WebSocket base URL not provided");
        return;
    }


    const socket = new WebSocket(crawlStatusWsUrl);

    socket.onopen = () => {
      console.log("WebSocket Connected");
      setIsConnected(true);
      setError(null); // Clear previous errors on successful connection
    };

    socket.onmessage = handleMessage; // Use the memoized handler

    socket.onerror = (event) => {
      console.error("WebSocket Error:", event);
      setError('WebSocket connection error. Check console for details.');
      setIsConnected(false);
    };

    socket.onclose = (event) => {
      console.log("WebSocket Disconnected:", event.reason, `Code: ${event.code}`);
      setIsConnected(false);
      // Optional: Implement reconnection logic here if desired
      // setError('WebSocket disconnected.'); // Can be noisy, maybe only show persistent errors
    };

    // Cleanup function
    return () => {
      console.log("Closing WebSocket connection");
      socket.close();
    };
  // Add handleMessage to dependency array
  }, [wsUrl, handleMessage]);

  // Render logic
  if (error) {
    return <div className="p-4 text-red-600 bg-red-100 border border-red-400 rounded">Error: {error}</div>;
  }

  if (!isConnected && tasks.length === 0) {
     // Don't show loading indefinitely if connection fails/closes
     return <div className="p-4 text-gray-500">Connecting to ingestion status...</div>;
  }


  return (
    <div className="space-y-4 p-4 border border-gray-shade_4 rounded-lg bg-gray-shade_1">
       <h3 className="text-lg font-semibold text-gray-shade_e mb-2">Ingestion Status</h3>
      {tasks.length === 0 && <div className="text-gray-shade_a">No active ingestion tasks.</div>}
      {tasks.map((task) => (
        // Basic display for now - Replace with a dedicated component later
        <div key={task.taskId} className={`p-3 rounded border ${task.status === 'error' ? 'border-red-400 bg-red-50' : 'border-gray-shade_3 bg-gray-shade_2'}`}>
          <div className="flex justify-between items-center mb-1">
             <span className="font-medium text-gray-shade_d text-sm break-all">
                {task.type === 'crawl' ? `Crawl: ${task.initialUrl || task.taskId}` : `Ingest: ${task.documentName || task.documentTitle || task.taskId}`}
             </span>
             <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                 task.status === 'success' ? 'bg-green-100 text-green-800' :
                 task.status === 'error' ? 'bg-red-100 text-red-800' :
                 task.status === 'progress' ? 'bg-blue-100 text-blue-800' :
                 'bg-yellow-100 text-yellow-800' // pending
             }`}>
                {task.status}
             </span>
          </div>
          <div className="text-sm text-gray-shade_a mb-2">{task.message}</div>
          {task.status === 'progress' && (
            <div className="w-full bg-gray-shade_3 rounded-full h-2.5">
              <div className="bg-blue h-2.5 rounded-full" style={{ width: `${task.progress}%` }}></div>
            </div>
          )}
           {/* Optionally render the old PDF monitor if needed for specific PDF WS logic */}
           {/* {task.type === 'pdf' && task.websocketUrl && (
              <PDFIngestionMonitor key={task.documentId} {...task as PDFIngestionMonitorProps} />
           )} */}
        </div>
      ))}
    </div>
  );
};

export default IngestionDashboard;