import React, { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { FileList } from './components/FileList';
import { StorageStats } from './components/StorageStats';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { useQueryClient } from '@tanstack/react-query';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
    queryClient.invalidateQueries({ queryKey: ['storageStats'] });
  };

  const queryClient = useQueryClient();

  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster position="top-center" reverseOrder={false} />

      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">Abnormal Security - File Hub</h1>
          <p className="mt-1 text-sm text-gray-500">
            File management system
          </p>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="mb-6 bg-white shadow sm:rounded-lg">
          <StorageStats />
        </div>
        <div className="px-4 py-6 sm:px-0">
          <div className="space-y-6">
            <div className="bg-white shadow sm:rounded-lg">
              <FileUpload onUploadSuccess={handleUploadSuccess} />
            </div>
            <div className="bg-white shadow sm:rounded-lg">
              <FileList key={refreshKey} />
            </div>
          </div>
        </div>
      </main>
      <footer className="bg-white shadow mt-8">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            © 2024 File Hub. All rights reserved.
          </p>
        </div>
      </footer>

      {/* React Query DevTools - only renders in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </div>
  );
}

export default App;
