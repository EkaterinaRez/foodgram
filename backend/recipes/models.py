from django.db import models

from core.validators import RecipeValidators
from users.models import FoodgramUser


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(max_length=32, unique=True, verbose_name="Тэг")
    slug = models.SlugField(
        max_length=32,
        unique=True,
        validators=[RecipeValidators.slug_validator],
        verbose_name="Слаг",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=128, unique=True, verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=64, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientForRecipe",
        related_name="recipes",
        verbose_name="Ингредиенты",
        help_text="Выберите ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Теги",
        help_text="Выберите теги",
        related_name='recipes'
    )
    image = models.ImageField(
        upload_to="media/",
        verbose_name="Изображение",
        help_text="Выберите изображение",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
        help_text="Введите название рецепта"
    )
    text = models.TextField(
        verbose_name="Описание", help_text="Введите описание рецепта"
    )

    cooking_time = models.PositiveSmallIntegerField(
        null=False,
        verbose_name="Время приготовления",
        help_text="Введите время приготовления",
        validators=[RecipeValidators.cook_time_validator],
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f'Рецепт {self.name}, автор {self.author}'


class IngredientForRecipe(models.Model):
    """Модель для связи между ингредиентами и рецептами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[RecipeValidators.count_ingredients_validator]
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient'
            ),
        )
        verbose_name = 'Ингредиенты рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'


class Favorite(models.Model):
    """Модель для сохранения избранных рецептов."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='favorites',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name='favorites',
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            ),
        )

    def __str__(self):
        return ("Рецепт в избранном: "
                f"{self.recipe.name}, пользователь: {self.user}")


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
        help_text='Список покупок пользователя'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cart'
            ),
        )
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('-recipe',)

        def __str__(self):
            return f"Рецепт в списке у {self.user}"
