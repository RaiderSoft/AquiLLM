import React, { useState } from 'react';
import { Folder } from './CollectionsTree';

interface CreateCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (newCollection: Folder) => void;
}

const CreateCollectionModal: React.FC<CreateCollectionModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [name, setName] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    const newCollection: Folder = {
      id: Date.now(), // temporary ID, will be replaced by server
      name: name.trim(),
      parent: null,
      collection: 0,
      path: name.trim(),
      children: [],
      document_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    onSubmit(newCollection);
    setName('');
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
    input: {
      width: '100%',
      padding: '0.75rem',
      border: '1px solid #e2e8f0',
      borderRadius: '0.375rem',
      fontSize: '1rem',
      color: '#1a1a1a',
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
        <h3 style={modalStyles.title}>Create New Collection</h3>
        <form onSubmit={handleSubmit} style={modalStyles.form}>
          <div>
            <label htmlFor="collectionName" style={modalStyles.label}>
              Collection Name
            </label>
            <input
              id="collectionName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={modalStyles.input}
              placeholder="Enter collection name"
              autoFocus
            />
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
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateCollectionModal; 