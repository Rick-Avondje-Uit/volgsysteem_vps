from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Persoonlijke info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissies'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Belangrijke data'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    filter_horizontal = ('groups', 'user_permissions')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    def email(self, obj):
        return obj.email

# Unregister and re-register User admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)