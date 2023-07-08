from django.contrib import admin

from recipes.models import (
    Ingredient, Recipe, Tag, Favorite, ShoppingCart, IngredientRecipe
)


class IngredientRecipeAdmin(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags',)
    inlines = (IngredientRecipeAdmin,)


admin.site.register(Ingredient, IngridientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
