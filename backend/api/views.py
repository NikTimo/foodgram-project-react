from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import viewsets, filters, status
from rest_framework.permissions import (
    IsAuthenticated, SAFE_METHODS,
)
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import CustomUserPagionation, CustomPecipePagionation
from api.permissions import IsAuthorOrAdminPermission
from api.serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer, RecipeSafeMethodSerializer,
    SubscribeSerializer, RecipeShortSerializer
)
from users.models import User, Subscribe
from recipes.models import (
    Tag, Recipe,
    Ingredient, Favorite, ShoppingCart, IngredientRecipe
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminPermission,)
    pagination_class = CustomPecipePagionation
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSafeMethodSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        if self.request.method == 'POST':
            if Favorite.objects.filter(
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).exists():
                return Response({
                    'errors': 'Рецепт уже добавлен'
                }, status=status.HTTP_400_BAD_REQUEST)

            Favorite.objects.create(
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            )
            return Response(
                RecipeShortSerializer(
                    get_object_or_404(Recipe, pk=pk),
                    context={'request': request}
                ).data, status=status.HTTP_201_CREATED
            )
        if self.request.method == 'DELETE':
            if not Favorite.objects.filter(
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).exists():
                return Response({
                    'errors': 'Рецепт не добавлен в избранное'
                }, status=status.HTTP_400_BAD_REQUEST)
            get_object_or_404(
                Favorite,
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if self.request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).exists():
                return Response({
                    'errors': 'Рецепт уже добавлен в корзину'
                }, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            )
            return Response(
                RecipeShortSerializer(
                    get_object_or_404(Recipe, pk=pk),
                    context={'request': request}
                ).data, status=status.HTTP_201_CREATED
            )
        if self.request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).exists():
                return Response({
                    'errors': 'Рецепт не добавлен в корзину'
                }, status=status.HTTP_400_BAD_REQUEST)
            get_object_or_404(
                ShoppingCart,
                user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        if not ShoppingCart.objects.filter(user=self.request.user).exists():
            return Response({
                'errors': 'Ваша корзина пуста'
            }, status=status.HTTP_400_BAD_REQUEST)
        ingredient_list = IngredientRecipe.objects.filter(
            recipe__shoppingcart__user_id=request.user.id
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        print_list = ''
        print_list += '\n'.join([
            f'{i + 1}. {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for i, ingredient in enumerate(ingredient_list)
        ])
        res = HttpResponse(print_list, content_type='text/plain')
        res['Content-Disposition'] = (
            'attachment; filename=your_shopping_list'
        )
        return res


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class CustomDjoserUserViewSet(UserViewSet):
    pagination_class = CustomUserPagionation

    def get_queryset(self):
        return User.objects.all()

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            SubscribeSerializer(
                self.paginate_queryset(
                    User.objects.filter(
                        following__subscriber_id=self.request.user.id
                    )
                ),
                many=True,
                context={'request': request}
            ).data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        if self.request.method == 'POST':
            if Subscribe.objects.filter(
                subscriber=self.request.user,
                author=get_object_or_404(User, pk=id)
            ).exists():
                return Response({
                    'errors': 'Подписка уже существует'
                }, status=status.HTTP_400_BAD_REQUEST)
            if self.request.user == get_object_or_404(User, pk=id):
                return Response({
                    'errors': 'Не выйдет подписаться самого на себя'
                }, status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.create(
                subscriber=self.request.user,
                author=get_object_or_404(User, pk=id)
            )
            return Response(SubscribeSerializer(
                get_object_or_404(User, pk=id), context={'request': request}
            ).data,
                status=status.HTTP_201_CREATED
            )
        if self.request.method == 'DELETE':
            if not Subscribe.objects.filter(
                subscriber=self.request.user,
                author=get_object_or_404(User, pk=id)
            ).exists():
                return Response({
                    'errors': 'Подписка еще не оформлена'
                }, status=status.HTTP_400_BAD_REQUEST)
            get_object_or_404(
                Subscribe,
                subscriber=self.request.user,
                author=get_object_or_404(User, pk=id)
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
