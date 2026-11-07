from rest_framework import serializers

from .models import Section


class SectionSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)

    class Meta:
        model = Section
        fields = ("id", "label", "class_name", "section")
