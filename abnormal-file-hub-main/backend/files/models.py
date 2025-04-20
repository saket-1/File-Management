from django.db import models
import uuid
import os

def file_upload_path(instance, filename):
    """Generate file path for new file upload"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

def get_upload_path(instance, filename):
    """ Determine upload path dynamically if needed """
    # Example: return os.path.join('uploads', instance.user.username, filename)
    return os.path.join('uploads', filename)

class File(models.Model):
    """ Represents an uploaded file. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=get_upload_path) # Changed to use function for flexibility
    size = models.BigIntegerField(editable=False) # Size in bytes, set automatically
    content_type = models.CharField(max_length=100, editable=False) # MIME type, set automatically
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """ Automatically populate name, size, and content_type on save. """
        if not self.name:
            self.name = os.path.basename(self.file.name)
        if self.file:
            self.size = self.file.size
            # Attempt to get content type, handle potential errors
            try:
                # Accessing file content might be needed for accurate type detection
                # but can be inefficient. Django often relies on filename extension.
                # For more robust detection, libraries like python-magic could be used.
                # self.content_type = magic.from_buffer(self.file.read(1024), mime=True)
                # For now, rely on Django's FileField handling or set manually if needed.
                # We can also extract from the uploaded file object if available during upload view.
                pass # Placeholder, content_type might be set in the view/serializer
            except Exception:
                self.content_type = 'application/octet-stream' # Default fallback

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def file_url(self):
        """ Returns the public URL for the file. """
        if self.file:
            return self.file.url
        return None
