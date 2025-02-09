export interface Folder {
  id: number;
  name: string;
  parent: number | null;  // null for root-level folders
  collection: number;     // ID of the collection this folder belongs to
  path: string;          // full path of the folder (e.g., "root/subfolder/current")
  children: Folder[];    // nested folders
  document_count: number;
  created_at: string;
  updated_at: string;
} 