from django.urls import path
from . import views
from django.views.static import serve

urlpatterns = [
    path('', views.Index.as_view()),
    # re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]