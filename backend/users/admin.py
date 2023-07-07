from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User


class MyUserAdmin(UserAdmin):
    list_filter = ('email', 'username')


admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
