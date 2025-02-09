import React, { useState } from 'react';

interface SearchResult {
  title: string;
  content: string;
  score: number;
  document_id: string;
}

const Search: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/search/?q=${encodeURIComponent(searchQuery)}`, {
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Search failed');
      }
      
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setError(error instanceof Error ? error.message : 'An error occurred while searching');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-white">Search Documents</h1>
      
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your documents..."
            className="flex-grow p-2 bg-gray-800 text-white rounded border border-gray-700 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={isSearching}
            className={`px-4 py-2 rounded font-semibold ${
              isSearching
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white transition-colors`}
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="text-red-500 mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {searchResults.map((result, index) => (
          <div key={index} className="bg-gray-800 p-4 rounded-lg">
            <h3 className="text-white font-medium mb-2">{result.title}</h3>
            <p className="text-gray-400 text-sm">{result.content}</p>
            <div className="mt-2 flex justify-between items-center">
              <span className="text-blue-400 text-xs">
                Score: {result.score.toFixed(2)}
              </span>
              <a
                href={`/document/${result.document_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 text-sm"
              >
                View Document
              </a>
            </div>
          </div>
        ))}
        {searchResults.length === 0 && !isSearching && searchQuery && (
          <div className="text-gray-400 text-center">
            No results found for "{searchQuery}"
          </div>
        )}
      </div>
    </div>
  );
};

export default Search; 