from django.db import models
import uuid
import os
import hashlib

def file_upload_path(instance, filename):
    """Generate file path for new file upload"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

def get_upload_path(instance, filename):
    """ Determine upload path dynamically if needed """
    # Example: return os.path.join('uploads', instance.user.username, filename)
    return os.path.join('uploads', filename)

# Function to define upload path based on hash
def physical_file_upload_path(instance, filename):
    """ Store physical files in a structure based on their hash """
    if not instance.hash:
        # Hash might not be set yet during initial save, use a temporary name?
        # Or better, ensure hash is calculated *before* this is called.
        # For now, let's assume hash will be set.
        return f'physical_files/{instance.hash[:2]}/{instance.hash[2:]}/{filename}'
    # Fallback or error needed if hash is None
    ext = filename.split('.')[-1]
    return f'physical_files/{instance.hash[:2]}/{instance.hash[2:]}/{instance.hash}.{ext}'

class PhysicalFile(models.Model):
    """ Represents the actual stored file data, identified by hash. """
    hash = models.CharField(max_length=64, unique=True, db_index=True) # SHA-256 hash
    file = models.FileField(upload_to=physical_file_upload_path)
    size = models.BigIntegerField(editable=False)
    content_type = models.CharField(max_length=255, editable=False) # Store type here too
    first_uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hash

class File(models.Model):
    """ Represents a user's logical file upload, linking to physical data. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    physical_file = models.ForeignKey(PhysicalFile, on_delete=models.PROTECT, related_name='logical_files')
    # Store the name given by the user at upload time
    original_name = models.CharField(max_length=255, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Optional: Add user ForeignKey if auth is implemented
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    # We can get size, content_type, and the actual file URL via physical_file
    @property
    def name(self):
        return self.original_name

    @property
    def size(self):
        return self.physical_file.size

    @property
    def content_type(self):
        return self.physical_file.content_type

    @property
    def file_url(self):
        if self.physical_file and self.physical_file.file:
            return self.physical_file.file.url
        return None
    
    @property
    def is_duplicate(self):
        """ Check if this logical file is a duplicate (more than one logical file points to the same physical file) """
        # This might be inefficient to calculate on the fly for lists.
        # Consider denormalizing or calculating differently if performance is an issue.
        return self.physical_file.logical_files.count() > 1

    def __str__(self):
        return f'{self.original_name} ({self.physical_file.hash[:8]}...)'

    class Meta:
        ordering = ['-uploaded_at']


def calculate_sha256(file_obj):
    """ Calculates SHA-256 hash of a file-like object chunk by chunk. """
    sha256_hash = hashlib.sha256()
    file_obj.seek(0) # Ensure reading from the start
    for chunk in file_obj.chunks():
        sha256_hash.update(chunk)
    file_obj.seek(0) # Reset pointer for subsequent use (e.g., saving)
    return sha256_hash.hexdigest()
