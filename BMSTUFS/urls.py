from django.urls import path
from django.conf.urls import url
from django.contrib.auth import views
from . import views

"""path(r'^login/$', 'django.contrib.auth.views.auth_login', name='login'),
path(r'^logout/$', 'django.contrib.auth.views', name='logout'),
path(r'^logout-then-login/$',
    'django.contrib.auth.views.logout_then_login',
    name='logout_then_login'
    )"""

urlpatterns = [
    path('', views.index, name='index'),
    path("download/<int:id>/", views.download_file, name='download'),
    path("storage/<int:id>/", views.show_folder, name='folder'),
    url(r'^register/$', views.register, name='register'),
    url(r'^edit/$', views.edit, name='edit'),
    path("storage", views.storage, name='storage'),
    path("email", views.send_mail, name='email'),
    path("history", views.show_history, name='history'),
    path("upload", views.upload_materials, name='upload_materials')
]
