from django_filters import rest_framework
from rest_framework import filters

from recipes.models import Recipe, Tag


class IngredientFilter(filters.SearchFilter):
    search_param = "name"


class RecipeFilter(rest_framework.FilterSet):
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = rest_framework.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(in_favorites__user_id=self.request.user.id)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(in_shopping_list__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
