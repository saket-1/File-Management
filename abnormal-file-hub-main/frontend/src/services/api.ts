import axios from 'axios';

// Retrieve the API base URL from environment variables
// Fallback to localhost:8000/api for development if not set
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create an Axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // 'Accept': 'application/json', // Often default, but can be explicit
  },
  // withCredentials: true, // Uncomment if using sessions/cookies for auth
});

// --- API Service Functions ---

// Type definition for File object from API
export interface ApiFile {
  id: string;
  original_name: string; // Renamed from 'name' to match backend model/serializer
  file_url: string;
  size: number;
  content_type: string;
  extension: string;    // Add extension field
  uploaded_at: string;
  // is_duplicate?: boolean; // Optional: if exposed by serializer
}

// Type definition for Storage Stats object from API
export interface StorageStats {
  logical_file_count: number;
  physical_file_count: number;
  total_logical_size_bytes: number;
  total_physical_size_bytes: number;
  storage_savings_bytes: number;
}

// Type for filter parameters
// Note: Should match the keys defined in backend FileFilter
interface ApiFileFilters {
  original_name?: string;
  extension?: string; // Changed from content_type
  min_size?: number;
  max_size?: number;
  start_date?: string; // Expecting YYYY-MM-DD format
  end_date?: string;   // Expecting YYYY-MM-DD format
}

// Function to fetch the list of files, now accepts filters
export const getFiles = async (filters?: ApiFileFilters): Promise<ApiFile[]> => {
  // Pass filters as query parameters
  const response = await apiClient.get<ApiFile[]>('/files/', {
    params: filters // Axios automatically handles serialization of params
  });
  return response.data;
};

// Function to upload a file
export const uploadFile = async (file: File): Promise<ApiFile> => {
  const formData = new FormData();
  formData.append('file', file);
  // Optional: could add original_name to form data if needed by backend explicitly
  // formData.append('original_name', file.name);

  const response = await apiClient.post<ApiFile>('/files/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Function to delete a file
export const deleteFile = async (fileId: string): Promise<void> => {
  await apiClient.delete(`/files/${fileId}/`);
};

// Function to fetch storage statistics
export const getStorageStats = async (): Promise<StorageStats> => {
  const response = await apiClient.get<StorageStats>('/storage-stats/');
  return response.data;
};

// Add functions for getFileDetails if needed later

export default apiClient; 