import React, { useState, useEffect } from 'react';
import { Folder } from '../components/Collections/CollectionsTree';
import MoveCollectionModal from '../components/Collections/MoveCollectionModal';
import CreateCollectionModal from '../components/Collections/CreateCollectionModal';
import CollectionSettingsMenu from '../components/Collections/CollectionSettingsMenu';
import { getCookie } from '../utils/csrf';

const CollectionsPage: React.FC = () => {
  const [collections, setCollections] = useState<Folder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [folderToMove, setFolderToMove] = useState<Folder | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Fetch collections from backend on mount
  useEffect(() => {
    fetch('/api/collections/')
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to fetch collections');
        }
        return res.json();
      })
      .then((data) => {
        const collections = data.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: null,
          collection: col.id,
          path: col.name,
          children: [],
          document_count: col.document_count,
          created_at: new Date(col.created_at || new Date()).toLocaleString(),
          updated_at: new Date(col.updated_at || new Date()).toISOString(),
        }));
        setCollections(collections);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError('Error fetching collections');
        setLoading(false);
      });
  }, []);

  const handleMoveClick = (folder: Folder) => {
    setFolderToMove(folder);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setFolderToMove(null);
    setIsModalOpen(false);
  };

  const handleOpenCreateModal = () => {
    setIsCreateModalOpen(true);
  };

  const handleCloseCreateModal = () => {
    setIsCreateModalOpen(false);
  };

  const handleSubmitCreate = (newCollection: Folder) => {
    fetch('/api/collections/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        name: newCollection.name
      })
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to create collection');
        }
        return fetch('/api/collections/');
      })
      .then(res => res.json())
      .then((data) => {
        const collections = data.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: null,
          collection: col.id,
          path: col.name,
          children: [],
          document_count: col.document_count,
          created_at: new Date(col.created_at || new Date()).toLocaleString(),
          updated_at: new Date(col.updated_at || new Date()).toISOString(),
        }));
        setCollections(collections);
        setIsCreateModalOpen(false);
      })
      .catch((err) => {
        console.error('Error:', err);
        alert('Failed to create collection. Please try again.');
      });
  };

  const handleDeleteCollection = (collection: Folder) => {
    if (window.confirm(`Are you sure you want to delete "${collection.name}"?`)) {
      fetch(`/api/collections/${collection.id}/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': getCookie('csrftoken')
        }
      })
        .then((res) => {
          if (!res.ok) throw new Error('Failed to delete collection');
          setCollections(collections.filter(c => c.id !== collection.id));
        })
        .catch((err) => {
          console.error('Error:', err);
          alert('Failed to delete collection. Please try again.');
        });
    }
  };

  const handleManageCollaborators = (collection: Folder) => {
    // TODO: Implement collaborator management
    console.log('Manage collaborators for:', collection);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Collections</h1>
        <button
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#2563eb',
            color: 'white',
            borderRadius: '0.375rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            border: 'none',
            cursor: 'pointer'
          }}
          onClick={handleOpenCreateModal}
        >
          <span>+</span>
          <span>New Collection</span>
        </button>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '1.5rem'
      }}>
        {collections.map((collection) => (
          <div
            key={collection.id}
            style={{
              backgroundColor: '#2d2d2d',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{collection.name}</h2>
              <CollectionSettingsMenu
                collection={collection}
                onMove={handleMoveClick}
                onDelete={handleDeleteCollection}
                onManageCollaborators={handleManageCollaborators}
              />
            </div>
            
            <div style={{ marginBottom: '1rem', fontSize: '0.875rem', color: '#9ca3af' }}>
              <div>Documents: {collection.document_count}</div>
              <div>Sub collections: {collection.children.length}</div>
              <div>Created: {collection.created_at}</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <button style={{
                padding: '0.5rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '0.375rem',
                border: 'none',
                cursor: 'pointer'
              }}>
                Ingest PDF
              </button>
              <button style={{
                padding: '0.5rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '0.375rem',
                border: 'none',
                cursor: 'pointer'
              }}>
                Ingest from arXiv
              </button>
              <button style={{
                padding: '0.5rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '0.375rem',
                border: 'none',
                cursor: 'pointer'
              }}>
                Ingest Transcript
              </button>
            </div>

            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              border: '2px dashed #4b5563',
              borderRadius: '0.375rem',
              textAlign: 'center'
            }}>
              <div>Drag Files Here</div>
              <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                <span>browse files</span> or <span>browse folders</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <MoveCollectionModal
        folder={folderToMove}
        collections={collections}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSubmit={() => {}}
      />
      <CreateCollectionModal
        isOpen={isCreateModalOpen}
        onClose={handleCloseCreateModal}
        onSubmit={handleSubmitCreate}
      />
    </div>
  );
};

export default CollectionsPage; 