from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from game.models import UserPhase, Question
import random

class Command(BaseCommand):
    help = "Resorteia as 10 fases de todos os usuários"

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        questions = list(Question.objects.all())

        if len(questions) < 10:
            self.stdout.write(self.style.ERROR("⚠️ É necessário pelo menos 10 questões no banco!"))
            return

        for user in users:
            # apaga as fases antigas
            UserPhase.objects.filter(user=user).delete()

            # sorteia 10 questões aleatórias para esse usuário
            selected_questions = random.sample(questions, 10)

            for i, question in enumerate(selected_questions, start=1):
                UserPhase.objects.create(
                    user=user,
                    phase_number=i,
                    question=question
                )

            self.stdout.write(self.style.SUCCESS(f"✅ Fases sorteadas para {user.username}"))

        self.stdout.write(self.style.SUCCESS("🎉 Todas as fases foram resorteadas com sucesso!"))
