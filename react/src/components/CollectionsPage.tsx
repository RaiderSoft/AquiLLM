import React, { useState, useEffect } from 'react';
import { Folder } from '../components/CollectionsTree';
import MoveCollectionModal from '../components/MoveCollectionModal';
import CreateCollectionModal from '../components/CreateCollectionModal';
import CollectionSettingsMenu from '../components/CollectionSettingsMenu';
import UserManagementModal from '../components/UserManagementModal';
import { getCookie } from '../utils/csrf';

// Define the prop types
interface CollectionsPageProps {
  apiUrl: string;       // URL to fetch collections (e.g. '/api/collections/')
  detailUrlBase?: string; // Base URL for navigating to a specific collection (e.g. '/collections')
}

const CollectionsPage: React.FC<CollectionsPageProps> = ({ apiUrl, detailUrlBase }) => {
  // Remove react-router since we'll handle navigation via props or window.location
  const [collections, setCollectionsToView] = useState<Folder[]>([]);
  const [allCollections, setAllCollections] = useState<Folder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [folderToMove, setFolderToMove] = useState<Folder | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [isUserManagementModalOpen, setIsUserManagementModalOpen] = useState<boolean>(false);
  const [selectedCollection, setSelectedCollection] = useState<Folder | null>(null);

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

  const handleManageCollaborators = (folder: Folder) => {
    setSelectedCollection(folder);
    setIsUserManagementModalOpen(true);
  };

  const handleCloseUserManagementModal = () => {
    setIsUserManagementModalOpen(false);
    setSelectedCollection(null);
  };

  const handleUserManagementSave = () => {
    // Set success message
    setSuccessMessage(`Collaborators for "${selectedCollection?.name}" updated successfully!`);
    
    // Clear message after 5 seconds
    setTimeout(() => {
      setSuccessMessage(null);
    }, 5000);

    // Refresh collections after saving permissions
    fetch(apiUrl, {
      credentials: 'include',
      headers: { 'Accept': 'application/json' }
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to refresh collections');
        }
        return res.json();
      })
      .then((data) => {
        const collectionsData = data.collections || [];
        const parsedCollections = collectionsData.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: col.parent,
          collection: col.id,
          path: col.path,
          children: [],
          document_count: col.document_count,
          children_count: col.children_count,
          created_at: new Date(col.created_at || new Date()).toLocaleString(),
          updated_at: new Date(col.updated_at || new Date()).toISOString(),
        }));

        const rootCollections = parsedCollections.filter((col: { parent: Folder | null }) => col.parent === null);
        setAllCollections(parsedCollections);
        setCollectionsToView(rootCollections);
      })
      .catch((err) => {
        console.error('Error refreshing collections:', err);
        setError('Failed to refresh collections after updating permissions');
        
        // Clear error message after 5 seconds
        setTimeout(() => {
          setError(null);
        }, 5000);
      });
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
    <div className='p-4'>
      {/* Success notification */}
      {successMessage && (
        <div className='bg-green-600 text-white p-4 mb-4 rounded flex items-center justify-between'>
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Error message display */}
      {error && (
        <div className='bg-red-600 text-white p-4 mb-4 rounded flex items-center justify-between'>
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Loading indicator */}
      {loading ? (
        <div>Loading collections...</div>
      ) : (
        <>
          {/* Header section */}
          <div className='flex justify-between items-center mb-4'>
            <h1 className='text-2xl font-bold'>My Collections</h1>
            <button
              onClick={handleOpenCreateModal}
              className='bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded'
            >
              New Collection
            </button>
          </div>

          {/* Collections grid */}
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
            {collections.map((folder) => (
              <div
                key={folder.id}
                className='bg-gray-shade_3 hover:bg-opacity-100 rounded-lg p-4 cursor-pointer transition duration-200 relative'
                onClick={() => {
                  if (detailUrlBase) {
                    window.location.href = `${detailUrlBase}/${folder.id}/`;
                  }
                }}
              >
                <div className='flex justify-between items-start'>
                  <div>
                    <h2 className='text-xl font-semibold mb-2'>{folder.name}</h2>
                    <p className='text-gray-300 mb-2'>
                      {folder.document_count} documents • {folder.children_count} subcollections
                    </p>
                    <p className='text-gray-400 text-sm'>
                      Created: {new Date(folder.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <CollectionSettingsMenu
                    collection={folder}
                    onMove={handleMoveClick}
                    onDelete={handleDeleteCollection}
                    onManageCollaborators={handleManageCollaborators}
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Modals */}
      {folderToMove && (
        <MoveCollectionModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          folder={folderToMove}
          collections={allCollections.filter(c => c.id !== folderToMove.id)}
          onSubmit={(folderId, newParentId) => {
            console.log(`Move folder ${folderId} to parent ${newParentId}`);
            handleCloseModal();
          }}
        />
      )}

      <CreateCollectionModal
        isOpen={isCreateModalOpen}
        onClose={handleCloseCreateModal}
        onSubmit={handleSubmitCreate}
      />

      {selectedCollection && (
        <UserManagementModal
          isOpen={isUserManagementModalOpen}
          onClose={handleCloseUserManagementModal}
          onSave={handleUserManagementSave}
          collection={selectedCollection}
        />
      )}
    </div>
  );
};

export default CollectionsPage;
