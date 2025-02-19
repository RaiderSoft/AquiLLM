import React, { useState, useEffect } from 'react';
import { Folder } from '../components/CollectionsTree';
import MoveCollectionModal from '../components/MoveCollectionModal';
import CreateCollectionModal from '../components/CreateCollectionModal';
import CollectionSettingsMenu from '../components/CollectionSettingsMenu';
import { getCookie } from '../utils/csrf';

// Define the prop types
interface CollectionsPageProps {
  apiUrl: string;       // URL to fetch collections (e.g. '/api/collections/')
  detailUrlBase?: string; // Base URL for navigating to a specific collection (e.g. '/collections')
}

const CollectionsPage: React.FC<CollectionsPageProps> = ({ apiUrl, detailUrlBase }) => {
  // Remove react-router since we’ll handle navigation via props or window.location
  const [collections, setCollectionsToView] = useState<Folder[]>([]);
  const [allCollections, setAllCollections] = useState<Folder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [folderToMove, setFolderToMove] = useState<Folder | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  // Fetch collections on mount using the provided API URL
  useEffect(() => {
    fetch(apiUrl, {
      credentials: 'include', // Include cookies if needed
      headers: { 'Accept': 'application/json' }
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to fetch collections');
        }
        return res.json();
      })
      .then((data) => {
        // Assume each collection in data.collections now includes a "parent" field.
        const collectionsData = data.collections || [];
        const parsedCollections = collectionsData.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: col.parent, // Use the parent's id or null if no parent.
          collection: col.id,
          path: col.path,
          children: [], // You could also parse children if provided.
          document_count: col.document_count,
          children_count: col.children_count,
          created_at: new Date(col.created_at || new Date()).toLocaleString(),
          updated_at: new Date(col.updated_at || new Date()).toISOString(),
        }));

        // Filter to only include root-level collections (parent === null)
        const rootCollections = parsedCollections.filter((col: { parent: Folder | null }) => col.parent === null);

        setAllCollections(parsedCollections);
        setCollectionsToView(rootCollections);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError('Error fetching collections');
        setLoading(false);
      });
  }, [apiUrl]);

  // Handler functions
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
    fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ name: newCollection.name }),
      credentials: 'include'
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to create collection');
        }
        // Refresh the list after creation
        return fetch(apiUrl, { credentials: 'include' });
      })
      .then(res => res.json())
      .then((data) => {
        const collectionsData = data.collections || [];
        const parsedCollections = collectionsData.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: null,
          collection: col.id,
          path: col.path,
          children: col.children || [],
          document_count: col.document_count,
          children_count: col.children_count,
          created_at: new Date(col.created_at || new Date()).toLocaleString(),
          updated_at: new Date(col.updated_at || new Date()).toISOString(),
        }));

        // Filter to only include root-level collections (parent === null)
        const rootCollections = parsedCollections.filter((col: { parent: Folder | null }) => col.parent === null);

        setAllCollections(parsedCollections);
        setCollectionsToView(rootCollections);
        setIsCreateModalOpen(false);
      })
      .catch((err) => {
        console.error('Error:', err);
        alert('Failed to create collection. Please try again.');
      });
  };

  const handleDeleteCollection = (collection: Folder) => {
    if (window.confirm(`Are you sure you want to delete "${collection.name}"?`)) {
      fetch(`/api/collections/delete/${collection.id}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        credentials: 'include'
      })
        .then((res) => {
          if (!res.ok) throw new Error('Failed to delete collection');

          setCollectionsToView(collections.filter(c => c.id !== collection.id));
        })
        .catch((err) => {
          console.error('Error:', err);
          alert('Failed to delete collection. Please try again.');
        });
    }
  };

  const handleManageCollaborators = (collection: Folder) => {
    console.log('Manage collaborators for:', collection);
  };

  // Instead of useNavigate, we use the provided detailUrlBase (if any) to redirect
  const handleCollectionClick = (collection: Folder) => {
    if (detailUrlBase) {
      window.location.href = `${detailUrlBase}/${collection.id}/`;
    }
  };

  const handleMoveCollection = (folderId: number, newParentId: number | null) => {
    fetch(`/collection/move/${folderId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({
        new_parent_id: newParentId, // null means moving to root
      }),
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((data) => {
            throw new Error(data.error || 'Failed to move collection');
          });
        }
        return res.json();
      })
      .then((data) => {
        console.log('Collection moved successfully:', data);
        // Optionally refresh the collections state to reflect changes:
        // fetchCollections(); // For example, re-fetch your collections
        // Close the modal:
        handleCloseModal();
      })
      .catch((err) => {
        console.error('Error moving collection:', err);
        alert(`Error moving collection: ${err.message}`);
      });
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div style={{ padding: '2rem' }} className='font-sans overflow-y-auto'>

      <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', textAlign: 'center', marginBottom: '1.5rem' }}>Collections</h1>

      <button
          className='bg-accent'
          style={{
            padding: '0.5rem 1rem',
            color: 'white',
            borderRadius: '0.375rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            border: 'none',
            cursor: 'pointer',
            marginBottom: '1.5rem'
          }}
          onClick={handleOpenCreateModal}
        >
          <span>+</span>
          <span>New Collection</span>
        </button>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '1.5rem'
      }}>
        {collections.map((collection) => (
          <div
            key={collection.id}
            className='bg-gray-shade_3 text-gray-shade_e border border-gray-shade_7 hover:scale-[102%] transition-transform rounded-[20px]'
            style={{
              padding: '1.5rem',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            }}
            onClick={() => handleCollectionClick(collection)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '.5rem' }}>

              <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold' }} className='cursor-pointer hover:underline'>{collection.name}</h2>

              <CollectionSettingsMenu
                collection={collection}
                onMove={handleMoveClick}
                onDelete={handleDeleteCollection}
                onManageCollaborators={handleManageCollaborators}
              />
            </div>
            
            <div style={{ marginBottom: '1.5rem', fontSize: '0.875rem', color: '#9ca3af' }} onClick={(e) => e.stopPropagation()}>
              <div className='pointer-events-none'>Documents: {collection.document_count}</div>
              <div className='pointer-events-none'>Sub collections: {collection.children_count}</div>
              <div className='pointer-events-none'>Created: {collection.created_at}</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem' }} onClick={(e) => e.stopPropagation()}>
              <button
                className='bg-accent'
                style={{
                  padding: '0.5rem',
                  color: 'white',
                  borderRadius: '0.375rem',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                Ingest PDF
              </button>
              <button
                className='bg-accent'
                style={{
                  padding: '0.5rem',
                  color: 'white',
                  borderRadius: '0.375rem',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                Ingest from arXiv
              </button>
              <button
                className='bg-accent'
                style={{
                  padding: '0.5rem',
                  color: 'white',
                  borderRadius: '0.375rem',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                Ingest Transcript
              </button>
            </div>

            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              border: '2px dashed #4b5563',
              borderRadius: '0.375rem',
              textAlign: 'center'
            }} onClick={(e) => e.stopPropagation()}>
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
        collections={allCollections.filter(col => col.id !== folderToMove?.id)}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSubmit={handleMoveCollection}
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
