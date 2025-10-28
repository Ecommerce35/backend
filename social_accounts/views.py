from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .utils import Google, register_social_user
from .serializers import *

class GoogleSocialAuthView(APIView):
    serializer_class = GoogleSignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        print(serializer)
        serializer.is_valid(raise_exception=True)
        data = ((serializer.validated_data)['access_token'])
        return Response(data, status=status.HTTP_200_OK)

