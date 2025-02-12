import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import NewConversation from './pages/NewConversation';
import Conversations from './pages/Conversations';
import Search from './pages/Search';
import CollectionsPage from './pages/CollectionsPage';
import CollectionView from './pages/CollectionView';
import IngestArxiv from './pages/IngestArxiv';
import IngestPDF from './pages/IngestPDF';
import IngestTranscript from './pages/IngestTranscript';

const App: React.FC = () => {
  return (
    <Router basename="/app">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="collections" element={<CollectionsPage />} />
          <Route path="collections/:id" element={<CollectionView />} />
          <Route path="new-conversation" element={<NewConversation />} />
          <Route path="conversations" element={<Conversations />} />
          <Route path="search" element={<Search />} />
          <Route path="ingest">
            <Route path="arxiv" element={<IngestArxiv />} />
            <Route path="pdf" element={<IngestPDF />} />
            <Route path="transcript" element={<IngestTranscript />} />
          </Route>
          <Route path="*" element={<Home />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App; 