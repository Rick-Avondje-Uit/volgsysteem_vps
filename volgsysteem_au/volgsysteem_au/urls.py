from django.contrib import admin
from django.urls import path, include
from core.handlers import custom_permission_denied

handler403 = custom_permission_denied
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
    path("", include('core.urls')),
    path("vragenlijst/", include("survey.urls")),

]
