import React, { useState, useEffect } from 'react';
import { Folder } from '../components/CollectionsTree';
import CollectionSettingsMenu from '../components/CollectionSettingsMenu';
import FileSystemViewer from '../components/FileSystemViewer';
import MoveCollectionModal from '../components/MoveCollectionModal';
import { FileSystemItem } from '../types/FileSystemItem';
import { getCookie } from '../utils/csrf';
import IngestRowContainer from '../components/IngestRow';
import formatUrl from '../utils/formatUrl';

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

  const [movingItem, setMovingItem] = useState<FileSystemItem | null>(null);
  const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);
  const [allCollections, setAllCollections] = useState<Folder[]>([]);

  // Fetch current collection details (children and documents)
  useEffect(() => {
    fetch(formatUrl(window.apiUrls.api_collection, { col_id: collectionId }), {
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
          created_at: new Date(child.created_at || new Date()).toLocaleString(),
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
    fetch(window.apiUrls.api_collections, {
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

  const handleRenameItem = () => {
    // TODO: Implement rename functionality
  }

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
      window.location.href = formatUrl(window.pageUrls.collection, { col_id: item.id });
    } else {
      window.location.href = formatUrl(window.pageUrls.document, { doc_id: item.id });
    }
  };

  // Context Menu onMove handler (from FileSystemViewer)
  const handleContextMove = (item: FileSystemItem) => {
    // When user right-clicks on an item and selects "Move"
    setMovingItem(item);
    setIsMoveModalOpen(true);
  };

  // Handler for moving the current collection.
  const handleMoveSubmit = (itemId: number, newParentId: number | null) => {
    if (!movingItem) return;
    if (movingItem.type === 'collection') {
      // Call collection move endpoint:
      fetch(formatUrl(window.apiUrls.api_move_collection, { collection_id: itemId }), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ new_parent_id: newParentId }),
        credentials: 'include',
      })
        .then(res => res.ok ? res.json() : res.json().then(data => { throw new Error(data.error || 'Failed to move collection'); }))
        .then(data => {
          console.log('Collection moved:', data);
          setIsMoveModalOpen(false);
          setMovingItem(null);
          // Optionally, refresh the collection details.
        })
        .catch(err => {
          console.error('Error moving collection:', err);
          alert(`Error: ${err.message}`);
        });
    } else {
      // Assume it's a document
      fetch(formatUrl(window.apiUrls.api_move_document, { doc_id: movingItem.id }), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ new_collection_id: newParentId }),
        credentials: 'include',
      })
        .then(res => res.ok ? res.json() : res.json().then(data => { throw new Error(data.error || 'Failed to move document'); }))
        .then(data => {
          console.log('Document moved:', data);
          setIsMoveModalOpen(false);
          setMovingItem(null);
          // Optionally, refresh the document list.
        })
        .catch(err => {
          console.error('Error moving document:', err);
          alert(`Error: ${err.message}`);
        });
    }
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
          }}
        >
          ← Back
        </button>
        
        {/* 
            The right padding here is a little weird, because the padding on the the element to the right of it
            has a padding of 0.5rem that slightly offsets this title off-center.  This padding re-centers it with respect
            to the page. 
        */}
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', flex: 1, textAlign: 'center', paddingRight: '0.5rem' }}>
          {collection.name}
        </h1>

        <CollectionSettingsMenu
          collection={collection}
          onManageCollaborators={handleManageCollaborators}
          onDelete={handleDelete}
          onMove={() => {
            setMovingItem({ id: collection!.id, type: 'collection', name: collection!.name });
            setIsMoveModalOpen(true);
          }}
        />
      </div>

      <div className="relative flex items-center mb-[24px]"> 
          <div className="flex-grow border-t border-gray-shade_4"></div>
            <span className="font-sans text-xs px-[8px] bg-dark-mode-background text-gray-shade_7">Add Content</span>
          <div className="flex-grow border-t border-gray-shade_4"></div>
      </div>

      <IngestRowContainer
        ingestArxivUrl={window.apiUrls.api_ingest_arxiv}
        ingestPdfUrl={window.apiUrls.api_ingest_pdf}
        collectionId={collectionId}
      />

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
        onMove={handleContextMove}
        onContextMenuRename={handleRenameItem}
      />

      {/* Move Modal for moving the current collection */}
      <MoveCollectionModal
        folder={movingItem as Folder}       // the collection or document being moved
        collections={allCollections.filter(collection => collection.id !== movingItem?.id)} // full list of collections with parent information
        isOpen={isMoveModalOpen}
        onClose={() => { setIsMoveModalOpen(false); setMovingItem(null); }}
        onSubmit={handleMoveSubmit} // your move handler that calls the API
      />
    </div>
  );
};

export default CollectionView;
