from django.contrib import admin
from .models import Question, Alternative, Test

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_number", "subject", "test")
    search_fields = ("question_text", "subject")
    list_filter = ("test",)

@admin.register(Alternative)
class AlternativeAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "alternative_number", "is_correct")
    list_filter = ("is_correct",)

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
