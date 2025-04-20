import React, { useState, useCallback, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { uploadFile, ApiFile } from '../services/api';
import { ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

interface FileUploadProps {
  onUploadSuccess: () => void; // Callback to notify parent component
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();
  // Create a ref for the file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mutation for uploading the file
  const uploadMutation = useMutation<ApiFile, Error, File>({
    mutationFn: uploadFile,
    onSuccess: (data) => {
      toast.success(`File "${data.original_name}" uploaded successfully!`);
      queryClient.invalidateQueries({ queryKey: ['files'] });
      setSelectedFile(null);
      // Reset file input value
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onUploadSuccess();
      // Explicitly reset the mutation state after success
      uploadMutation.reset();
    },
    onError: (error) => {
      // Extract backend validation error message if available
      let errorMessage = error.message;
      if (axios.isAxiosError(error) && error.response?.data) {
          const responseData = error.response.data;
          if (typeof responseData === 'object' && responseData !== null) {
              if (responseData.detail) {
                  errorMessage = responseData.detail;
              } else if (responseData.file && Array.isArray(responseData.file) && responseData.file.length > 0) {
                  errorMessage = responseData.file[0]; 
              } else {
                  errorMessage = JSON.stringify(responseData);
              }
          }
      }
      toast.error(`Upload failed: ${errorMessage}`);
      console.error('Upload error:', error);
      // Also reset file input value on error
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      // Also reset mutation state on error
      uploadMutation.reset();
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      // Frontend check (optional, backend validation is primary)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (selectedFile.size > maxSize) {
        toast.error('File size exceeds the 10MB limit.');
        return;
      }
      uploadMutation.mutate(selectedFile);
    }
  };

  // Handle drag and drop
  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault(); // Necessary to allow drop
  }, []);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      setSelectedFile(event.dataTransfer.files[0]);
    } else {
      setSelectedFile(null);
    }
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload New File</h2>
      <div 
        className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="space-y-1 text-center">
          <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
          <div className="flex text-sm text-gray-600">
            <label
              htmlFor="file-upload"
              className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
            >
              <span>Upload a file</span>
              {/* Attach the ref to the input */}
              <input 
                ref={fileInputRef} 
                id="file-upload" 
                name="file-upload" 
                type="file" 
                className="sr-only" 
                onChange={handleFileChange} 
              />
            </label>
            <p className="pl-1">or drag and drop</p>
          </div>
          <p className="text-xs text-gray-500">Any file up to 10MB</p> {/* Reflecting README limit */}
        </div>
      </div>

      {selectedFile && (
        <div className="mt-4 flex items-center justify-between bg-gray-50 p-3 rounded-md">
          <p className="text-sm font-medium text-gray-700 truncate">
            Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
          </p>
          <button
            onClick={() => setSelectedFile(null)} // Allow removing selection
            className="ml-4 text-sm font-medium text-red-600 hover:text-red-500"
          >
            Clear
          </button>
        </div>
      )}

      <div className="mt-4 text-right">
        <button
          type="button"
          onClick={handleUpload}
          disabled={!selectedFile || uploadMutation.isPending}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploadMutation.isPending ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Uploading...
            </>
          ) : (
            <>
             <ArrowUpTrayIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
             Upload File
            </>
          )}
        </button>
      </div>
    </div>
  );
}; 