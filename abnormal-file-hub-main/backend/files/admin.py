from django.contrib import admin
from .models import File, PhysicalFile

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'get_content_type', 'get_size', 'uploaded_at', 'physical_file_hash')
    # list_filter = ('uploaded_at',) # Cannot easily filter by content_type now
    search_fields = ('original_name', 'physical_file__hash')
    readonly_fields = ('id', 'physical_file', 'uploaded_at', 'file_url', 'get_content_type', 'get_size', 'physical_file_hash')
    list_select_related = ('physical_file',)

    def get_content_type(self, obj):
        return obj.content_type # Use the property
    get_content_type.short_description = 'Content Type'

    def get_size(self, obj):
        # Format size nicely
        size = obj.size
        if size is None: return '-'
        if size < 1024: return f'{size} B'
        if size < 1024**2: return f'{size/1024:.1f} KB'
        if size < 1024**3: return f'{size/1024**2:.1f} MB'
        return f'{size/1024**3:.1f} GB'
    get_size.short_description = 'Size'

    def file_url(self, obj):
        from django.utils.html import format_html
        url = obj.file_url # Use the property
        if url:
            return format_html("<a href='{url}' target='_blank'>{url}</a>", url=url)
        return "-"
    file_url.short_description = "File URL"

    def physical_file_hash(self, obj):
        return obj.physical_file.hash[:12] + '...' if obj.physical_file else '-'
    physical_file_hash.short_description = "Physical Hash (Truncated)"

# Optionally register PhysicalFile model for admin view too
@admin.register(PhysicalFile)
class PhysicalFileAdmin(admin.ModelAdmin):
    list_display = ('hash', 'size', 'content_type', 'first_uploaded')
    search_fields = ('hash',)
    readonly_fields = ('hash', 'file', 'size', 'content_type', 'first_uploaded') 