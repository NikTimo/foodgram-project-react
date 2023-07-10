import base64

from django.db import transaction
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from recipes.models import (
    Tag, Recipe, Ingredient,
    IngredientRecipe, Favorite, ShoppingCart
)
from users.models import User, Subscribe


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomDjoserUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 'password'
        )


class CustomDjoserUserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            subscriber=self.context['request'].user, author=obj
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount',)


class IngredientsRecipeSafeMethodSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeSafeMethodSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    author = CustomDjoserUserSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        return IngredientsRecipeSafeMethodSerializer(
            IngredientRecipe.objects.filter(recipe=obj),
            many=True
        ).data

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=self.context['request'].user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=self.context['request'].user, recipe=obj
        ).exists()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeSerializer(RecipeSafeMethodSerializer):
    ingredients = IngredientsRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False
    )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user, **validated_data
        )
        recipe.tags.set(tags)
        ingredient_recipe_list = []
        for ingredient in ingredients:
            ingredient_recipe_list.append(
                IngredientRecipe(
                    ingredient_id=ingredient['id'],
                    recipe=recipe,
                    amount=ingredient['amount']
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_recipe_list)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        instance.ingredients.clear()
        ingredient_recipe_list = []
        for ingredient in ingredients:
            ingredient_recipe_list.append(
                IngredientRecipe(
                    ingredient_id=ingredient['id'],
                    recipe=instance,
                    amount=ingredient['amount']
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_recipe_list)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSafeMethodSerializer(
            instance, context={'request': self.context.get('request')}
        ).data

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                'Вы не добавили ни одного ингредиента.'
            )
        ids = [ingredient['id'] for ingredient in data]
        if not len(set(ids)) == len(ids):
            raise serializers.ValidationError(
                'В списке ингредиентов есть повторяющиеся элементы.'
            )
        return data


class RecipeShortSerializer(RecipeSafeMethodSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscribeSerializer(CustomDjoserUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        return RecipeShortSerializer(
            Recipe.objects.filter(author=obj),
            context={'request': self.context.get('request')},
            many=True
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'recipes', 'recipes_count',
        )
