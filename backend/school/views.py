from rest_framework import generics, serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole

from .models import Section, SiteSettings
from .serializers import SectionSerializer


class SectionListView(generics.ListAPIView):
    """Public: the register form needs the list before anyone is logged in."""
    permission_classes = [AllowAny]
    serializer_class = SectionSerializer
    queryset = Section.objects.all()


class SectionCreateView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        cls = str(request.data.get("class_name", "")).strip()
        raw = request.data.get("sections") or [""]
        if not cls or len(cls) > 20:
            return Response({"class_name": ["Enter a class name (up to 20 characters)."]}, status=400)
        names = {str(s).strip().upper() for s in raw}
        if any(len(n) > 10 for n in names):
            return Response({"sections": ["A section name is at most 10 characters."]}, status=400)
        made = [Section.objects.get_or_create(class_name=cls, section=n)[0] for n in sorted(names)]
        return Response(SectionSerializer(made, many=True).data, status=status.HTTP_201_CREATED)


class SectionDeleteView(APIView):
    permission_classes = [IsAdminRole]

    def delete(self, request, pk):
        sec = generics.get_object_or_404(Section, pk=pk)
        if sec.students.exists() or sec.teachers.exists():
            return Response({"detail": f"Cannot delete {sec.label}: students or teachers are assigned to it."}, status=400)
        sec.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BrandingSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    logo = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = SiteSettings
        fields = ("school_name", "logo", "logo_url")

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None

    def validate_logo(self, f):
        if f.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("The logo must be smaller than 2 MB.")
        return f


class BrandingView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(BrandingSerializer(SiteSettings.load()).data)

    def post(self, request):
        ser = BrandingSerializer(SiteSettings.load(), data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
