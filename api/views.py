from rest_framework.viewsets import ModelViewSet
from .serializers import get_auto_serializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.apps import apps
from django.http import Http404
from rest_framework.response import Response
from django.db.models import ForeignKey

def get_generic_viewset(model_class):
    class GenericViewSet(ModelViewSet):
        queryset = model_class.objects.all()
        serializer_class = get_auto_serializer(model_class)

    return GenericViewSet

@api_view(["POST"])
@permission_classes([AllowAny])
def signup_view(request):
    error = None

    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    confirm_password = request.data.get("confirm_password")

    if not username or not email or not password or not confirm_password:
        error = "All fields are required."
    elif password != confirm_password:
        error = "Passwords do not match."
    elif User.objects.filter(username=username).exists():
        error = "Username already exists."
    else:
        User.objects.create_user(username=username,email=email,password=password,is_superuser=False,is_staff=False,)
        return redirect("/login/")

    return render(
        request, "signup.html", {"error": error, "username": username, "email": email}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def custom_model_list_view(request, model_name):
    model_class_name = ''.join(w.capitalize() for w in model_name.split('-'))
    try:
        model = apps.get_model('api', model_class_name)
    except LookupError:
        raise Http404()
    
    fields = {x.name: x for x in model._meta.get_fields()}
    filters = {}
    nested_lookup = False

    for k, v in request.query_params.items():  # or request.data if POST
        if '__' in k:
            # allow nested lookups
            filters[k] = v
            nested_lookup = True
        elif k in fields and not isinstance(fields[k], ForeignKey):
            filters[k] = v
        elif k.endswith('_id') and isinstance(fields.get(k[:-3]), ForeignKey):
            filters[f"{k[:-3]}__id"] = v

    qs = model.objects.filter(**filters)
    
    if nested_lookup:
        qs = qs.distinct() 

    return Response(get_auto_serializer(model)(qs, many=True).data)

