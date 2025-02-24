import React from 'react';
import { FileSystemItem } from '../types/FileSystemItem';

interface ContextMenuProps {
  x: number;
  y: number;
  item: FileSystemItem;
  onClose: () => void;
  onViewDetails: (item: FileSystemItem) => void;
  onRename: (item: FileSystemItem) => void;
  onMove: (item: FileSystemItem) => void;
  onRemove: (item: FileSystemItem) => void;
}

const ContextMenu: React.FC<ContextMenuProps> = ({
  x,
  y,
  item,
  onClose,
  onViewDetails,
  onRename,
  onMove,
  onRemove,
}) => {
  return (
    <div
      style={{
        position: 'fixed',
        top: y,
        left: x,
        backgroundColor: '#444444',
        boxShadow: '0px 2px 8px rgba(0,0,0,0.2)',
        border: '1px solid #777777',
        borderRadius: '8px',
        zIndex: 2000,
      }}
      onMouseLeave={onClose}
    >
      <ul style={{ listStyle: 'none', padding: '8px', margin: 0 }}>
        <li
          style={{ padding: '4px 8px', cursor: 'pointer' }}
          onClick={() => { onViewDetails(item); onClose(); }}
        >
          View Details
        </li>
        <li
          style={{ padding: '4px 8px', cursor: 'pointer' }}
          onClick={() => { onRename(item); onClose(); }}
        >
          Rename
        </li>
        <li
          style={{ padding: '4px 8px', cursor: 'pointer' }}
          onClick={() => { onMove(item); onClose(); }}
        >
          Move
        </li>
        <li
          style={{ padding: '4px 8px', cursor: 'pointer' }}
          className="text-red"
          onClick={() => { onRemove(item); onClose(); }}
        >
          Remove
        </li>
      </ul>
    </div>
  );
};

export default ContextMenu;