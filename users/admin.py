from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import TANFUserCreationForm, TANFUserChangeForm
from .models import TANFUser


class TANFUserAdmin(UserAdmin):
    add_form = TANFUserCreationForm
    form = TANFUserChangeForm
    model = TANFUser
    list_display = ('email', 'stt_code', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'stt_code',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'stt_code', 'is_staff', 'is_active')}),
    )
    search_fields = ('email', 'stt_code',)
    ordering = ('email',)


admin.site.register(TANFUser, TANFUserAdmin)
