from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class CustomUserPagionation(PageNumberPagination):
    page_size = settings.USER_PAG_PAGE_SIZE
    page_size_query_param = 'limit'


class CustomPecipePagionation(PageNumberPagination):
    page_size = settings.RECIPE_PAG_PAGE_SIZE
    page_size_query_param = 'limit'
