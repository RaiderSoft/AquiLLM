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
    padding: '2rem',
    borderRadius: '32px',
    borderColor: '#7777777',
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
    marginBottom: '1.5rem',
    color: '#eeeeee',
  },
  breadcrumb: {
    marginBottom: '1rem',
    fontSize: '0.9rem',
    color: '#555',
  },
  list: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    border: '1px solid #e2e8f0',
    borderRadius: '4px',
    maxHeight: '300px',
    overflowY: 'auto',
  },
  listItem: {
    padding: '0.75rem 1rem',
    borderBottom: '1px solid #e2e8f0',
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
  },
  button: {
    padding: '0.5rem 1rem',
    borderRadius: '0.375rem',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  cancelButton: {
    backgroundColor: '#e2e8f0',
    color: '#4a5568',
    border: 'none',
  },
  submitButton: {
    backgroundColor: '#3182ce',
    color: 'white',
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
      <div style={modalStyles.content}>
        <h3 style={modalStyles.title}>Move Collection</h3>
        {/* Breadcrumb Navigation */}
        <div style={modalStyles.breadcrumb}>
          {breadcrumb.length > 0 ? (
            <>
              <button onClick={handleGoBack} style={{ marginRight: '16px' }}>
                ← Back
              </button>
              {breadcrumb.map((b, idx) => (
                <span key={b.id}>
                  {b.name}{idx < breadcrumb.length - 1 ? ' / ' : ''}
                </span>
              ))}
            </>
          ) : (
            <span className='text-accent-light'>Root Level</span>
          )}
        </div>

        {/* List of collections at the current level */}
        <ul style={modalStyles.list}>
          {currentItems.map(item => (
            <li
              key={item.id}
              style={modalStyles.listItem}
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
            style={{ ...modalStyles.button, ...modalStyles.cancelButton }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSelectCurrent}
            style={{ ...modalStyles.button, ...modalStyles.submitButton }}
          >
            Select This Folder
          </button>
        </div>
      </div>
    </div>
  );
};

export default MoveCollectionModal;
