"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from tarefas.views import (
    CategoriaViewSet,
    HistoricoTarefaViewSet,
    LoginView,
    NotificacaoViewSet,
    SubtarefaViewSet,
    TarefaViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet)
router.register('categorias', CategoriaViewSet)
router.register('tarefas', TarefaViewSet)
router.register('subtarefas', SubtarefaViewSet)
router.register('notificacoes', NotificacaoViewSet)
router.register('historico-tarefas', HistoricoTarefaViewSet, basename='historico-tarefa')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]
