import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const IngestArxiv: React.FC = () => {
  const [arxivId, setArxivId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!arxivId.trim()) {
      setError('Please enter an arXiv ID');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch('/api/insert_arxiv/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ arxiv_id: arxivId.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.error || 'Failed to ingest arXiv paper');
      }

      const data = await response.json();
      setSuccess(true);
      setArxivId('');

      // If we have a document ID, navigate to it after a short delay
      if (data.document_id) {
        setTimeout(() => {
          navigate(`/document/${data.document_id}`);
        }, 1500);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-white">Ingest arXiv Paper</h1>
      
      <form onSubmit={handleSubmit} className="max-w-md">
        <div className="mb-4">
          <label className="block text-white mb-2">arXiv ID or URL</label>
          <input
            type="text"
            value={arxivId}
            onChange={(e) => setArxivId(e.target.value)}
            placeholder="e.g., 2101.12345 or https://arxiv.org/abs/2101.12345"
            className="w-full p-2 bg-gray-800 text-white rounded border border-gray-700 focus:outline-none focus:border-blue-500"
          />
          <p className="mt-1 text-gray-400 text-sm">
            Enter the arXiv ID (e.g., 2101.12345) or the full URL
          </p>
        </div>

        {error && (
          <div className="mb-4 text-red-500 text-sm">{error}</div>
        )}

        {success && (
          <div className="mb-4 text-green-500 text-sm">
            Successfully ingested arXiv paper! Redirecting to document view...
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 px-4 rounded-lg font-semibold ${
            loading
              ? 'bg-gray-600 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          } text-white transition-colors`}
        >
          {loading ? 'Ingesting...' : 'Ingest Paper'}
        </button>
      </form>
    </div>
  );
};

export default IngestArxiv; 