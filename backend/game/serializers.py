from rest_framework import serializers
from .models import UserProfile, UserPhase
from questions.serializers import QuestionSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'crystals', 'energy']
        read_only_fields = ['user', 'crystals', 'energy']


class UserPhaseSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = UserPhase
        fields = ['id', 'phase_number', 'question', 'is_completed']
        read_only_fields = ['phase_number', 'question', 'is_completed']
