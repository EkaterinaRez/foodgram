from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from core.permissions import IsAdminOrReadOnly
from recipes.models import Favorites
from users.models import FoodgramUser

from .serializers import FavoriteSerializer, FoodgramUserSerializer


class FoodgramUserViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления пользователями."""

    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    http_method_names = ("get", "post", "patch", "delete")
    lookup_field = "id"

    @action(
        detail=False,
        methods=("get", "patch"),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        if request.method == "PATCH":
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления избранными рецептами."""

    queryset = Favorites.objects.all()
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
