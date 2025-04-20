import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FileList } from './FileList';

// Mock the API service (minimal mock to prevent actual calls)
jest.mock('../services/api', () => ({
  getFiles: jest.fn(() => new Promise(() => {})), // Mock getFiles to never resolve during this simple test
  deleteFile: jest.fn(),
}));

// Minimal QueryClient for rendering context
const queryClient = new QueryClient();

describe('FileList Component Basic Render', () => {
  test('renders file list header', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <FileList />
      </QueryClientProvider>
    );
    // Check if the main header text is present
    expect(screen.getByText('Uploaded Files')).toBeInTheDocument();
  });
}); 