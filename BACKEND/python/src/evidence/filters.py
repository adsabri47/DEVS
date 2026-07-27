import django_filters
from .models import Evidence

class EvidenceFilter(django_filters.FilterSet):
    """
    This class acts as the 'Search Engine' for our evidence vault.
    It allows investigators to narrow down thousands of files into specific sets.
    """

    # --- DATE RANGE FILTERING ---
    # We're setting up 'start' and 'end' boundaries here.
    # 'gte' (Greater Than or Equal) and 'lte' (Less Than or Equal) let us
    # look for evidence captured within a specific window of time.
    start_date = django_filters.DateTimeFilter(field_name="uploaded_at", lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name="uploaded_at", lookup_expr='lte')
    
    # --- TEXT SEARCH ---
    # 'icontains' makes the search case-insensitive.
    # If an investigator types 'cctv', it will find 'CCTV', 'Cctv', and 'cctv_footage'.
    title = django_filters.CharFilter(lookup_expr='icontains')
    
    # --- ATTRIBUTE FILTERING ---
    # This allows us to drill down into who specifically logged the exhibit 
    # by looking up their unique User ID.
    uploaded_by = django_filters.NumberFilter(field_name="uploaded_by__id")

    class Meta:
        # We're telling the filter exactly which model to scan 
        # and providing a few extra shorthand fields like file type (mime_type).
        model = Evidence
        fields = ['mime_type', 'title', 'uploaded_by']