from django.shortcuts import render
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from .models import File
from .serializers import FileSerializer

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
    """ API view to list all files or upload a new file. """
    queryset = File.objects.all().order_by('-uploaded_at')
    serializer_class = FileSerializer

    # Additional logic for setting content_type on upload might go here
    # in perform_create method.

class FileRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    """ API view to retrieve details of a file or delete it. """
    queryset = File.objects.all()
    serializer_class = FileSerializer
    # lookup_field = 'id' # or pk, depending on URL conf
