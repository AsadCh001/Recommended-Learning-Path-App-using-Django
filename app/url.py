from django.contrib import admin
from django.urls import path,include
from app import views
from rest_framework.routers import DefaultRouter
from .views import RecommendedLearningPathsView


urlpatterns = [
    path('', views.index , name = 'index'),
    path('login', views.loging , name = 'login'),
    path('signup', views.viewsignup , name = 'signup'),
    path('create', views.signup , name = 'create'),
    path('users', views.userauth, name = 'auth'),
    path('views', views.viewuser, name = 'views'),
    path('logout', views.logoutuser , name = 'logout'),
    path('pages', views.pages , name = 'pages'),
    path('path', RecommendedLearningPathsView.as_view(), name='path'),
    path('profile/<int:path_id>/', views.profile, name='profile'),
    path('save', views.save, name='save'),
    
]
