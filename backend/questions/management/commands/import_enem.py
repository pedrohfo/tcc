from django.core.management.base import BaseCommand
from questions.models import Test, Question, Alternative
import re
from PyPDF2 import PdfReader

QUESTIONS_PDF = 'C:/Users/pedro/Downloads/Enem-Extractor/Enem-Extractor/2023_PV_impresso_D1_CD1.pdf'
ANSWERS_PDF = 'C:/Users/pedro/Downloads/Enem-Extractor/Enem-Extractor/2023_GB_impresso_D1_CD1.pdf'

def clean_string(s):
    return s.replace("\n", " ").replace("\t", " ").replace("  ", " ")

def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_questions_and_alternatives(text):
    subject_blocks = re.findall(r'([A-ZÇÃÕÂÊÁÉÍÓÚÜ,\s]+?)\s*Questões de (\d{2}) a (\d{2})(?!\s*\(opção)', text, re.MULTILINE)
    subject_map = {}
    for subject, start, end in subject_blocks:
        for num in range(int(start), int(end) + 1):
            subject_map[num] = subject.strip()

    question_numbers = re.findall(r'QUESTÃO (\d+)', text)
    questions = re.split(r'QUESTÃO \d+', text)

    question_data = []
    for i, question in enumerate(questions[1:]):
        question_split = re.split(r'\n[A-E]\s[A-E]\s', question)
        question_text = clean_string(question_split[0].strip())
        alternatives = [alt.strip() for alt in question_split[1:] if alt.strip()]
        for j in range(len(alternatives)):
            alternatives[j] = clean_string(alternatives[j].split('.')[0] + '.')
        subject = subject_map.get(int(question_numbers[i]), 'DESCONHECIDO')
        question_data.append({
            'number': int(question_numbers[i]),
            'subject': subject,
            'question': question_text,
            'alternatives': alternatives
        })
    return question_data

def extract_answers(pdf_path):
    text = extract_text(pdf_path)
    text = re.sub(r'[ \t]+', ' ', text)
    lang_match = re.search(r'INGLÊS\s+ESPANHOL\s+((?:\d+\s+[A-E]\s+[A-E]\s*)+)', text)
    lang_block = lang_match.group(1) if lang_match else ''
    lang_answers_raw = re.findall(r'(\d+)\s+([A-E])\s+([A-E])', lang_block)
    lang_answers = []
    for qnum, eng, esp in lang_answers_raw:
        lang_answers.append((int(qnum), eng))
    for qnum, eng, esp in lang_answers_raw:
        lang_answers.append((int(qnum), esp))
    second_block_match = re.search(r'QUESTÃO\s+GABARITO\s+([\s\S]+?)LINGUAGENS', text)
    second_block = second_block_match.group(1) if second_block_match else ''
    rest_answers_raw = re.findall(r'(\d{1,2})\s+([A-E])', second_block)
    rest_answers = [(int(q), a) for q, a in rest_answers_raw if int(q) > 5]
    final_answers = lang_answers + rest_answers
    return final_answers

class Command(BaseCommand):
    help = "Importa questões e alternativas do ENEM para o banco"

    def handle(self, *args, **options):
        text = extract_text(QUESTIONS_PDF)
        question_data = extract_questions_and_alternatives(text)
        answers = extract_answers(ANSWERS_PDF)

        test, _ = Test.objects.get_or_create(name="Enem 2023")
        answer_map = {}
        for qnum, letter in answers:
            if qnum not in answer_map:
                answer_map[qnum] = letter
            else:
                if isinstance(answer_map[qnum], list):
                    answer_map[qnum].append(letter)
                else:
                    answer_map[qnum] = [answer_map[qnum], letter]

        inserted_counter = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        alt_letters = ['A', 'B', 'C', 'D', 'E']

        for q in question_data:
            number = q['number']
            if number in {1, 2, 3, 4, 5}:
                idx = inserted_counter[number]
                correct_letter = answer_map[number][idx]
                inserted_counter[number] += 1
            else:
                correct_letter = answer_map.get(number)

            question = Question.objects.create(
                test=test,
                question_number=number,
                subject=q['subject'],
                question_text=q['question']
            )

            for i, alt in enumerate(q['alternatives']):
                alt_letter = alt_letters[i]
                Alternative.objects.create(
                    question=question,
                    alternative_text=alt,
                    alternative_number=alt_letter,
                    is_correct=(alt_letter == correct_letter)
                )

        self.stdout.write(self.style.SUCCESS("Dados do ENEM 2023 importados com sucesso."))