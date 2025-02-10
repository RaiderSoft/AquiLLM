/**
 * Modal component for moving collections to different locations
 * @module MoveCollectionModal
 */

import React, { useState } from 'react';
import { Folder } from './CollectionsTree';

interface MoveCollectionModalProps {
  folder: Folder | null;                                    // Collection to be moved
  collections: Folder[];                                    // Available target collections
  isOpen: boolean;                                         // Controls modal visibility
  onClose: () => void;                                     // Callback when modal is closed
  onSubmit: (folderId: number, newParentId: number | null) => void; // Callback when move is confirmed
}

/**
 * Modal dialog for moving a collection to a new parent
 * @param props - Component properties
 * @param props.folder - Collection being moved
 * @param props.collections - Available collections to move to
 * @param props.isOpen - Whether the modal is visible
 * @param props.onClose - Function to call when modal should close
 * @param props.onSubmit - Function to call with move details
 */
const MoveCollectionModal: React.FC<MoveCollectionModalProps> = ({ 
  folder, 
  collections, 
  isOpen, 
  onClose, 
  onSubmit 
}) => {
  const [newParentId, setNewParentId] = useState<number | null>(null);

  if (!isOpen || !folder) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(folder.id, newParentId);
  };

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
    },
    content: {
      backgroundColor: 'white',
      padding: '2rem',
      borderRadius: '8px',
      width: '100%',
      maxWidth: '400px',
      position: 'relative' as const,
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    },
    title: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      marginBottom: '1.5rem',
      color: '#1a1a1a',
    },
    form: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1rem',
    },
    label: {
      display: 'block',
      marginBottom: '0.5rem',
      color: '#4a5568',
      fontWeight: 500,
    },
    select: {
      width: '100%',
      padding: '0.75rem',
      border: '1px solid #e2e8f0',
      borderRadius: '0.375rem',
      fontSize: '1rem',
      color: '#1a1a1a',
      backgroundColor: 'white',
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
    }
  };

  return (
    <div style={modalStyles.overlay}>
      <div style={modalStyles.content}>
        <h3 style={modalStyles.title}>Move Collection</h3>
        <form onSubmit={handleSubmit} style={modalStyles.form}>
          <div>
            <label htmlFor="parentSelect" style={modalStyles.label}>
              Select New Parent
            </label>
            <select
              id="parentSelect"
              style={modalStyles.select}
              onChange={(e) => setNewParentId(e.target.value ? parseInt(e.target.value) : null)}
              defaultValue=""
            >
              <option value="">Move to root</option>
              {collections
                .filter(col => col.id !== folder.id) // Prevent moving to itself
                .map(col => (
                  <option key={col.id} value={col.id}>
                    {col.name}
                  </option>
                ))
              }
            </select>
          </div>
          <div style={modalStyles.buttonContainer}>
            <button
              type="button"
              onClick={onClose}
              style={{ ...modalStyles.button, ...modalStyles.cancelButton }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ ...modalStyles.button, ...modalStyles.submitButton }}
            >
              Move
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MoveCollectionModal; 