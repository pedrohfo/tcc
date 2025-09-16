from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from questions.models import Question
from django.conf import settings

class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "achievement")

    def __str__(self):
        return f"{self.user.username} -> {self.achievement.name}"

class HintHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phase_number = models.IntegerField()
    hint = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'phase_number')  # um hint por usuário/fase
        ordering = ['-created_at']

    def __str__(self):
        return f"Dica - Usuário: {self.user.username}, Fase: {self.phase_number}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    crystals = models.IntegerField(default=100)
    energy = models.IntegerField(default=7)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    last_energy_update = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.crystals} cristais"
    
    @property
    def score(self):
        return self.correct_answers - self.wrong_answers


class UserPhase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phase_number = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'phase_number')

    def __str__(self):
        return f"Fase {self.phase_number} - {self.user.username} - {'Concluída' if self.is_completed else 'Pendente'}"
