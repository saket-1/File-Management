from rest_framework import serializers
from .models import File, PhysicalFile

class FileSerializer(serializers.ModelSerializer):
    """ Serializer for the File (logical file) model. """
    file_url = serializers.SerializerMethodField()
    size = serializers.ReadOnlyField(source='physical_file.size')
    content_type = serializers.ReadOnlyField(source='physical_file.content_type')
    extension = serializers.ReadOnlyField(source='physical_file.extension')
    # Field to indicate if it's a known duplicate (optional, might impact performance)
    # is_duplicate = serializers.ReadOnlyField()

    # Make physical_file writeable by primary key for the view's create logic
    physical_file = serializers.PrimaryKeyRelatedField(queryset=PhysicalFile.objects.all(), write_only=True)
    # Expose original_name for reading and potentially writing if needed directly
    original_name = serializers.CharField(max_length=255)

    class Meta:
        model = File
        fields = [
            'id',
            'original_name', # Use original_name from the model
            'physical_file', # Write-only FK field
            'file_url',      # Read-only absolute URL (via method field)
            'size',          # Read-only from PhysicalFile
            'content_type',  # Read-only from PhysicalFile
            'extension',     # Add extension to fields
            'uploaded_at',   # Read-only from File
            # 'is_duplicate' # Optional field
        ]
        # Read-only fields for the API response (excluding write-only physical_file FK)
        read_only_fields = ['id', 'file_url', 'size', 'content_type', 'extension', 'uploaded_at', 'is_duplicate']

    def get_file_url(self, obj):
        """ Build the absolute URL using the physical file. """
        request = self.context.get('request')
        # Access url via the physical_file relation
        if obj.physical_file and obj.physical_file.file and request:
            return request.build_absolute_uri(obj.physical_file.file.url)
        return None

    # Removed validate_file - validation now happens before PhysicalFile creation in the view
    # Removed custom create - view now handles PhysicalFile lookup/creation and passes FK 