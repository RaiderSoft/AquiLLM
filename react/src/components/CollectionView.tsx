import React, { useState, useEffect } from 'react';
import { Folder } from '../components/CollectionsTree';
import CollectionSettingsMenu from '../components/CollectionSettingsMenu';
import FileSystemViewer from '../components/FileSystemViewer';
import { FileSystemItem } from '../types/FileSystemItem';

interface CollectionContent {
  id: number;
  type: string;
  name: string;
  created_at: string;
  document_count?: number;
}

interface CollectionViewProps {
  collectionId: string;
  onBack?: () => void; // optional callback when the back button is pressed
}

const CollectionView: React.FC<CollectionViewProps> = ({ collectionId, onBack }) => {
  const [collection, setCollection] = useState<Folder | null>(null);
  const [contents, setContents] = useState<CollectionContent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // Fetch collection details using the provided collectionId
    fetch(`/collection/${collectionId}/`, {
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

        // Set collection data
        setCollection({
          id: data.collection.id,
          name: data.collection.name,
          parent: data.collection.parent,
          collection: data.collection.id,
          path: data.collection.name,
          children: data.children || [],
          document_count: data.documents?.length || 0,
          created_at: data.collection.created_at
            ? new Date(data.collection.created_at).toLocaleString()
            : new Date().toLocaleString(),
          updated_at: data.collection.updated_at
            ? new Date(data.collection.updated_at).toISOString()
            : new Date().toISOString(),
        });

        // Transform documents data
        const transformedContents = (data.documents || []).map((doc: any) => ({
          id: doc.id,
          type: doc.type || 'document',
          name: doc.title || 'Untitled',
          created_at: doc.created_at
            ? new Date(doc.created_at).toLocaleString()
            : new Date().toLocaleString(),
          document_count: 0, // Documents don't have a document count
        }));
        setContents(transformedContents);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [collectionId]);

  // When the back button is clicked, use the provided onBack callback
  // or fallback to window.history.back()
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.history.back();
    }
  };

  const handleManageCollaborators = () => {
    // TODO: Implement collaborator management
  };

  const handleDelete = () => {
    // TODO: Implement delete functionality
  };

  const handleRemoveItem = (item: FileSystemItem) => {
    // Implement a delete call or show a confirmation
    console.log('Removing item:', item);
  };

  const handleOpenItem = (item: FileSystemItem) => {
    if (item.type === 'collection') {
      // Navigate to the sub-collection, e.g.:
      window.location.href = `/collection/${item.id}/`;
    } else if (item.type === 'pdf') {
      // Open the PDF in a new tab
      window.open(`/pdf/${item.id}/`, '_blank');
    } else {
      // Open the standard document view
      window.location.href = `/document/${item.id}/`;
    }
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
        <button
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            borderRadius: '0.375rem',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          Ingest PDF
        </button>
        <button
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            borderRadius: '0.375rem',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          Ingest from arXiv
        </button>
        <button
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            borderRadius: '0.375rem',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          Ingest Transcript
        </button>
      </div>

      <FileSystemViewer
        mode="browse"
        items={contents}
        onOpenItem={handleOpenItem}
        onRemoveItem={handleRemoveItem}
      />

    </div>
  );
};

export default CollectionView;
