import React, { useState, useMemo, useEffect } from 'react';
import { FileSystemItem } from '../types/FileSystemItem';
import { FolderIcon } from '../icons/folder';
import { DocumentIcon } from '../icons/document';
import { Folder } from './CollectionsTree';
import ContextMenu from './CustomContextMenu';

// Props for the FileSystemViewer
interface FileSystemViewerProps {
  mode: 'browse' | 'select';                   // The current mode
  items: FileSystemItem[];                     // The items (collections/documents) to display
  collection: Folder;                           // The current collection
  onOpenItem?: (item: FileSystemItem) => void; // Callback when a user clicks a row to "open" or navigate
  onRemoveItem?: (item: FileSystemItem) => void;  // Callback for removing/deleting an item
  onSelectCollection?: (item: FileSystemItem) => void; // Callback for selecting a collection (in select mode)
  onMove?: (item: FileSystemItem) => void; // Callback for moving a collection (in browse mode)
  onContextMenuRename?: (item: FileSystemItem) => void; // Callback for renaming a collection (in browse mode)
}

const FileSystemViewer: React.FC<FileSystemViewerProps> = ({
  mode,
  items,
  collection,
  onOpenItem,
  onRemoveItem,
  onSelectCollection,
  onMove,
  onContextMenuRename,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Filter items by search query
  const filteredItems = useMemo(() => {
    if (!searchQuery) return items;
    return items.filter(item =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [items, searchQuery]);

  // Define a state to track the custom context menu
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean;
    x: number;
    y: number;
    item: FileSystemItem | null;
  }>({ visible: false, x: 0, y: 0, item: null });

  // Handler for right-click on an item:
  const handleContextMenu = (e: React.MouseEvent, item: FileSystemItem) => {
    e.preventDefault();
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      item,
    });
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      // You might add logic to check if the click was outside the context menu
      if (contextMenu.visible) {
        setContextMenu({ visible: false, x: 0, y: 0, item: null });
      }
    };
  
    if (contextMenu.visible) {
      document.addEventListener('click', handleClickOutside);
    }
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [contextMenu.visible]);

  const getIconForType = (type: string) => {

    switch (type) {
      case 'collection':
        return <FolderIcon />
      case 'PDFDocument':
        return <DocumentIcon />;
    }

  };

  // Handle checkbox toggles
  const handleToggleSelect = (itemId: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const getTextColorForType = (type: string) => {
    if (type === 'collection') return '#A5CCF3'; // Blue
    return '#F49071'; // Orange (for everything else)
  };

  // A convenience function to see if all displayed items are selected
  const allDisplayedSelected = filteredItems.every(item => selectedIds.has(item.id));

  // Toggle select-all for items currently displayed
  const handleToggleSelectAll = () => {
    if (allDisplayedSelected) {
      // Unselect all
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        filteredItems.forEach(item => newSet.delete(item.id));
        return newSet;
      });
    } else {
      // Select all
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        filteredItems.forEach(item => newSet.add(item.id));
        return newSet;
      });
    }
  };

  // Render “Manage” column content depending on mode/item type
  const renderManageCell = (item: FileSystemItem) => {
    // In browse mode, show "Remove" button for all items
    if (mode === 'browse') {
      return (
        <button
          className='text-red'
          style={{
            borderRadius: '0.25rem',
            border: 'none',
            cursor: 'pointer'
          }}
          onClick={(e) => {
            e.stopPropagation();
            onRemoveItem?.(item);
          }}
        >
          Remove
        </button>
      );
    }

    // In select mode, if the item is a collection, show "Select" button
    if (mode === 'select' && item.type === 'collection') {
      return (
        <button
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: '#4b5563',
            color: 'white',
            borderRadius: '0.25rem',
            border: 'none',
            cursor: 'pointer'
          }}
          onClick={(e) => {
            e.stopPropagation();
            onSelectCollection?.(item);
          }}
        >
          Select
        </button>
      );
    }

    // Otherwise, no action in select mode for non-collection items
    return null;
  };

  return (
    <div style={{ backgroundColor: '#292929', borderRadius: '36px' }} className='font-sans border border-gray-shade_6 overflow-hidden'>
      {/* Top Bar: Search, etc. */}
      <div style={{ display: 'flex', justifyContent: 'space-between'}} className='bg-gray-shade_4 p-[16px] border-b border-b-gray-shade_6'>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className='bg-gray-shade_4 border border-gray-shade_7 placeholder:text-gray-shade_b rounded-[20px]'
            style={{
              padding: '0.5rem',
            }}
          />
        </div>
        
        <span className='flex items-center text-align-center text-gray-shade_a text-sm'>
            Root/{collection.path}
        </span>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#555555',
              color: '#eeeeee',
              borderRadius: '22px',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            Add Content
          </button>
          <button
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#555555',
              color: '#eeeeee',
              borderRadius: '22px',
              border: 'none',
              cursor: 'pointer'
            }}
            onClick={() => {
              // Example bulk remove
              const selectedItems = items.filter(i => selectedIds.has(i.id));
              selectedItems.forEach(item => onRemoveItem?.(item));
              setSelectedIds(new Set());
            }}
          >
            Remove
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflow: 'auto' }}>
        <table style={{ width: '100%', height: '100%', borderCollapse: 'collapse'}}>
          <thead className='bg-gray-shade_4'>
            <tr className='border-b border-b-gray-shade_6 h-[40px] max-h-[40px]'>
              <th style={{ textAlign: 'left' }} className='h-full flex items-center justify-left'>
                <input
                  type="checkbox"
                  checked={allDisplayedSelected && filteredItems.length > 0}
                  onChange={handleToggleSelectAll}
                  style={{
                    zIndex: 100,
                    appearance: 'none',         // Standard
                    WebkitAppearance: 'none',   // Chrome, Safari
                    MozAppearance: 'none',      // Firefox
                    backgroundColor: "#555555",
                    border: "1px solid #777777",
                    borderRadius: "4px",
                    width: '16px',
                    height: '16px',
                    marginLeft: "1rem"
                  }}
                />
              </th>
              <th style={{ textAlign: 'left' }}>Type</th>
              <th style={{ textAlign: 'left' }}>Name</th>
              <th style={{ textAlign: 'left' }}>Manage</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => {
              const isSelected = selectedIds.has(item.id);
              return (
                <tr
                    key={item.id}
                    onContextMenu={(e) => handleContextMenu(e, item)}
                    className='h-[40px] max-h-[40px] hover:bg-gray-shade_3 transition-colors'
                    style={{
                        borderBottom: '1px solid #555555',
                        cursor: 'pointer',                      
                        color: getTextColorForType(item.type),
                    }}
                    onClick={() => {
                        onOpenItem?.(item);
                    }}
                >
                    <td style={{ textAlign: 'left'  }}>
                      <input
                          type="checkbox"
                          style={{
                            zIndex: 100,
                            appearance: 'none',         // Standard
                            WebkitAppearance: 'none',   // Chrome, Safari
                            MozAppearance: 'none',      // Firefox
                            backgroundColor: "#555555",
                            border: "1px solid #777777",
                            borderRadius: "4px",
                            width: '16px',
                            height: '16px',
                            marginLeft: "1rem"
                          }}
                          checked={isSelected}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleToggleSelect(item.id);
                          }}
                        />
                    </td>

                    <td style={{ textAlign: 'left', fontSize: '14px' }} className='flex justify-left items-center gap-[16px] h-full'>
                        {getIconForType(item.type)}
                        {item.type}
                    </td>
                    <td style={{ textAlign: 'left', fontSize: '14px'  }}>{item.name}</td>
                    <td style={{ textAlign: 'left', fontSize: '14px'  }}>{renderManageCell(item)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {contextMenu.visible && contextMenu.item && (
          <ContextMenu
            x={contextMenu.x}
            y={contextMenu.y}
            item={contextMenu.item}
            onClose={() => setContextMenu({ visible: false, x: 0, y: 0, item: null })}
            onViewDetails={(item) => {
              // Implement viewing details
              console.log('View details for', item);
            }}
            onRename={(item) => {
              // Implement renaming logic (e.g. open a rename modal)
              console.log('Rename', item);
              onContextMenuRename?.(item);
            }}
            onMove={(item) => {
              console.log('Move', item);
              onMove?.(item);
            }}
          />
        )}

      </div>

      {/* Pagination Controls (placeholder) */}
      <div
       className='text-gray-shade_e'
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          gap: '1rem',
          padding: '1rem',
        }}
      >
        <span>Rows per page: 10</span>
        <button style={{ background: 'none', border: 'none', color: '#eeeeee' }}>←</button>
        <button style={{ background: 'none', border: 'none', color: '#eeeeee' }}>→</button>
      </div>
    </div>
  );
};

export default FileSystemViewer;
