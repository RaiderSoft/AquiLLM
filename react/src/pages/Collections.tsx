import React, { useEffect, useState } from 'react';
import CollectionsTree from '../components/Collections/CollectionsTree';
import { getFolders } from '../api/folderService';
import { Folder } from '../types/folder';

/**
 * Collections Page Container Component
 * 
 * This is a container (page-level) component responsible for:
 * 1. Fetching folder data from the Django backend using our service layer
 * 2. Managing loading and error states
 * 3. Passing the folder data to the presentational CollectionsTree component
 */
const Collections: React.FC = () => {
  // State management for folders data, loading state, and potential errors
  const [folders, setFolders] = useState<Folder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Effect hook to fetch folder data when component mounts
  useEffect(() => {
    // Define an asynchronous function to fetch folder data using the service layer
    const fetchFolders = async () => {
      try {
        const data = await getFolders();
        setFolders(data);
        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching folders:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchFolders();
  }, []); // Empty dependency array means this effect runs once on mount

  // Show loading state while fetching data
  if (loading) return <div>Loading collections...</div>;
  
  // Show error message if data fetch failed
  if (error) return <div>Error loading collections: {error}</div>;

  // Render the collections page with the folder tree
  return (
    <div>
      <h1>Collections</h1>
      {/* Pass the fetched folder data to our presentational component */}
      <CollectionsTree folders={folders} />
    </div>
  );
};

export default Collections; 