/**
 * CollectionsTree Component
 * 
 * A presentational component that renders a hierarchical tree of folders.
 * This component is responsible for the visual representation of folders
 * and their nested structure (similar to a file explorer).
 */

import React, { useState } from 'react';

/**
 * Represents a collection/folder in the system
 * @interface Folder
 */
export interface Folder {
  id: number;
  name: string;
  parent: number | null;  // Parent collection ID, null if root-level
  collection: number;     // Reference to the collection this folder belongs to
  path: string;          // Full path in format: "parent/child/grandchild"
  children: Folder[];    // Nested collections
  document_count: number;
  created_at: string;
  updated_at: string;
}

// Define props for CollectionsTree, adding onMoveCollection callback
interface CollectionsTreeProps {
  folders: Folder[];
  onMoveCollection: (folder: Folder) => void;
}

/**
 * Renders a hierarchical tree view of collections
 * @param props - Component properties
 * @param props.folders - Array of folders to display
 * @param props.onMoveCollection - Callback when a collection is moved
 */
const CollectionsTree: React.FC<CollectionsTreeProps> = ({ folders, onMoveCollection }) => {
  if (!folders || folders.length === 0) return <div>No folders found.</div>;
  
  return (
    <ul style={{ listStyleType: 'none', paddingLeft: '1rem' }}>
      {folders.map((folder) => (
        <FolderItem key={folder.id} folder={folder} onMoveCollection={onMoveCollection} />
      ))}
    </ul>
  );
};

// Define props for FolderItem
interface FolderItemProps {
  folder: Folder;
  onMoveCollection: (folder: Folder) => void;
}

/**
 * Individual folder item component with expand/collapse functionality
 * @param props - Component properties
 * @param props.folder - Folder data to display
 * @param props.onMoveCollection - Callback when move action is triggered
 */
const FolderItem: React.FC<FolderItemProps> = ({ folder, onMoveCollection }) => {
  // State to track whether this folder's children are currently visible
  const [expanded, setExpanded] = useState<boolean>(false);

  return (
    <li>
      {/* Clickable folder row with expand/collapse functionality and a Move button */}
      <div
        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {/* Folder expansion indicator (▼ when expanded, ▶ when collapsed, • for leaf nodes) */}
          <span style={{ marginRight: '0.5rem' }}>
            {folder.children && folder.children.length > 0 
              ? (expanded ? '▼' : '▶') 
              : '•'}
          </span>
          {/* Folder name and document count */}
          <span>
            {folder.name} ({folder.document_count} documents)
          </span>
        </div>
        {/* Move button added next to folder name. Stopping propagation so click does not toggle expand/collapse. */}
        <button 
          onClick={(e) => { 
            e.stopPropagation(); 
            onMoveCollection(folder); 
          }} 
          style={{ marginLeft: 'auto' }}
        >
          Move
        </button>
      </div>
      
      {/* Recursively render child folders when expanded */}
      {expanded && folder.children && folder.children.length > 0 && (
        <CollectionsTree folders={folder.children} onMoveCollection={onMoveCollection} />
      )}
    </li>
  );
};

export default CollectionsTree; 