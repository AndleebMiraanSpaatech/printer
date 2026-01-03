from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from django.apps import apps
from . import views
from .views import get_generic_viewset
import re

app_name = "api"

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'), 
    path('custom/<str:model_name>/',views.custom_model_list_view,name='custom-model-list'),   
]

def camel_to_kebab(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

router = DefaultRouter()
for model in apps.get_containing_app_config(__package__).get_models():
    route_name = camel_to_kebab(model.__name__)
    router.register(route_name, get_generic_viewset(model))

urlpatterns += [path('', include(router.urls))]
