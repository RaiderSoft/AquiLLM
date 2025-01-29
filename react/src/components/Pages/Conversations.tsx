import React from 'react';

const Conversations: React.FC = () => {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-white">Previous Conversations</h1>
      <div className="grid gap-4">
        {/* Placeholder for conversation list */}
        <div className="bg-gray-800 p-4 rounded-lg hover:bg-gray-700 cursor-pointer">
          <div className="text-white font-medium">Conversation Title</div>
          <div className="text-gray-400 text-sm">Last message preview...</div>
          <div className="text-gray-500 text-xs mt-2">January 29, 2024</div>
        </div>
        {/* Add more conversation items here */}
      </div>
    </div>
  );
};

export default Conversations; 