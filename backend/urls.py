from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from sales.views import SaleOrderViewSet
from users.views import CurrentUserView  # Импортируем новое представление
from sales.webhooks import ofd_webhook

router = DefaultRouter()
router.register(r'orders', SaleOrderViewSet, basename='order')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/me/', CurrentUserView.as_view(), name='current_user'),  # НОВЫЙ ЭНДПОИНТ
    path('api/webhooks/ofd/', ofd_webhook, name='ofd_webhook'),
]