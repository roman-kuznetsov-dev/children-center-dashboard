from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Club, User

# Регистрируем Клубы
admin.site.register(Club)

# Регистрируем Пользователей с кастомными настройками
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'club')
    list_filter = ('role', 'club')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'club')}),
    )

admin.site.register(User, CustomUserAdmin)