import React, { useState } from 'react';
import { Folder } from './CollectionsTree';

interface MoveCollectionModalProps {
  folder: Folder | null; // the folder to move
  collections: Folder[]; // available collections for new parent selection
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (folderId: number, newParentId: number | null) => void;
}

const MoveCollectionModal: React.FC<MoveCollectionModalProps> = ({ folder, collections, isOpen, onClose, onSubmit }) => {
  const [newParentId, setNewParentId] = useState<number | null>(null);

  if (!isOpen || !folder) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(folder.id, newParentId);
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      <div style={{ backgroundColor: 'white', padding: '1rem', borderRadius: '8px', width: '300px' }}>
        <h3 style={{ marginBottom: '1rem' }}>Move Collection</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="parentSelect">Select New Parent</label>
            <select
              id="parentSelect"
              style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem' }}
              onChange={(e) => setNewParentId(e.target.value ? parseInt(e.target.value) : null)}
              defaultValue=""
            >
              <option value="">Move to root</option>
              {collections.map(col => {
                if (folder.id === col.id) return null; // avoid moving a folder under itself
                return (
                  <option key={col.id} value={col.id}>
                    {col.name}
                  </option>
                );
              })}
            </select>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={{ marginRight: '0.5rem' }}>
              Cancel
            </button>
            <button type="submit">
              Move
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MoveCollectionModal; 