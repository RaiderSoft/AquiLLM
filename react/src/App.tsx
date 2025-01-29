import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Home from './components/Pages/Home';
import NewConversation from './components/Pages/NewConversation';
import Conversations from './components/Pages/Conversations';
import Search from './components/Pages/Search';
import Collections from './components/Pages/Collections';
import IngestArxiv from './components/Pages/IngestArxiv';
import IngestPDF from './components/Pages/IngestPDF';
import IngestTranscript from './components/Pages/IngestTranscript';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="new-conversation" element={<NewConversation />} />
          <Route path="conversations" element={<Conversations />} />
          <Route path="search" element={<Search />} />
          <Route path="collections" element={<Collections />} />
          <Route path="ingest">
            <Route path="arxiv" element={<IngestArxiv />} />
            <Route path="pdf" element={<IngestPDF />} />
            <Route path="transcript" element={<IngestTranscript />} />
          </Route>
          {/* Fallback route */}
          <Route path="*" element={<Home />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App; 