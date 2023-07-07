from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomDjoserUserViewSet,
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet
)

router = DefaultRouter()
router.register('users', CustomDjoserUserViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
