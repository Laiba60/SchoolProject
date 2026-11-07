from rest_framework import serializers

from school.utils import display_subject


class ResultSerializer(serializers.Serializer):
    """Output shape shared by the teacher and admin result lists."""
    id = serializers.IntegerField()
    student_uid = serializers.CharField(source="student.uid")
    student_name = serializers.CharField(source="student.full_name")
    section = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    total_marks = serializers.IntegerField()
    obtained_marks = serializers.IntegerField()
    percentage = serializers.FloatField()
    grade = serializers.CharField()

    def get_section(self, r):
        return r.student.section.label if r.student.section else ""

    def get_subject(self, r):
        return display_subject(r.subject)

    def get_teacher_name(self, r):
        return r.teacher.full_name if r.teacher else None


class ResultInputSerializer(serializers.Serializer):
    student_uid = serializers.CharField(required=False)
    subject = serializers.CharField(required=False, max_length=80)
    total_marks = serializers.IntegerField(min_value=1)
    obtained_marks = serializers.IntegerField(min_value=0)

    def validate(self, data):
        if data["obtained_marks"] > data["total_marks"]:
            raise serializers.ValidationError({"obtained_marks": "Obtained marks cannot be more than total marks."})
        return data
