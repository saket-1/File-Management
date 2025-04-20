from django.contrib import admin
from .models import File

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'content_type', 'uploaded_at')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('name',)
    readonly_fields = ('size', 'content_type', 'uploaded_at', 'file_url')

    def file_url(self, obj):
        # Method to display file_url in admin
        from django.utils.html import format_html
        if obj.file:
            return format_html("<a href='{url}' target='_blank'>{url}</a>", url=obj.file.url)
        return "-"
    file_url.short_description = "File URL" 