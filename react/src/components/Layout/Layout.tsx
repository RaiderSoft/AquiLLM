import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="flex h-full overflow-hidden bg-gray-900 font-serif">
      <Sidebar isOpen={isSidebarOpen} />
      
      <div className="flex-grow flex flex-col h-full overflow-hidden">
        {/* Navigation Bar */}
        <nav className="bg-gray-800 text-white m-2.5 rounded-lg flex-shrink-0 px-4">
          <div className="mx-auto flex justify-between items-center max-w-full">
            <button
              className="bg-gray-700 my-2 hover:bg-gray-600 px-3 py-1 rounded-lg"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            >
              <img
                className={`h-6 transition-transform duration-300 ${isSidebarOpen ? '-scale-x-100' : ''}`}
                src="/images/latex-implies.svg"
                alt={isSidebarOpen ? "Close Menu" : "Open Menu"}
              />
            </button>

            {!isSidebarOpen && (
              <a href="/" className="text-2xl px-2 rounded-lg font-bold hover:bg-gray-700 flex justify-center items-center hover:underline">
                <div className="flex justify-center items-center">
                  <img className="h-6 object-scale-down" src="/images/aquila-small-lightest.svg" alt="AquiLLM Logo" />
                  <span className="pl-2">AquiLLM</span>
                </div>
              </a>
            )}

            <div className="flex items-center my-2">
              <button className="bg-gray-700 hover:bg-gray-600 hover:underline text-lg px-3 py-1 rounded-lg font-black">
                Log Out
              </button>
            </div>
          </div>
        </nav>

        {/* Main Content Area */}
        <div className="flex-grow overflow-y-auto p-5">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default Layout; 