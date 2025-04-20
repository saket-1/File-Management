import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { getFiles, deleteFile, ApiFile } from '../services/api';
import { ArrowDownTrayIcon, TrashIcon, MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import axios from 'axios';
import { useDebounce } from '../hooks/useDebounce'; // Assuming a debounce hook exists/is created

// Define type for filters
interface FileFilters {
  original_name?: string;
  content_type?: string;
  min_size?: number;
  max_size?: number;
  start_date?: string;
  end_date?: string;
  extension?: string;
}

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Helper to remove empty keys from filter object
const cleanFilters = (filters: FileFilters): Record<string, string | number> => {
    const cleaned: Record<string, string | number> = {};
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            cleaned[key] = value;
        }
    });
    return cleaned;
};

export const FileList: React.FC<{ key?: number }> = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<FileFilters>({});
  const debouncedNameFilter = useDebounce(filters.original_name, 500); // Debounce name input

  // Create the final filter object including debounced name
  const activeFilters = useMemo(() => cleanFilters({ 
      ...filters,
      original_name: debouncedNameFilter 
  }), [filters, debouncedNameFilter]);

  // Query to fetch files, passing cleaned filters and using filters in queryKey
  const { data: files, isLoading, error, isFetching } = useQuery<ApiFile[], Error>({
    // Query key includes active filters to trigger refetch on change
    queryKey: ['files', activeFilters],
    queryFn: () => getFiles(activeFilters), // Pass cleaned filters directly
    retry: 1,
    placeholderData: (previousData) => previousData, // Keep old data while fetching new
  });

  const handleFilterChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { name, value } = event.target;
      setFilters(prev => ({
          ...prev,
          [name]: value === '' ? undefined : value, // Store undefined for empty inputs
      }));
  };

  const clearFilters = () => {
      setFilters({});
  };

  // --- Delete Mutation (remains largely the same) ---
  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: deleteFile,
    onSuccess: (_, deletedFileId) => {
      const deletedFileName = queryClient.getQueryData<ApiFile[]>(['files', activeFilters])?.find(f => f.id === deletedFileId)?.original_name || 'File';
      toast.success(`"${deletedFileName}" deleted successfully.`);
      queryClient.invalidateQueries({ queryKey: ['files'] }); // Invalidate file list query
      queryClient.invalidateQueries({ queryKey: ['storageStats'] }); // Invalidate stats query too!
    },
    onError: (error, fileId) => {
       let errorMessage = error.message;
       if (axios.isAxiosError(error) && error.response?.data) {
          const responseData = error.response.data;
          if (typeof responseData === 'object' && responseData !== null && responseData.detail) {
              errorMessage = responseData.detail;
          } else if (typeof responseData === 'string') {
              errorMessage = responseData;
          } 
      } 
      toast.error(`Error deleting file: ${errorMessage}`);
      console.error('Delete error:', error);
    },
  });

  const handleDelete = (fileId: string) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      deleteMutation.mutate(fileId);
    }
  };
  // --- End Delete Mutation ---

  // Display toast on initial load error
  if (error && !files && !isLoading) {
    toast.error(`Error loading files: ${error.message}`, { id: 'loadError' });
    // Return or display error state in the table area
  }

  return (
    <div className="p-4 md:p-6">
      <h2 className="text-xl font-semibold mb-4">Uploaded Files</h2>
      
      {/* Filter Section */}
      <div className="mb-4 p-4 bg-gray-50 rounded-md shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          {/* Filename Search */}
          <div>
            <label htmlFor="original_name" className="block text-sm font-medium text-gray-700">Filename</label>
            <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <input
                    type="text"
                    name="original_name"
                    id="original_name"
                    className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
                    placeholder="Search by name..."
                    value={filters.original_name || ''}
                    onChange={handleFilterChange}
                />
            </div>
          </div>

          {/* Content Type Filter -> Extension Filter */}
          <div>
            <label htmlFor="extension" className="block text-sm font-medium text-gray-700">File Extension</label>
            <input
              type="text"
              name="extension"
              id="extension"
              className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
              placeholder="e.g., pdf, txt, jpg"
              value={filters.extension || ''}
              onChange={handleFilterChange}
            />
          </div>

          {/* Date Range Filter */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">Uploaded After</label>
              <input 
                type="date" 
                name="start_date" 
                id="start_date"
                className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                value={filters.start_date || ''}
                onChange={handleFilterChange}
              />
            </div>
             <div>
              <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">Uploaded Before</label>
              <input 
                type="date" 
                name="end_date" 
                id="end_date"
                className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                value={filters.end_date || ''}
                onChange={handleFilterChange}
              />
            </div>
          </div>

          {/* Size Range Filter (Simplified - two number inputs) */}
          <div className="grid grid-cols-2 gap-2">
             <div>
              <label htmlFor="min_size" className="block text-sm font-medium text-gray-700">Min Size (KB)</label>
              <input 
                type="number"
                name="min_size"
                id="min_size"
                min="0"
                className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="e.g., 100"
                value={filters.min_size !== undefined ? filters.min_size / 1024 : ''} // Display/Edit in KB
                onChange={(e) => setFilters(prev => ({ ...prev, min_size: e.target.value === '' ? undefined : parseInt(e.target.value) * 1024 }))}
              />
            </div>
             <div>
              <label htmlFor="max_size" className="block text-sm font-medium text-gray-700">Max Size (KB)</label>
              <input 
                type="number"
                name="max_size"
                id="max_size"
                min="0"
                className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="e.g., 5000"
                value={filters.max_size !== undefined ? filters.max_size / 1024 : ''} // Display/Edit in KB
                onChange={(e) => setFilters(prev => ({ ...prev, max_size: e.target.value === '' ? undefined : parseInt(e.target.value) * 1024 }))}
              />
            </div>
          </div>

        </div>
          {/* Clear Filters Button */} 
         <div className="mt-4 flex justify-end">
            <button 
                onClick={clearFilters} 
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
               <XMarkIcon className="-ml-0.5 mr-2 h-4 w-4" aria-hidden="true" />
                Clear Filters
            </button>
        </div>
      </div>
      {/* End Filter Section */} 

      {/* File List Table */}
      <div className="overflow-x-auto relative">
       {/* Loading/Fetching Indicator */} 
       {(isLoading || isFetching) && (
           <div className="absolute inset-0 bg-white bg-opacity-50 flex items-center justify-center z-10">
               <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                   <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                   <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
               </svg>
           </div>
       )}

       {error && !isLoading && (
           <div className="text-center p-4 text-red-600 bg-red-50 rounded-md my-4">Error loading files: {error.message}. Please try adjusting filters or refreshing.</div>
       )}

       {(!isLoading && !error && (!files || files.length === 0)) ? (
           <div className="text-center p-6 text-gray-500 bg-white rounded-md shadow-sm my-4">No files match the current filters.</div>
       ) : (
          <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-md shadow-sm">
            {/* Table Head */} 
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uploaded At</th>
                <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            {/* Table Body */}
            <tbody className="bg-white divide-y divide-gray-200">
              {files?.map((file) => (
                <tr key={file.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 max-w-xs truncate" title={file.original_name}>{file.original_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatFileSize(file.size)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate uppercase" title={file.content_type}>
                    {file.extension || 'N/A'} 
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(file.uploaded_at).toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium space-x-2">
                    <a href={file.file_url} target="_blank" rel="noopener noreferrer" download className="text-indigo-600 hover:text-indigo-900 inline-flex items-center" title="Download">
                      <ArrowDownTrayIcon className="h-5 w-5" aria-hidden="true" />
                    </a>
                    <button onClick={() => handleDelete(file.id)} disabled={deleteMutation.isPending && deleteMutation.variables === file.id} className={`text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed inline-flex items-center ${deleteMutation.isPending && deleteMutation.variables === file.id ? 'animate-pulse' : ''}`} title="Delete">
                      <TrashIcon className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
       )}
      </div>
    </div>
  );
}; 