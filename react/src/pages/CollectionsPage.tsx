import React, { useState, useEffect } from 'react';
import CollectionsTree, { Folder } from '../components/Collections/CollectionsTree';
import MoveCollectionModal from '../components/Collections/MoveCollectionModal';
import CreateCollectionModal from '../components/Collections/CreateCollectionModal';
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
        // Transform the API response to match our Folder interface
        const collections = data.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: null,
          collection: col.id,
          path: col.name,
          children: [],
          document_count: col.document_count,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
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
    // Open modal with the folder to move
    setFolderToMove(folder);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setFolderToMove(null);
    setIsModalOpen(false);
  };

  const handleSubmitMove = (folderId: number, newParentId: number | null) => {
    // Here you would call an API endpoint to update the folder's parent
    console.log(`Move folder ${folderId} to new parent ${newParentId}`);

    // For now, simulate update by updating local state
    const updateFolderParent = (folders: Folder[]): Folder[] => {
      return folders.map((folder) => {
        if (folder.id === folderId) {
          return { ...folder, parent: newParentId };
        }
        if (folder.children && folder.children.length > 0) {
          return { ...folder, children: updateFolderParent(folder.children) };
        }
        return folder;
      });
    };

    const updatedCollections = updateFolderParent(collections);
    setCollections(updatedCollections);
    handleCloseModal();
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
        // After successful creation, fetch the updated collections list
        return fetch('/api/collections/');
      })
      .then(res => res.json())
      .then((data) => {
        // Transform and update the collections list
        const collections = data.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: null,
          collection: col.id,
          path: col.name,
          children: [],
          document_count: col.document_count,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }));
        setCollections(collections);
        setIsCreateModalOpen(false);
      })
      .catch((err) => {
        console.error('Error:', err);
        alert('Failed to create collection. Please try again.');
      });
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Collections</h1>
        <button
          style={{ padding: '0.5rem 1rem', backgroundColor: 'blue', color: 'white', borderRadius: '4px' }}
          onClick={handleOpenCreateModal}
        >
          Create Collection
        </button>
      </div>
      <CollectionsTree folders={collections} onMoveCollection={handleMoveClick} />
      <MoveCollectionModal
        folder={folderToMove}
        collections={collections}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSubmit={handleSubmitMove}
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