from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import render


class FrontendView(APIView):
    """
    Serve the frontend HTML page
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, 'index.html')
