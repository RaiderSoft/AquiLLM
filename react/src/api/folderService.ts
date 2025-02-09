import { Folder } from '../types/folder';

/**
 * Fetches folder data from the Django backend.
 * 
 * @returns {Promise<Folder[]>} - A promise that resolves to an array of Folder objects.
 * @throws {Error} - Throws an error if the network response is not ok.
 */
export const getFolders = async (): Promise<Folder[]> => {
  // Point to Django backend running on port 8080
  const response = await fetch('http://localhost:8080/api/collections/', {
    credentials: 'include', // include auth cookies if necessary
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch folders: ${response.statusText}`);
  }

  const data: Folder[] = await response.json();
  return data;
}; 