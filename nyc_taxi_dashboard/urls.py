"""
URL configuration for NYC Taxi Dashboard.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
from pathlib import Path

frontend_dist = Path(settings.BASE_DIR) / 'frontend' / 'dist'
frontend_assets = frontend_dist / 'assets'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('dashboard.urls')),
    # React SPA - catch all frontend routes (must load index.html from frontend/dist)
    re_path(r'^(?!api/|admin/|static/|assets/).*', TemplateView.as_view(template_name='index.html')),
]
if frontend_assets.exists():
    urlpatterns.insert(2, re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': str(frontend_assets)}))
