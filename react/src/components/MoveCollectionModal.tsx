import React, { useState, useMemo } from 'react';
import { Folder } from './CollectionsTree';
import { FileSystemItem } from '../types/FileSystemItem';

interface MoveCollectionModalProps {
  folder: Folder | null; // The collection being moved
  collections: Folder[]; // All available collections (including nested ones)
  isOpen: boolean;       // Modal visibility
  onClose: () => void;
  onSubmit: (folderId: number, newParentId: number | null) => void;
}

/* Example inline modal styles */
const modalStyles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    backdropFilter: 'blur(10px)',
  },
  content: {
    backgroundColor: '#333333',
    padding: '1rem',
    borderRadius: '32px',
    width: '100%',
    maxWidth: '600px',
    position: 'relative' as const,
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    font: 'sans',
    color: '#eeeeee',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    color: '#eeeeee',
  },
  breadcrumb: {
    marginBottom: '1rem',
    fontSize: '1rem',
    color: '#555',
    width: '100%'
  },
  list: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    borderRadius: '8px',
    border: '1px solid #777777',
    maxHeight: '300px',
    overflowy: 'auto',
  },
  listItem: {
    padding: '0.75rem 1rem',
    cursor: 'pointer',
  },
  listItemHover: {
    backgroundColor: '#f7fafc',
  },
  buttonContainer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '0.75rem',
    marginTop: '1.5rem',
    marginBottom: '.5rem',
  },
  button: {
    padding: '0.5rem 1rem',
    borderRadius: '20px',
    fontSize: '0.875rem',
    cursor: 'pointer',
  },
  cancelButton: {
    color: '#eeeeee',
    border: 'none',
  },
  submitButton: {
    color: 'eeeeee',
    border: 'none',
  },
};

const MoveCollectionModal: React.FC<MoveCollectionModalProps> = ({
  folder,
  collections,
  isOpen,
  onClose,
  onSubmit,
}) => {
  // currentParentId represents the folder whose children we're browsing.
  // null means we’re at the root level.
  const [currentParentId, setCurrentParentId] = useState<number | null>(null);

  // Compute the list of collections that have currentParentId as their parent.
  const currentItems = useMemo(() => {
    return collections.filter(col => col.parent === currentParentId);
  }, [collections, currentParentId]);

  // Build breadcrumb from currentParentId up to the root.
  const buildBreadcrumb = (parentId: number | null): Folder[] => {
    if (parentId === null) return [];
    const parentFolder = collections.find(col => col.id === parentId);
    if (!parentFolder) return [];
    return [...buildBreadcrumb(parentFolder.parent), parentFolder];
  };
  const breadcrumb = buildBreadcrumb(currentParentId);

  // Handler when user clicks on a folder in the list to drill down.
  const handleItemClick = (item: FileSystemItem) => {
    // Only allow drilling down if the item is a collection.
    if (item.type === 'collection') {
      setCurrentParentId(item.id);
    }
  };

  // "Select This Folder" button will select the current folder (i.e. currentParentId)
  const handleSelectCurrent = () => {
    onSubmit(folder!.id, currentParentId);
  };

  // Back button to go up one level.
  const handleGoBack = () => {
    if (currentParentId !== null) {
      const parentFolder = collections.find(col => col.id === currentParentId);
      setCurrentParentId(parentFolder ? parentFolder.parent : null);
    }
  };

  if (!isOpen || !folder) return null;

  return (
    <div style={modalStyles.overlay}>
      <div style={modalStyles.content} className='border-gray-shade_7 border flex flex-col items-center justify-left'> 

        <h3 style={modalStyles.title}>Move Collection</h3>

        {/* Breadcrumb Navigation */}
        <div style={modalStyles.breadcrumb} className='flex flex-col items-center justify-center'>
          <span className='text-gray-shade_a'>
            <strong>{folder.name}</strong> will be moved to:
          </span>
          <div>          
            {breadcrumb.length > 0 ? (
            <>      
              {breadcrumb.map((b, idx) => (
                <span key={b.id} className="text-accent-light">
                  {b.name}{idx < breadcrumb.length - 1 ? ' / ' : ''}
                </span>
              ))}
            </>
            ) : (
              <span className='text-accent-light'>Root</span>
            )}
          </div>
        </div>

        <div className='w-full flex justify-left'>
          <button onClick={handleGoBack} style={{ marginRight: '32px' }} className='text-gray-shade_a hover:bg-gray-shade_6 transition-all rounded-[8px] p-[4px] mb-[8px]'>
                  ← Back
          </button>
        </div>

        {/* List of collections at the current level */}
        <ul style={modalStyles.list} className='w-full'>
          {currentItems.map(item => (
            <li
              key={item.id}
              style={modalStyles.listItem}
              className='hover:bg-gray-shade_4 transition-all rounded-[8px]'
              onClick={() => handleItemClick({ id: item.id, type: 'collection', name: item.name })}
            >
              {item.name}
            </li>
          ))}
          {currentItems.length === 0 && (
            <li style={{ padding: '0.75rem 1rem', color: '#999' }}>
              No sub-collections here.
            </li>
          )}
        </ul>

        {/* Action Buttons */}
        <div style={modalStyles.buttonContainer}>
          <button
            type="button"
            onClick={onClose}
            className='bg-gray-shade_6'
            style={{ ...modalStyles.button, ...modalStyles.cancelButton }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSelectCurrent}
            className='bg-accent'
            style={{ ...modalStyles.button, ...modalStyles.submitButton }}
          >
            Select This Location
          </button>
        </div>
      </div>
    </div>
  );
};

export default MoveCollectionModal;
