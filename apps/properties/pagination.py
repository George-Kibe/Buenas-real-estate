from rest_framework.pagination import PageNumberPagination


class PropertyPagination(PageNumberPagination):
    # Keep in step with PAGE_SIZE in client/src/app/properties/page.tsx.
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48
