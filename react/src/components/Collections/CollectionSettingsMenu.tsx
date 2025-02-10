/**
 * Dropdown menu component for collection actions
 * @module CollectionSettingsMenu
 */

import React, { useState, useRef, useEffect } from 'react';
import { Folder } from './CollectionsTree';

interface CollectionSettingsMenuProps {
  collection: Folder;                        // Collection to manage
  onMove: (collection: Folder) => void;      // Callback for move action
  onDelete: (collection: Folder) => void;    // Callback for delete action
  onManageCollaborators: (collection: Folder) => void; // Callback for managing collaborators
}

/**
 * Renders a dropdown menu with collection management options
 * @param props - Component properties
 * @param props.collection - Collection being managed
 * @param props.onMove - Function to call when move is selected
 * @param props.onDelete - Function to call when delete is selected
 * @param props.onManageCollaborators - Function to call when manage collaborators is selected
 */
const CollectionSettingsMenu: React.FC<CollectionSettingsMenuProps> = ({
  collection,
  onMove,
  onDelete,
  onManageCollaborators,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Handle clicks outside the menu to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={menuRef} style={{ position: 'relative' }}>
      <button
        style={{ background: 'none', border: 'none', cursor: 'pointer' }}
        onClick={() => setIsOpen(!isOpen)}
      >
        ⚙️
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          right: 0,
          top: '100%',
          backgroundColor: '#2d2d2d',
          borderRadius: '0.375rem',
          boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
          padding: '0.5rem',
          zIndex: 10,
          minWidth: '200px',
        }}>
          <button
            onClick={() => {
              onManageCollaborators(collection);
              setIsOpen(false);
            }}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '0.5rem 1rem',
              border: 'none',
              backgroundColor: 'transparent',
              color: 'white',
              cursor: 'pointer',
              borderRadius: '0.25rem',
            }}
          >
            👥 Manage Collaborators
          </button>
          <button
            onClick={() => {
              onMove(collection);
              setIsOpen(false);
            }}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '0.5rem 1rem',
              border: 'none',
              backgroundColor: 'transparent',
              color: 'white',
              cursor: 'pointer',
              borderRadius: '0.25rem',
            }}
          >
            📦 Move Collection
          </button>
          <button
            onClick={() => {
              onDelete(collection);
              setIsOpen(false);
            }}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '0.5rem 1rem',
              border: 'none',
              backgroundColor: 'transparent',
              color: '#ef4444',
              cursor: 'pointer',
              borderRadius: '0.25rem',
            }}
          >
            🗑️ Delete
          </button>
        </div>
      )}
    </div>
  );
};

export default CollectionSettingsMenu; 