from django.contrib.auth import login
from django.conf import settings

from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from accounts.models import User


class LoginView(KnoxLoginView):
    
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        try:
            serializer = AuthTokenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            login(request, user)
            return super(LoginView, self).post(request, format=None)
        except Exception:
            return Response("bad credentials", status=status.HTTP_400_BAD_REQUEST)