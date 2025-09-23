from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.db.models.functions import Rank

from tcc import settings
from .models import Achievement, HintHistory, UserAchievement, UserProfile, UserPhase
from django.db.models import F, Window
from .serializers import UserProfileSerializer, UserPhaseSerializer
from questions.models import Alternative, Question
import openai

from django.utils import timezone

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class UserAchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Todas conquistas cadastradas
        all_achievements = Achievement.objects.all()

        # IDs das conquistas já obtidas
        earned_ids = UserAchievement.objects.filter(user=user).values_list("achievement_id", flat=True)

        # Monta resposta
        data = [
            {
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "earned": ach.id in earned_ids,
            }
            for ach in all_achievements
        ]

        return Response(data)

class HintView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, phase_number):
        user = request.user
        profile = user.userprofile

        achievement, _ = Achievement.objects.get_or_create(
            name="Hasta la vista, baby", defaults={"description": "Pediu ajuda do ChatGPT em uma questão!"}
        )
        UserAchievement.objects.get_or_create(user=request.user, achievement=achievement)

        # 1. verifica se já existe dica salva para esta fase
        existing_hint = HintHistory.objects.filter(user=user, phase_number=phase_number).first()
        if existing_hint:
            return Response({"hint": existing_hint.hint}, status=status.HTTP_200_OK)

        # 2. checa se o usuário tem cristais suficientes
        if profile.crystals < 30:
            return Response(
                {"detail": "Cristais insuficientes para pedir dica."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # 3. recupera a fase e a questão associada
            user_phase = UserPhase.objects.get(user=user, phase_number=phase_number)
            question = user_phase.question

            # alternativas associadas
            alternatives = Alternative.objects.filter(question=question)
            alternatives_text = "\n".join(
                [f"{alt.alternative_number}) {alt.alternative_text}" for alt in alternatives]
            )

            # 4. monta prompt para ChatGPT
            prompt = f"""
Você é um tutor de ENEM. Ajude o aluno a resolver a questão abaixo, sem dar a resposta final direta.
Questão: {question.question_text}

Alternativas:
{alternatives_text}

Dê uma dica curta, em português, que oriente o raciocínio sem revelar a alternativa correta explicitamente.
"""

            # 5. chama OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Você é um tutor útil."},
                          {"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )

            hint_text = response.choices[0].message.content.strip()

            # 6. desconta cristais e salva histórico
            profile.crystals -= 30
            profile.save()

            HintHistory.objects.create(
                user=user,
                phase_number=phase_number,
                hint=hint_text
            )

            return Response({"hint": hint_text}, status=status.HTTP_200_OK)

        except UserPhase.DoesNotExist:
            return Response(
                {"detail": "Fase não encontrada para o usuário."},
                status=status.HTTP_404_NOT_FOUND
            )

class EnterPhaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, phase_number):
        user = request.user
        profile = user.userprofile

        # Se não for a primeira fase, só deixa entrar se a anterior foi concluída
        if phase_number > 1:
            if not UserPhase.objects.filter(
                user=user, 
                phase_number=phase_number - 1, 
                is_completed=True
            ).exists():
                return Response(
                    {'detail': 'Você não pode acessar esta fase ainda.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        if profile.energy <= 0:
            return Response(
                {'detail': 'Energia insuficiente.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_phase = UserPhase.objects.get(
            user=user, 
            phase_number=phase_number
        )

        if user_phase.is_completed:
            return Response(UserPhaseSerializer(user_phase).data, status=200)
        
        profile.energy -= 1
        profile.save()

        # Cria a fase para o usuário, se não existir
        user_phase, _ = UserPhase.objects.get_or_create(
            user=user, 
            phase_number=phase_number
        )

        return Response(UserPhaseSerializer(user_phase).data, status=200)

class UserPhaseDetailView(generics.RetrieveAPIView):
    serializer_class = UserPhaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'phase_number'

    def get_queryset(self):
        return UserPhase.objects.filter(user=self.request.user)

    def get_object(self):
        phase_number = int(self.kwargs.get(self.lookup_field))
        user = self.request.user

        # Se não for a primeira fase, verificar se a fase anterior foi concluída
        if phase_number > 1:
            previous_phase = UserPhase.objects.filter(
                user=user,
                phase_number=phase_number - 1
            ).first()

            if not previous_phase or not previous_phase.is_completed:
                raise exceptions.PermissionDenied(
                    f"Você precisa concluir a fase {phase_number - 1} antes de acessar a fase {phase_number}."
                )

        return super().get_object()


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)

        # ⚡ Atualização da energia
        now = timezone.now()
        if profile.last_energy_update:
            elapsed = now - profile.last_energy_update
            recovered = elapsed.days  # 1 energia por dia inteiro
            if recovered > 0:
                profile.energy = min(profile.energy + recovered, 7)  # limite máximo = 7
                profile.last_energy_update = now
                profile.save()
        else:
            # caso seja a primeira vez
            profile.last_energy_update = now
            profile.save()

        return profile


class InitializeUserPhasesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if UserPhase.objects.filter(user=user).exists():
            return Response({"detail": "Fases já iniciadas para este usuário."}, status=status.HTTP_400_BAD_REQUEST)

        questions = Question.objects.all()[:20]  # por exemplo, primeiras 20 questões
        for idx, q in enumerate(questions, start=1):
            UserPhase.objects.create(user=user, phase_number=idx, question=q)

        return Response({"detail": "Fases iniciais criadas com sucesso."}, status=status.HTTP_201_CREATED)


class UserPhaseListView(generics.ListAPIView):
    serializer_class = UserPhaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserPhase.objects.filter(user=self.request.user).order_by('phase_number')


class AnswerPhaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, phase_number):
        user = request.user
        phase = get_object_or_404(UserPhase, user=user, phase_number=phase_number)

        if phase.is_completed:
            return Response({"detail": "Esta fase já foi concluída."}, status=status.HTTP_400_BAD_REQUEST)

        alternative_id = request.data.get("alternative_id")
        if not alternative_id:
            return Response({"detail": "É necessário informar uma alternativa."}, status=status.HTTP_400_BAD_REQUEST)

        is_correct = phase.question.alternative_set.filter(id=alternative_id, is_correct=True).exists()

        if is_correct:
            phase.is_completed = True
            phase.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.correct_answers += 1
            profile.crystals += 10  # ganha 10 cristais por acerto
            profile.save()

            if profile.correct_answers >= 5:
                achievement, _ = Achievement.objects.get_or_create(
                    name="Penta", defaults={"description": "Acertou 5 questões!"}
                )
                UserAchievement.objects.get_or_create(user=request.user, achievement=achievement)

            return Response({"correct": True, "crystals": profile.crystals})
        else:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.wrong_answers += 1
            profile.save()
            return Response({"correct": False, "crystals": UserProfile.objects.get(user=user).crystals})

from django.db.models import F

class RankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 🔹 MESMA query para ambos - consistência total
        users_ranked = (
            UserProfile.objects
            .annotate(score_calc=F("correct_answers") - F("wrong_answers"))
            .order_by("-score_calc", "-correct_answers", "wrong_answers")  # MESMA ordenação
            .values("user__username", "correct_answers", "wrong_answers", "score_calc")
        )

        # 🔹 Top 10 (já está ordenado)
        top_users = list(users_ranked[:10])

        # 🔹 Encontrar a posição do usuário atual na lista COMPLETA
        all_users = list(users_ranked)
        
        # Procura o índice do usuário atual
        user_index = None
        for i, user in enumerate(all_users):
            if user['user__username'] == request.user.username:
                user_index = i
                break

        # 🔹 Posição = índice + 1
        current_user_data = None
        if user_index is not None:
            current_user_data = {
                **all_users[user_index],
                "rank": user_index + 1  # Posição real baseada na ordenação
            }

        return Response({
            "top_users": top_users,
            "current_user": current_user_data
        })