import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStorageStats, StorageStats as StorageStatsType } from '../services/api';
import { InformationCircleIcon, CircleStackIcon, ArchiveBoxXMarkIcon } from '@heroicons/react/24/outline';

// Helper function to format file size (same as in FileList)
const formatFileSize = (bytes: number | undefined): string => {
    if (bytes === undefined || bytes === null) return 'N/A';
    // Handle negative savings case gracefully
    if (bytes <= 0) return '0 Bytes'; 
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    if (i >= sizes.length) return `${(bytes / Math.pow(k, sizes.length - 1)).toFixed(1)} ${sizes[sizes.length - 1]}`;
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export const StorageStats: React.FC = () => {
    // Query to fetch storage stats
    const { data: stats, isLoading, error } = useQuery<StorageStatsType, Error>({
        queryKey: ['storageStats'], // Unique query key for stats
        queryFn: getStorageStats,
        staleTime: 1000 * 60 * 5, // Cache stats for 5 minutes, less frequently updated
    });

    // Function to render a single stat item
    const renderStat = (icon: React.ElementType, label: string, value: string | number | undefined, description?: string) => (
        <div className="relative overflow-hidden rounded-lg bg-white px-4 pb-6 pt-5 shadow sm:px-6 sm:pt-6">
            <dt>
                <div className="absolute rounded-md bg-indigo-500 p-3">
                    {React.createElement(icon, { className: "h-6 w-6 text-white", ariaHidden: true })}
                </div>
                <p className="ml-16 truncate text-sm font-medium text-gray-500">{label}</p>
            </dt>
            <dd className="ml-16 flex items-baseline pb-1">
                <p className="text-2xl font-semibold text-gray-900">{value ?? '-'}</p>
            </dd>
            {description && (
                <div className="ml-16 text-xs text-gray-500">{description}</div>
            )}
        </div>
    );

    if (isLoading) {
        return <div className="text-center p-4 text-gray-500">Loading storage stats...</div>;
    }

    if (error) {
        return <div className="text-center p-4 text-red-600">Error loading storage stats: {error.message}</div>;
    }

    if (!stats) {
        return <div className="text-center p-4 text-gray-500">Storage stats unavailable.</div>;
    }

    // Calculate duplicate count safely
    const duplicateReferences = Math.max(0, stats.logical_file_count - stats.physical_file_count);

    return (
        <div className="p-4 md:p-6">
            <h3 className="text-base font-semibold leading-6 text-gray-900 mb-4">Storage Overview</h3>
            <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {renderStat(
                    InformationCircleIcon,
                    'Total Files (Logical)',
                    stats.logical_file_count,
                    `Total potential size: ${formatFileSize(stats.total_logical_size_bytes)}`
                )}
                 {renderStat(
                    CircleStackIcon,
                    'Unique Files Stored (Physical)',
                    stats.physical_file_count,
                    `Actual disk usage: ${formatFileSize(stats.total_physical_size_bytes)}`
                )}
                {renderStat(
                    ArchiveBoxXMarkIcon,
                    'Storage Savings (Deduplication)',
                    formatFileSize(stats.storage_savings_bytes),
                    `${duplicateReferences} duplicate references` // Use safe calculation
                 )}
            </dl>
        </div>
    );
}; 