from django.shortcuts import render
from rest_framework import viewsets, status, generics, views
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count
from .models import File, PhysicalFile, calculate_sha256
from .serializers import FileSerializer
from .filters import FileFilter

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

    # Overriding destroy to handle physical file cleanup
    def perform_destroy(self, instance):
        """
        Delete the logical file instance.
        If it's the last logical file pointing to the physical file,
        delete the physical file record and the actual file from storage.
        """
        try:
            # Get the related physical file before deleting the logical instance
            physical_file = instance.physical_file
            
            # Delete the logical file instance first
            super().perform_destroy(instance)

            # Check if any other logical files reference the same physical file
            if not File.objects.filter(physical_file=physical_file).exists():
                # If not, delete the physical file from storage and the database record
                # Ensure file exists before attempting delete to avoid errors
                if physical_file.file:
                    physical_file.file.delete(save=False) # Delete file from storage, False to prevent model save
                physical_file.delete() # Delete PhysicalFile database record
                print(f"Deleted physical file: {physical_file.hash}") # Optional logging

        except Exception as e:
            # Log the error or handle appropriately
            print(f"Error during custom destroy for File {instance.id}: {e}")
            # Consider raising the exception again or returning an error response
            # depending on desired behavior if cleanup fails.
            # For now, we let the logical file deletion succeed even if cleanup fails.
            # If the super().perform_destroy() was already called, the logical file is gone.
            pass

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
