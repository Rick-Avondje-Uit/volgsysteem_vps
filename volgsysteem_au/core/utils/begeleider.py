from core.models import Begeleider
from core.serializers import BegeleiderSerializer

def get_begeleider_list():
    return Begeleider.objects.all()

def create_begeleider(data):
    serializer = BegeleiderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return serializer.data
    return serializer.errors
