from rest_framework import serializers
from models import *


class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True)
    photo = Base64ImageField(max_length=None, use_url=True)
    # reviews = serializers.SerializerMethodField()
    # comments = serializers.SerializerMethodField()
    # tags = TagSerializer(many=True)

    class Meta:
        model = Recipe

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        # tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(name=ingredient["name"])
            recipe.ingredients.add(ingredient)

        # for tag in tags_data:
        #     tag, created = Tag.objects.get_or_create(name=tag["name"])
        #     recipe.tags.add(tag)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.directions = validated_data.get('directions', instance.directions)
        instance.photo = validated_data.get('photo', instance.photo)

        if hasattr(validated_data, 'ingredients') and len(validated_data.ingredients) > 0:
            instance.ingredients = validated_data.get('ingredients', instance.ingredients)
        instance.save()

        return instance

    def get_reviews(self, obj):
        reviews = Review.objects.filter(recipe=obj.id)
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

    def get_comments(self, current_recipe):
        comments = Comment.objects.filter(recipe=current_recipe.id)
        serializer = CommentSerializer(comments, many=True)
        return serializer.data