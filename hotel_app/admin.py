from django.contrib import admin
from .models import Hotel, CustomUser
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'phone_number', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('email', 'phone_number')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Hotel)