from rest_framework import serializers
from .models import Question, Alternative


class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = ['id', 'alternative_text', 'is_correct']
        extra_kwargs = {
            'is_correct': {'write_only': True}  # Para não expor a resposta correta diretamente no GET
        }


class QuestionSerializer(serializers.ModelSerializer):
    alternatives = AlternativeSerializer(many=True, read_only=True, source='alternative_set')

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'image', 'alternatives']
