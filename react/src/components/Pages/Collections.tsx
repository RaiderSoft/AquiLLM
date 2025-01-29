import React, { useState, useEffect } from 'react';

interface Collection {
  id: string;
  name: string;
  documentCount: number;
  lastUpdated: string;
}

const Collections: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await fetch('/api/collections/');
        if (!response.ok) {
          throw new Error('Failed to fetch collections');
        }
        const data = await response.json();
        setCollections(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load collections');
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-white">
        Loading collections...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-500">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Your Collections</h1>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          onClick={() => {/* TODO: Open new collection modal */}}
        >
          New Collection
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {collections.map((collection) => (
          <div
            key={collection.id}
            className="bg-gray-800 p-4 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <h3 className="text-white font-medium mb-2">{collection.name}</h3>
            <div className="text-gray-400 text-sm">
              {collection.documentCount} documents
            </div>
            <div className="text-gray-500 text-xs mt-2">
              Last updated: {new Date(collection.lastUpdated).toLocaleDateString()}
            </div>
            <div className="mt-4 flex gap-2">
              <button
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                onClick={() => {/* TODO: View collection */}}
              >
                View
              </button>
              <button
                className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                onClick={() => {/* TODO: Delete collection */}}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {collections.length === 0 && (
        <div className="text-center text-gray-400 mt-8">
          No collections yet. Create one to get started!
        </div>
      )}
    </div>
  );
};

export default Collections; 