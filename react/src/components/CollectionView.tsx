import React, { useState, useEffect } from 'react';
import { Folder } from '../components/CollectionsTree';
import CollectionSettingsMenu from '../components/CollectionSettingsMenu';
import FileSystemViewer from '../components/FileSystemViewer';
import MoveCollectionModal from '../components/MoveCollectionModal';
import { FileSystemItem } from '../types/FileSystemItem';
import { getCookie } from '../utils/csrf';

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
  // State for current collection details (children, documents)
  const [collection, setCollection] = useState<Folder | null>(null);
  const [contents, setContents] = useState<CollectionContent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // State for move modal (for moving the current collection)
  const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);
  
  // State for all available collections for moving purposes.
  const [allCollections, setAllCollections] = useState<Folder[]>([]);

  // Fetch current collection details (children and documents)
  useEffect(() => {
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

        // Set collection data (including children)
        setCollection({
          id: data.collection.id,
          name: data.collection.name,
          parent: data.collection.parent,
          collection: data.collection.id,
          path: data.collection.path,
          children: data.children || [],
          document_count: data.documents?.length || 0,
          children_count: data.children?.length || 0,
          created_at: data.collection.created_at
            ? new Date(data.collection.created_at).toLocaleString()
            : new Date().toLocaleString(),
          updated_at: data.collection.updated_at
            ? new Date(data.collection.updated_at).toISOString()
            : new Date().toISOString(),
        });

        console.log(collection);

        // Transform documents data
        const transformedDocuments = (data.documents || []).map((doc: any) => ({
          id: doc.id,
          type: doc.type || 'document',
          name: doc.title || 'Untitled',
          created_at: doc.created_at
            ? new Date(doc.created_at).toLocaleString()
            : new Date().toLocaleString(),
          document_count: 0,
        }));
        // Transform children (sub-collections) data
        const transformedChildren = (data.children || []).map((child: any) => ({
          id: child.id,
          type: 'collection', // explicitly mark it as a collection
          name: child.name,
          created_at: child.created_at || null,
          document_count: child.document_count,
        }));
        // Merge children and documents for the file system viewer
        const combinedItems = [...transformedChildren, ...transformedDocuments];
        setContents(combinedItems);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [collectionId]);

  // Fetch all available collections (for moving purposes)
  useEffect(() => {
    fetch('/get_collections_json/', {
      headers: {
        'Accept': 'application/json'
      },
      credentials: 'include'
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to fetch available collections');
        }
        return res.json();
      })
      .then(data => {
        // Expecting data.collections to be an array
        const collectionsData = data.collections || [];
        // We assume each collection has id, name, parent, etc.
        const parsed = collectionsData.map((col: any) => ({
          id: col.id,
          name: col.name,
          parent: col.parent, // either null or parent ID
          document_count: col.document_count,
          // Add other fields as needed.
        }));
        setAllCollections(parsed);
      })
      .catch(err => {
        console.error('Error fetching all collections:', err);
      });
  }, []);

  // Navigation handlers
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
    console.log('Removing item:', item);
    // TODO: Implement removal (delete API call, confirmation, etc.)
  };

  const handleOpenItem = (item: FileSystemItem) => {
    if (item.type === 'collection') {
      window.location.href = `/collection/${item.id}/`;
    } else if (item.type === 'pdf') {
      window.open(`/pdf/${item.id}/`, '_blank');
    } else {
      window.location.href = `/document/${item.id}/`;
    }
  };

  // Handler for moving the current collection.
  const handleMoveCollection = (folderId: number, newParentId: number | null) => {
    fetch(`/collection/move/${folderId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({
        new_parent_id: newParentId, // if null, move to root
      }),
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) {
          return res.json().then(data => {
            throw new Error(data.error || 'Failed to move collection');
          });
        }
        return res.json();
      })
      .then(data => {
        console.log('Collection moved successfully:', data);
        // Optionally, update the view or redirect if necessary.
        // For example, re-fetch current collection details or navigate away.
        setIsMoveModalOpen(false);
        // You might want to refresh the list of available collections, too.
      })
      .catch(err => {
        console.error('Error moving collection:', err);
        alert(`Error moving collection: ${err.message}`);
      });
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!collection) return <div>Collection not found</div>;

  return (
    <div style={{ padding: '2rem' }} className='font-sans'>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'end', justifyContent: 'center' }} className='mb-[32px] px-[40px]'>
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

        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', flex: 1, textAlign: 'center' }}>
          {collection.name}
        </h1>

        <CollectionSettingsMenu
          collection={collection}
          onManageCollaborators={handleManageCollaborators}
          onDelete={handleDelete}
          onMove={() => setIsMoveModalOpen(true)}
        />
      </div>

      <div className="relative flex items-center mb-[24px]"> 
          <div className="flex-grow border-t border-gray-shade_4"></div>
            <span className="font-sans text-xs px-[8px] bg-dark-mode-background text-gray-shade_7">Add Content</span>
          <div className="flex-grow border-t border-gray-shade_4"></div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '32px' }} className='mb-[24px]'>
        <button
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            borderRadius: '20px',
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
            borderRadius: '20px',
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
            borderRadius: '20px',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          Ingest Transcript
        </button>
      </div>

      <div className="relative flex items-center mb-[24px]"> 
          <div className="flex-grow border-t border-gray-shade_4"></div>
            <span className="font-sans text-xs px-[8px] bg-dark-mode-background text-gray-shade_7">Browse</span>
          <div className="flex-grow border-t border-gray-shade_4"></div>
      </div>

      <FileSystemViewer
        mode="browse"
        items={contents}
        collection={collection}
        onOpenItem={handleOpenItem}
        onRemoveItem={handleRemoveItem}
      />

      {/* Move Modal for moving the current collection */}
      <MoveCollectionModal
        folder={collection}       // the collection being moved
        collections={allCollections.filter(col => col.id !== collection?.id)} // full list of collections with parent information
        isOpen={isMoveModalOpen}
        onClose={() => setIsMoveModalOpen(false)}
        onSubmit={handleMoveCollection} // your move handler that calls the API
      />
    </div>
  );
};

export default CollectionView;
