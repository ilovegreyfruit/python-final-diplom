from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, Shop, Category, Product, ProductInfo

# Снимаем регистрацию стандартной модели Group
admin.site.unregister(Group)


class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'type', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_active', 'type', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('type', 'company', 'position')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'type', 'is_active', 'is_staff', 'is_superuser')}
         ),
    )

    search_fields = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


admin.site.register(User, UserAdmin)
admin.site.register(Shop)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductInfo)