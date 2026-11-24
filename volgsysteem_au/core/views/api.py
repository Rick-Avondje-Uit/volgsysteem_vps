from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from core.models import Begeleider, Deelnemer, DagRapportage
from core.serializers import BegeleiderSerializer, DeelnemerSerializer, RapportageSerializer, RapportageListSerializer

class ApiBegeleiders(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        objects = Begeleider.objects.all()

        serializer = BegeleiderSerializer(objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ApiDeelnemerList(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, format=None):
        deelnemers = Deelnemer.objects.all()
        serializer = DeelnemerSerializer(deelnemers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DeelnemerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ApiRapportageList(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, format=None):
        rapportages = DagRapportage.objects.all().order_by("-datum")
        serializer = RapportageSerializer(rapportages, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RapportageListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    