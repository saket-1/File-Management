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

// Example: Type definition for a File object (adjust based on actual API response)
export interface ApiFile {
  id: string; // Assuming UUID is string
  name: string;
  file_url: string;
  size: number;
  content_type: string;
  uploaded_at: string; // ISO date string
}

// Function to fetch the list of files
export const getFiles = async (): Promise<ApiFile[]> => {
  const response = await apiClient.get<ApiFile[]>('/files/');
  return response.data;
};

// Function to upload a file
export const uploadFile = async (file: File): Promise<ApiFile> => {
  const formData = new FormData();
  formData.append('file', file);

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

// Add functions for getFileDetails if needed later

export default apiClient; 