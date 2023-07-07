from rest_framework.pagination import PageNumberPagination
from foodgram.settings import USER_PAG_PAGE_SIZE, RECIPE_PAG_PAGE_SIZE


class CustomUserPagionation(PageNumberPagination):
    page_size = USER_PAG_PAGE_SIZE
    page_size_query_param = 'limit'


class CustomPecipePagionation(PageNumberPagination):
    page_size = RECIPE_PAG_PAGE_SIZE
    page_size_query_param = 'limit'
