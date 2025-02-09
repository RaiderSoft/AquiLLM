import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface NavLink {
  text: string;
  url: string;
  isReactRoute?: boolean;
}

const mainNavLinks: NavLink[] = [
  { text: 'New Conversation', url: '/new_convo/', isReactRoute: false },
  { text: 'Old Conversations', url: '/user_conversations/', isReactRoute: false },
  { text: 'Search', url: '/search/', isReactRoute: false },
  { text: 'Collections', url: '/collections/', isReactRoute: true },
];

const utilityNavLinks: NavLink[] = [
  { text: 'Ingest from arXiv', url: '/insert_arxiv/', isReactRoute: false },
  { text: 'Ingest PDF', url: '/ingest_pdf/', isReactRoute: false },
  { text: 'Ingest Transcript', url: '/ingest_vtt/', isReactRoute: false },
];

const Sidebar: React.FC<{ isOpen: boolean }> = ({ isOpen }) => {
  const location = useLocation();
  const isReactRoute = location.pathname.startsWith('/app/');

  // Function to get the correct URL based on whether we're in a React route
  const getUrl = (link: NavLink) => {
    if (link.isReactRoute) {
      return isReactRoute ? link.url : `/app${link.url}`;
    }
    return isReactRoute ? link.url.replace('/app/', '/') : link.url;
  };

  return (
    <div 
      className={`flex flex-col w-60 bg-gray-800 text-white m-2.5 rounded-lg flex-shrink-0 min-h-[calc(100vh-20px)] 
        overflow-y-hidden border border-dashed border-gray-600 border-2 transition-all duration-300 
        ${!isOpen ? '-ml-64' : ''}`}
    >
      <a href="/" className="text-2xl font-bold hover:bg-gray-700 flex justify-center items-center p-6 hover:underline">
        <div className="flex justify-center items-center">
          <img className="h-20 object-scale-down" src="/static/images/aquila-medium.svg" alt="AquiLLM Logo" />
          <span className="py-2">AquiLLM</span>
        </div>
      </a>

      <div className="flex flex-col">
        <div className="px-4 py-2 text-sm text-gray-400">Menu</div>
        {mainNavLinks.map((link) => (
          <a
            key={link.url}
            href={getUrl(link)}
            className="px-5 py-2 text-lg font-bold hover:underline hover:bg-gray-700"
          >
            {link.text}
          </a>
        ))}
      </div>

      <div className="flex flex-col mt-4">
        <div className="px-4 py-2 text-sm text-gray-400">Utilities</div>
        {utilityNavLinks.map((link) => (
          <a
            key={link.url}
            href={getUrl(link)}
            className="px-5 py-2 text-lg font-bold hover:underline hover:bg-gray-700"
          >
            {link.text}
          </a>
        ))}
      </div>

      <div className="flex justify-center p-5 mt-auto">
        <img src="/static/images/aquila.svg" alt="AquiLLM Logo" className="h-24" />
      </div>
    </div>
  );
};

export default Sidebar; 