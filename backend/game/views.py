from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from tcc import settings
from .models import HintHistory, UserProfile, UserPhase
from .serializers import UserProfileSerializer, UserPhaseSerializer
from questions.models import Alternative, Question
import openai

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class HintView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, phase_number):
        user = request.user
        profile = user.userprofile

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
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
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
            profile.crystals += 10  # ganha 10 cristais por acerto
            profile.save()

            return Response({"correct": True, "crystals": profile.crystals})
        else:
            return Response({"correct": False, "crystals": UserProfile.objects.get(user=user).crystals})
