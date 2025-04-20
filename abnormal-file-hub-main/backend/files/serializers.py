from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import File

# Define the size limit (e.g., 10MB)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

class FileSerializer(serializers.ModelSerializer):
    """ Serializer for the File model. """
    # file_url = serializers.ReadOnlyField() # Changed from ReadOnlyField
    file_url = serializers.SerializerMethodField() # Use MethodField to build absolute URL

    class Meta:
        model = File
        fields = [
            'id',
            'name',
            'file',      # Note: This might expose internal path, consider carefully
            'file_url',  # Public absolute URL
            'size',
            'content_type',
            'uploaded_at'
        ]
        read_only_fields = ['id', 'size', 'content_type', 'uploaded_at', 'file_url'] # Add id and file_url here too

    def validate_file(self, value):
        """ Check if the uploaded file size exceeds the limit. """
        if value.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(f"File size cannot exceed {MAX_UPLOAD_SIZE // 1024 // 1024}MB.")
        return value

    def get_file_url(self, obj):
        """ Build the absolute URL for the file. """
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None # Return None if file or request is not available

    def create(self, validated_data):
        """ Override create to potentially set content_type from uploaded file. """
        uploaded_file = self.context['request'].FILES.get('file')
        if uploaded_file:
            validated_data['content_type'] = uploaded_file.content_type
            # validated_data['size'] = uploaded_file.size # Size is set in model's save
            if 'name' not in validated_data or not validated_data['name']: # Set name from filename if not provided
                 validated_data['name'] = uploaded_file.name

        return super().create(validated_data) 