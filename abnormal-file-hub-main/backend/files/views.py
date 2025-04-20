from django.shortcuts import render
from rest_framework import viewsets, status, generics, views
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count
from .models import File, PhysicalFile, calculate_sha256
from .serializers import FileSerializer
from .filters import FileFilter
import os # Import the os module
from django.conf import settings # To get MEDIA_ROOT if needed (though .path should be absolute)

# Create your views here.

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = {
            'file': file_obj,
            'original_filename': file_obj.name,
            'file_type': file_obj.content_type,
            'size': file_obj.size
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class FileListCreateView(generics.ListCreateAPIView):
    """ API view to list all files or upload a new file with deduplication. Supports filtering. """
    queryset = File.objects.all().select_related('physical_file').order_by('-uploaded_at')
    serializer_class = FileSerializer
    filterset_class = FileFilter

    def create(self, request, *args, **kwargs):
        """ Handle file upload with deduplication logic. """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate hash before proceeding
        try:
            file_hash = calculate_sha256(file_obj)
        except Exception as e:
            # Handle potential errors during hash calculation (e.g., read errors)
            return Response({'error': f'Error calculating file hash: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Use transaction to ensure atomicity
        try:
            with transaction.atomic():
                # Check if physical file with this hash already exists
                physical_file, created = PhysicalFile.objects.get_or_create(
                    hash=file_hash,
                    defaults={
                        'file': file_obj, # Pass the file object here
                        'size': file_obj.size,
                        'content_type': file_obj.content_type,
                    }
                )
                
                # If created is True, the file object was saved by get_or_create
                # If created is False, the file object we have is temporary and won't be saved

                # Create the logical file entry
                # Use original_name from request data if provided, otherwise use filename
                original_name = request.data.get('original_name', file_obj.name)
                
                logical_file_data = {
                    'physical_file': physical_file.pk,
                    'original_name': original_name
                }
                
                serializer = self.get_serializer(data=logical_file_data)
                serializer.is_valid(raise_exception=True)
                # Pass physical_file instance to save method if needed, although pk should be enough
                # self.perform_create(serializer, physical_file=physical_file)
                saved_logical_file = serializer.save() # physical_file_id is set from validated_data

        except Exception as e:
             # Catch potential database errors or other issues
            return Response({'error': f'Error processing file upload: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return the serialized data of the *logical* file
        # Re-serialize the saved instance to include related data (like file_url)
        final_serializer = self.get_serializer(saved_logical_file)
        headers = self.get_success_headers(final_serializer.data)
        return Response(final_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # perform_create is not strictly needed if we handle creation fully in create()
    # def perform_create(self, serializer, physical_file):
    #     serializer.save(physical_file=physical_file)

class FileRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    """ API view to retrieve details of a logical file or delete it. """
    queryset = File.objects.all().select_related('physical_file')
    serializer_class = FileSerializer
    # lookup_field = 'id' # or pk, default is pk

    def perform_destroy(self, instance):
        """
        Delete the logical file instance.
        If it's the last logical file pointing to the physical file,
        delete the physical file record, the actual file from storage,
        and attempt to clean up the empty parent directory.
        """
        try:
            physical_file = instance.physical_file
            should_delete_physical = not File.objects.filter(physical_file=physical_file).exclude(pk=instance.pk).exists()

            if should_delete_physical:
                # Get the full path before deleting the file object
                try:
                    physical_file_path = physical_file.file.path
                except ValueError:
                    # Handle cases where the file might already be missing from storage
                    physical_file_path = None 
                except Exception as e:
                    print(f"Error getting physical file path for {physical_file.pk}: {e}")
                    physical_file_path = None

            # Delete the logical file instance first (this might trigger signals if any)
            super().perform_destroy(instance) 

            # Now, handle physical file and directory cleanup if necessary
            if should_delete_physical:
                # Delete the physical file from storage if path was found
                if physical_file_path and physical_file.file and os.path.exists(physical_file_path):
                    try:
                        physical_file.file.delete(save=False) # Delete file from storage
                        print(f"Deleted physical file from storage: {physical_file_path}")
                    except Exception as e:
                        print(f"Error deleting physical file from storage {physical_file_path}: {e}")
                        physical_file_path = None # Cannot attempt dir cleanup if file delete failed
                
                # Delete PhysicalFile database record AFTER storage deletion attempt
                try:
                    physical_file.delete() 
                    print(f"Deleted PhysicalFile record: PK {physical_file.pk}, Hash {physical_file.hash}")
                except Exception as e:
                     print(f"Error deleting PhysicalFile record {physical_file.pk}: {e}")
                     # Decide if we should still attempt directory cleanup - probably not if DB delete failed.
                     physical_file_path = None 

                # Attempt to remove the parent directory if file deletion was successful
                if physical_file_path:
                    try:
                        directory_path = os.path.dirname(physical_file_path)
                        prefix_dir_path = None # Initialize prefix path
                        if os.path.exists(directory_path) and not os.listdir(directory_path):
                            prefix_dir_path = os.path.dirname(directory_path) # Get prefix path before removing hash dir
                            os.rmdir(directory_path)
                            print(f"Removed empty hash directory: {directory_path}")
                            
                            # Now, check and remove the prefix directory if it's empty
                            if prefix_dir_path and os.path.exists(prefix_dir_path) and not os.listdir(prefix_dir_path):
                                try:
                                    os.rmdir(prefix_dir_path)
                                    print(f"Removed empty prefix directory: {prefix_dir_path}")
                                except OSError as e_prefix:
                                    print(f"Could not remove prefix directory {prefix_dir_path}: {e_prefix}")
                                except Exception as e_prefix_general:
                                    print(f"Error during prefix directory cleanup {prefix_dir_path}: {e_prefix_general}")
                                    
                    except OSError as e:
                        # Directory might not be empty, or permission error
                        print(f"Could not remove hash directory {directory_path}: {e}")
                    except Exception as e:
                         print(f"Error during directory cleanup for {directory_path}: {e}")

        except PhysicalFile.DoesNotExist:
            # The physical file was already deleted somehow, ensure logical is gone
             print(f"PhysicalFile not found for logical file {instance.pk}, ensuring logical delete completes.")
             if File.objects.filter(pk=instance.pk).exists():
                 super().perform_destroy(instance)
        except Exception as e:
            print(f"General error during custom destroy for File {instance.id}: {e}")
            # Ensure logical file deletion still proceeds if possible
            if File.objects.filter(pk=instance.pk).exists():
                try:
                    super().perform_destroy(instance)
                except Exception as final_e:
                     print(f"Failed to ensure logical file deletion after error: {final_e}")
            # Re-raise the original error maybe? Or log it.

# New View for Storage Statistics
class StorageStatsView(views.APIView):
    """ API view to retrieve storage statistics. """

    def get(self, request, *args, **kwargs):
        """ Calculate and return storage stats. """
        try:
            # Total size if all files were stored without deduplication
            logical_aggregation = File.objects.select_related('physical_file').aggregate(
                total_logical_size=Sum('physical_file__size'),
                count=Count('id')
            )
            total_logical_size = logical_aggregation.get('total_logical_size') or 0
            logical_file_count = logical_aggregation.get('count') or 0

            # Actual size stored (sum of unique physical files)
            physical_aggregation = PhysicalFile.objects.aggregate(
                total_physical_size=Sum('size'),
                count=Count('id')
            )
            total_physical_size = physical_aggregation.get('total_physical_size') or 0
            physical_file_count = physical_aggregation.get('count') or 0

            # Calculate savings
            storage_savings = total_logical_size - total_physical_size

            stats = {
                'logical_file_count': logical_file_count,
                'physical_file_count': physical_file_count,
                'total_logical_size_bytes': total_logical_size,
                'total_physical_size_bytes': total_physical_size,
                'storage_savings_bytes': storage_savings,
            }
            return Response(stats, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error appropriately
            print(f"Error calculating storage stats: {e}")
            return Response({"error": "Could not calculate storage statistics."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
