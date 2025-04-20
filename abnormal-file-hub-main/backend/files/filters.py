import django_filters
from .models import File

class FileFilter(django_filters.FilterSet):
    """ FilterSet for the File (logical file) model. """

    # Filter by original filename (case-insensitive contains)
    original_name = django_filters.CharFilter(lookup_expr='icontains')

    # Filter by content type (exact match, case-insensitive)
    content_type = django_filters.CharFilter(
        field_name='physical_file__content_type',
        lookup_expr='iexact'
    )

    # Filter by size range (using field_name to access physical_file.size)
    min_size = django_filters.NumberFilter(field_name='physical_file__size', lookup_expr='gte')
    max_size = django_filters.NumberFilter(field_name='physical_file__size', lookup_expr='lte')

    # Filter by upload date range
    start_date = django_filters.DateFilter(field_name='uploaded_at', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='uploaded_at', lookup_expr='date__lte')

    class Meta:
        model = File
        # Define fields available for filtering
        # Note: We defined custom filters above for more control, but could list basic fields here too.
        fields = [
            'original_name',
            'content_type',
            'min_size', 
            'max_size',
            'start_date',
            'end_date'
        ] 