import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Folder } from '../components/Collections/CollectionsTree';
import CollectionSettingsMenu from '../components/Collections/CollectionSettingsMenu';

interface CollectionContent {
  id: number;
  type: string;
  name: string;
  created_at: string;
  document_count?: number;
}

const CollectionView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [collection, setCollection] = useState<Folder | null>(null);
  const [contents, setContents] = useState<CollectionContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // Fetch collection details using the existing endpoint
    fetch(`/collection/${id}/`, {
      headers: {
        'Accept': 'application/json'
      }
    })
      .then(res => {
        if (!res.ok) {
          return res.json().then(err => {
            throw new Error(err.error || 'Failed to fetch collection');
          });
        }
        return res.json();
      })
      .then(data => {
        if (!data.collection) {
          throw new Error('Invalid response format');
        }

        setCollection({
          id: data.collection.id,
          name: data.collection.name,
          parent: data.collection.parent,
          collection: data.collection.id,
          path: data.collection.name,
          children: data.children || [],
          document_count: data.documents?.length || 0,
          created_at: data.collection.created_at ? new Date(data.collection.created_at).toLocaleString() : new Date().toLocaleString(),
          updated_at: data.collection.updated_at ? new Date(data.collection.updated_at).toISOString() : new Date().toISOString(),
        });

        // Transform the documents data to match our interface
        const transformedContents = (data.documents || []).map((doc: any) => ({
          id: doc.id,
          type: doc.type || 'document',
          name: doc.title || 'Untitled',
          created_at: doc.created_at ? new Date(doc.created_at).toLocaleString() : new Date().toLocaleString(),
          document_count: 0 // Documents don't have a document count
        }));
        setContents(transformedContents);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  const handleBack = () => {
    navigate('/collections');
  };

  const handleManageCollaborators = () => {
    // TODO: Implement collaborator management
  };

  const handleDelete = () => {
    // TODO: Implement delete functionality
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!collection) return <div>Collection not found</div>;

  return (
    <div style={{ padding: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
        <button
          onClick={handleBack}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            color: '#9ca3af',
            marginRight: '1rem'
          }}
        >
          ← Back
        </button>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', flex: 1 }}>{collection.name}</h1>
        <CollectionSettingsMenu
          collection={collection}
          onManageCollaborators={handleManageCollaborators}
          onDelete={handleDelete}
          onMove={() => {}}
        />
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#3b82f6',
          color: 'white',
          borderRadius: '0.375rem',
          border: 'none',
          cursor: 'pointer'
        }}>
          Ingest PDF
        </button>
        <button style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#3b82f6',
          color: 'white',
          borderRadius: '0.375rem',
          border: 'none',
          cursor: 'pointer'
        }}>
          Ingest from arXiv
        </button>
        <button style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#3b82f6',
          color: 'white',
          borderRadius: '0.375rem',
          border: 'none',
          cursor: 'pointer'
        }}>
          Ingest Transcript
        </button>
      </div>

      {/* Search and Controls */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '1rem',
        backgroundColor: '#1f2937',
        padding: '1rem',
        borderRadius: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '0.5rem',
              borderRadius: '0.375rem',
              border: '1px solid #4b5563',
              backgroundColor: '#374151',
              color: 'white'
            }}
          />
        </div>
      </div>

      {/* Content Table */}
      <div style={{ backgroundColor: '#1f2937', borderRadius: '0.5rem', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#374151' }}>
              <th style={{ padding: '1rem', textAlign: 'left' }}>
                <input type="checkbox" />
              </th>
              <th style={{ padding: '1rem', textAlign: 'left' }}>Type</th>
              <th style={{ padding: '1rem', textAlign: 'left' }}>Name</th>
              <th style={{ padding: '1rem', textAlign: 'left' }}>Manage</th>
            </tr>
          </thead>
          <tbody>
            {contents.map((item) => (
              <tr key={item.id} style={{ borderTop: '1px solid #4b5563' }}>
                <td style={{ padding: '1rem' }}>
                  <input type="checkbox" />
                </td>
                <td style={{ padding: '1rem' }}>{item.type}</td>
                <td style={{ padding: '1rem' }}>{item.name}</td>
                <td style={{ padding: '1rem' }}>
                  <button style={{
                    padding: '0.25rem 0.5rem',
                    backgroundColor: '#4b5563',
                    color: 'white',
                    borderRadius: '0.25rem',
                    border: 'none',
                    cursor: 'pointer'
                  }}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'flex-end', 
        alignItems: 'center',
        gap: '1rem',
        marginTop: '1rem',
        color: '#9ca3af'
      }}>
        <span>Rows per page: 10</span>
        <button style={{ background: 'none', border: 'none', color: '#9ca3af' }}>←</button>
        <button style={{ background: 'none', border: 'none', color: '#9ca3af' }}>→</button>
      </div>
    </div>
  );
};

export default CollectionView; 