from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from game.models import UserPhase, UserProfile
from questions.models import Question

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_phases(sender, instance, created, **kwargs):
    if created:
        # cria o profile
        UserProfile.objects.get_or_create(user=instance)

        # só cria fases se não tiver nenhuma
        if not UserPhase.objects.filter(user=instance).exists():
            questions = Question.objects.order_by("?")[:10]  # sorteia 10 aleatórias
            for idx, q in enumerate(questions, start=1):
                UserPhase.objects.create(user=instance, phase_number=idx, question=q)
