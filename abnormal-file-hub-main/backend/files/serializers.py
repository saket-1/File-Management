from rest_framework import serializers
from .models import File

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
        read_only_fields = ['size', 'content_type', 'uploaded_at'] # These are set automatically

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
            if not validated_data.get('name'): # Set name from filename if not provided
                 validated_data['name'] = uploaded_file.name

        return super().create(validated_data) 