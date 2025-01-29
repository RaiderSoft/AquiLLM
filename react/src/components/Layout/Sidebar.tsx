import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface NavLink {
  text: string;
  url: string;
}

const mainNavLinks: NavLink[] = [
  { text: 'New Conversation', url: '/new-conversation' },
  { text: 'Old Conversations', url: '/conversations' },
  { text: 'Search', url: '/search' },
  { text: 'Collections', url: '/collections' },
];

const utilityNavLinks: NavLink[] = [
  { text: 'Ingest from arXiv', url: '/ingest/arxiv' },
  { text: 'Ingest PDF', url: '/ingest/pdf' },
  { text: 'Ingest Transcript', url: '/ingest/transcript' },
];

const Sidebar: React.FC<{ isOpen: boolean }> = ({ isOpen }) => {
  return (
    <div 
      className={`flex flex-col w-60 bg-gray-800 text-white m-2.5 rounded-lg flex-shrink-0 min-h-[calc(100vh-20px)] 
        overflow-y-hidden border border-dashed border-gray-600 border-2 transition-all duration-300 
        ${!isOpen ? '-ml-64' : ''}`}
    >
      <Link to="/" className="text-2xl font-bold hover:bg-gray-700 flex justify-center items-center p-6 hover:underline">
        <div className="flex justify-center items-center">
          <img className="h-20 object-scale-down" src="/images/aquila-medium.svg" alt="AquiLLM Logo" />
          <span className="py-2">AquiLLM</span>
        </div>
      </Link>

      <div className="flex flex-col">
        <div className="px-4 py-2 text-sm text-gray-400">Menu</div>
        {mainNavLinks.map((link) => (
          <Link
            key={link.url}
            to={link.url}
            className="px-5 py-2 text-lg font-bold hover:underline hover:bg-gray-700"
          >
            {link.text}
          </Link>
        ))}
      </div>

      <div className="flex flex-col mt-4">
        <div className="px-4 py-2 text-sm text-gray-400">Utilities</div>
        {utilityNavLinks.map((link) => (
          <Link
            key={link.url}
            to={link.url}
            className="px-5 py-2 text-lg font-bold hover:underline hover:bg-gray-700"
          >
            {link.text}
          </Link>
        ))}
      </div>

      <div className="flex justify-center p-5 mt-auto">
        <img src="/images/aquila.svg" alt="AquiLLM Logo" className="h-24" />
      </div>
    </div>
  );
};

export default Sidebar; 