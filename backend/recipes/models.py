from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from core.generator import generate_short_url
from core.validators import RecipeValidators
from users.models import User


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
        User,
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
        related_name='recipes',
        validators=[MinValueValidator(1)]
    )
    image = models.ImageField(
        upload_to="recipes/",
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
        validators=[MinValueValidator(1),
                    MaxValueValidator(500)],
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)
    short_url = models.URLField(unique=True, null=True, blank=True)

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f'Рецепт {self.name}, автор {self.author}'

    def save(self, *args, **kwargs):
        """Генерация короткой ссылки."""
        if not self.short_url:
            self.short_url = generate_short_url()
        super().save(*args, **kwargs)


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
        validators=[MinValueValidator(1)]
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


class AbstractUserRecipe(models.Model):
    """Абстрактная модель для связывания пользователя и рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        help_text="Рецепт, связанный с пользователем",
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            ),
        )

    def __str__(self):
        return f"Рецепт: {self.recipe.name}, Пользователь: {self.user}"


class Favorite(AbstractUserRecipe):
    """Модель для сохранения избранных рецептов."""

    class Meta(AbstractUserRecipe.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            ),
        )

    def __str__(self):
        return f"Рецепт в избранном: {self.recipe.name}"


class ShoppingCart(AbstractUserRecipe):
    """Модель для списка покупок пользователя."""

    class Meta(AbstractUserRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('-recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cart'
            ),
        )

    def __str__(self):
        return f"Рецепт в списке у {self.user}"
