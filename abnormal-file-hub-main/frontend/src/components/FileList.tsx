import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getFiles, deleteFile, ApiFile } from '../services/api';
import { ArrowDownTrayIcon, TrashIcon } from '@heroicons/react/24/outline';

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const FileList: React.FC<{ key?: number }> = () => {
  const queryClient = useQueryClient();

  // Query to fetch files
  const { data: files, isLoading, error } = useQuery<ApiFile[], Error>({
    queryKey: ['files'],
    queryFn: getFiles,
  });

  // Mutation to delete a file
  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: deleteFile,
    onSuccess: () => {
      // Invalidate and refetch the files query on success
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
    // Optional: Add onError handling
    // onError: (err) => { alert(`Error deleting file: ${err.message}`); }
  });

  const handleDelete = (fileId: string) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      deleteMutation.mutate(fileId);
    }
  };

  if (isLoading) {
    return <div className="text-center p-4">Loading files...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-600">Error loading files: {error.message}</div>;
  }

  if (!files || files.length === 0) {
    return <div className="text-center p-4 text-gray-500">No files uploaded yet.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <h2 className="text-xl font-semibold mb-4 px-4 pt-4">Uploaded Files</h2>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uploaded At</th>
            <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {files.map((file) => (
            <tr key={file.id}>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{file.name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatFileSize(file.size)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{file.content_type}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(file.uploaded_at).toLocaleString()}</td>
              <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium space-x-2">
                <a
                  href={file.file_url} // Use the direct file URL from the backend
                  target="_blank"      // Open in new tab
                  rel="noopener noreferrer"
                  download // Suggests download, browser behavior may vary
                  className="text-indigo-600 hover:text-indigo-900 inline-flex items-center"
                  title="Download"
                >
                  <ArrowDownTrayIcon className="h-5 w-5" aria-hidden="true" />
                </a>
                <button
                  onClick={() => handleDelete(file.id)}
                  disabled={deleteMutation.isPending && deleteMutation.variables === file.id}
                  className={`text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed inline-flex items-center ${deleteMutation.isPending && deleteMutation.variables === file.id ? 'animate-pulse' : ''}`}
                  title="Delete"
                >
                  <TrashIcon className="h-5 w-5" aria-hidden="true" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}; 