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
  onBatchMove?: (items: FileSystemItem[]) => void; // Callback for moving multiple items at once
  onRemoveBatch?: (items: FileSystemItem[]) => void; // Callback for removing multiple items at once
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
  onBatchMove,
  onRemoveBatch,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [actionMenuOpen, setActionMenuOpen] = useState<boolean>(false);

  // Filter items by search query
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;
    const normalizedQuery = searchQuery.trim().toLowerCase();
    return items.filter(item =>
      item.name.toLowerCase().includes(normalizedQuery)
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
    const handleClickOutside = () => {
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

  // Get selected items
  const selectedItems = useMemo(() => {
    return items.filter(item => selectedIds.has(item.id));
  }, [items, selectedIds]);

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

  // Handle batch operations
  const handleBatchMove = () => {
    const selectedItems = items.filter(i => selectedIds.has(i.id));
    if (selectedItems.length === 0) {
      alert('No items selected');
      return;
    }
    
    onBatchMove?.(selectedItems);
  };

  // Add batch remove handler
  const handleBatchRemove = () => {
    const selectedItems = items.filter(i => selectedIds.has(i.id));
    if (selectedItems.length === 0) {
      alert('No items selected');
      return;
    }
    
    // Call the parent component's handler if provided
    // This would typically be the handleBatchRemoveItems in CollectionView
    if (typeof onRemoveBatch === 'function') {
      onRemoveBatch(selectedItems);
    } else {
      // Fallback: remove items one by one using the onRemoveItem callback
      if (window.confirm(`Are you sure you want to delete ${selectedItems.length} selected items?`)) {
        selectedItems.forEach(item => onRemoveItem?.(item));
        // Clear selection after deletion
        setSelectedIds(new Set());
      }
    }
  };

  // Render "Manage" column content depending on mode/item type
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
        <div className="flex gap-[16px]">
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            {/* Search Icon */}
            <div style={{ position: 'absolute', left: '10px', pointerEvents: 'none' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-shade_b">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            
            {/* Search Input */}
            <input
              type="text"
              placeholder="Search items..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className='bg-gray-shade_4 border border-gray-shade_7 placeholder:text-gray-shade_b rounded-[20px] w-[220px]'
              style={{
                padding: '0.5rem',
                paddingLeft: '2rem',
                paddingRight: searchQuery ? '2rem' : '0.5rem',
                outline: 'none',
              }}
            />
            
            {/* Clear Button */}
            {searchQuery && (
              <div 
                style={{ position: 'absolute', right: '10px', cursor: 'pointer' }}
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-shade_b hover:text-gray-shade_d">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </div>
            )}
          </div>

          {/* Divider between the search bar and current location */}
          <div className='h-full border-r border-gray-shade_6'></div>
          
          <span className='flex items-center text-align-center text-gray-shade_a text-sm'>
              Path: Root/{collection.path}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {/* Batch Operations */}
          <div className="relative">
            <button
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: selectedIds.size > 0 ? '#3182ce' : '#555555', // Highlight if items selected
                color: '#eeeeee',
                borderRadius: '22px',
                border: 'none',
                cursor: 'pointer'
              }}
              onClick={() => setActionMenuOpen(!actionMenuOpen)}
              disabled={selectedIds.size === 0}
            >
              {selectedIds.size > 0 ? `${selectedIds.size} Selected` : 'Select Items'}
            </button>
            
            {/* Dropdown menu for batch actions */}
            {actionMenuOpen && selectedIds.size > 0 && (
              <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-gray-shade_3 ring-1 ring-black ring-opacity-5 z-10">
                <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
                  <button
                    className="block w-full text-left px-4 py-2 text-sm text-gray-shade_e hover:bg-gray-shade_4"
                    role="menuitem"
                    onClick={() => {
                      setActionMenuOpen(false);
                      handleBatchMove();
                    }}
                  >
                    Move Selected
                  </button>
                  <button
                    className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-shade_4"
                    role="menuitem"
                    onClick={() => {
                      setActionMenuOpen(false);
                      handleBatchRemove();
                    }}
                  >
                    Delete Selected
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Batch Actions Bar - only show when items are selected */}
      {selectedIds.size > 0 && mode === 'browse' && (
        <div className="flex items-center justify-between bg-gray-shade_3 p-3 mb-2 rounded-md border border-gray-shade_6 transition-all duration-300 ease-in-out">
          <div className="flex items-center">
            <span className="text-gray-shade_d mr-4">
              <strong>{selectedIds.size}</strong> {selectedIds.size === 1 ? 'item' : 'items'} selected
            </span>
            
            <button
              className="bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 mr-2 rounded flex items-center transition-colors duration-200"
              onClick={() => onBatchMove?.(selectedItems)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m-8 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              Move
            </button>
            
            <button
              className="bg-red-600 hover:bg-red-700 text-white py-1 px-3 rounded flex items-center transition-colors duration-200"
              onClick={handleBatchRemove}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </button>
          </div>
          
          <button
            className="text-gray-shade_b hover:text-gray-shade_d transition-colors duration-200"
            onClick={() => setSelectedIds(new Set())}
            title="Clear selection"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Table */}
      <div style={{ overflow: 'auto' }}>
        <table style={{ width: '100%', height: '100%', borderCollapse: 'collapse'}}>
          <thead className='bg-gray-shade_4'>
            <tr className='border-b border-b-gray-shade_6 h-[40px] max-h-[40px]'>
              <th style={{ textAlign: 'left' }} className='h-full flex items-center justify-left'>
                <div 
                  style={{ 
                    padding: '4px', 
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  className="hover:bg-gray-shade_5 rounded"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleSelectAll();
                  }}
                >
                  <input
                    type="checkbox"
                    checked={allDisplayedSelected && filteredItems.length > 0}
                    onChange={(e) => {
                      e.stopPropagation();
                      handleToggleSelectAll();
                    }}
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      zIndex: 10,
                      appearance: 'none',         // Standard
                      WebkitAppearance: 'none',   // Chrome, Safari
                      MozAppearance: 'none',      // Firefox
                      backgroundColor: allDisplayedSelected && filteredItems.length > 0 ? "#3182ce" : "#555555",
                      border: "1px solid #777777",
                      borderRadius: "4px",
                      width: '16px',
                      height: '16px',
                      marginLeft: "1rem",
                      cursor: 'pointer',
                      position: 'relative',
                    }}
                    className={allDisplayedSelected && filteredItems.length > 0 ? "after:content-['✓'] after:absolute after:text-white after:text-xs after:top-[-1px] after:left-[3px]" : ""}
                  />
                </div>
              </th>
              
              <th style={{ textAlign: 'left' }}>Name</th>
              <th style={{ textAlign: 'left' }}>Type</th>
              <th style={{ textAlign: 'left' }}>Details</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.length > 0 ? (
              filteredItems.map((item) => {
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
                          backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.1)' : 'transparent', // Highlight selected rows
                      }}
                      onClick={() => {
                          onOpenItem?.(item);
                      }}
                  >
                      <td 
                        style={{ textAlign: 'left' }}
                        onClick={(e) => {
                          // Stop propagation at the cell level too
                          e.stopPropagation();
                        }}
                      >
                        <div 
                          style={{ 
                            padding: '4px', 
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                          className="hover:bg-gray-shade_5 rounded"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleSelect(item.id);
                          }}
                        >
                          <input
                              type="checkbox"
                              style={{
                                zIndex: 10,
                                appearance: 'none',         // Standard
                                WebkitAppearance: 'none',   // Chrome, Safari
                                MozAppearance: 'none',      // Firefox
                                backgroundColor: isSelected ? "#3182ce" : "#555555",
                                border: "1px solid #777777",
                                borderRadius: "4px",
                                width: '16px',
                                height: '16px',
                                marginLeft: "1rem",
                                cursor: 'pointer',
                                position: 'relative',
                              }}
                              checked={isSelected}
                              onChange={(e) => {
                                e.stopPropagation();
                                handleToggleSelect(item.id);
                              }}
                              onClick={(e) => {
                                // Ensure click doesn't propagate either
                                e.stopPropagation(); 
                              }}
                              className={isSelected ? "after:content-['✓'] after:absolute after:text-white after:text-xs after:top-[-1px] after:left-[3px]" : ""}
                            />
                        </div>
                      </td>
                      
                      <td style={{ textAlign: 'left', fontSize: '14px'  }}>{item.name}</td>

                      <td style={{ textAlign: 'left', fontSize: '14px' }} className='flex justify-left items-center gap-[16px] h-full'>
                          {getIconForType(item.type)}
                          {item.type}
                      </td>

                      <td style={{ textAlign: 'left', fontSize: '14px'  }}>{item.created_at}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={4} className="text-center py-8 text-gray-shade_a">
                  {searchQuery ? (
                    <div className="flex flex-col items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mb-2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                      </svg>
                      <p>No items match your search for "{searchQuery}"</p>
                      <button 
                        onClick={() => setSearchQuery('')}
                        className="mt-2 text-accent-light hover:underline"
                      >
                        Clear search
                      </button>
                    </div>
                  ) : (
                    <p>No items in this collection</p>
                  )}
                </td>
              </tr>
            )}
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
            onRemove={(item) => {
              {renderManageCell(item)}
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
