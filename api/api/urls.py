from django.contrib import admin
from django.urls import path, include

from knox import views as knox_views
from accounts.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('login/', LoginView.as_view()),
    path('logout/', knox_views.LogoutView.as_view()),
    path('logoutall/', knox_views.LogoutAllView.as_view()),
]
