import re
from PyPDF2 import PdfReader
import psycopg2

QUESTIONS_PDF = 'C:/Users/pedro/Downloads/Enem-Extractor/Enem-Extractor/2023_PV_impresso_D1_CD1.pdf'
ANSWERS_PDF = 'C:/Users/pedro/Downloads/Enem-Extractor/Enem-Extractor/2023_GB_impresso_D1_CD1.pdf'

# Database connection details
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

def connect_db():
    return psycopg2.connect(**DB_PARAMS)

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
    subject_blocks = re.findall(
        r'([A-ZÇÃÕÂÊÁÉÍÓÚÜ,\s]+?)\s*Questões de (\d{2}) a (\d{2})(?!\s*\(opção)',
        text,
        re.MULTILINE
    )

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

def extract_answers_old(pdf_path):
    text = extract_text(pdf_path)

    # Match default answer format
    all_answers = re.findall(r'(\d{1,3})\s([A-E])', text)

    # Match INGLÊS/ESPANHOL block for questions 1–5
    lang_section_match = re.search(r'INGLÊS\s+ESPANHOL\s+((?:\d+\s+[A-E]\s+[A-E]\s*)+)', text)
    lang_block = lang_section_match.group(1) if lang_section_match else ''
    lang_answers = re.findall(r'(\d+)\s([A-E])\s([A-E])', lang_block)

    lang_answer_map = {}
    for num, eng, esp in lang_answers:
        lang_answer_map[int(num)] = (eng, esp)

    final_answers = []
    used_lang_questions = set()

    for num, ans in all_answers:
        q_num = int(num)
        if q_num in lang_answer_map and q_num not in used_lang_questions:
            eng, esp = lang_answer_map[q_num]
            final_answers.append((q_num, eng))  # Inglês
            final_answers.append((q_num, esp))  # Espanhol
            used_lang_questions.add(q_num)
        elif q_num not in used_lang_questions:
            final_answers.append((q_num, ans))

    return final_answers

def extract_answers(pdf_path):
    text = extract_text(pdf_path)
    text = re.sub(r'[ \t]+', ' ', text)

    # Step 1: Extract the INGLÊS / ESPANHOL block
    lang_match = re.search(r'INGLÊS\s+ESPANHOL\s+((?:\d+\s+[A-E]\s+[A-E]\s*)+)', text)
    lang_block = lang_match.group(1) if lang_match else ''

    lang_answers_raw = re.findall(r'(\d+)\s+([A-E])\s+([A-E])', lang_block)

    # First 5 = Inglês only, then 5 more = Espanhol only
    lang_answers = []
    for qnum, eng, esp in lang_answers_raw:
        lang_answers.append((int(qnum), eng))  # Q1–Q5 Inglês first
    for qnum, eng, esp in lang_answers_raw:
        lang_answers.append((int(qnum), esp))  # Q1–Q5 Espanhol next

    # Step 2: Extract only the correct gabarito part (QUESTÕES 1 to 45)
    # Find the second gabarito block after "QUESTÃO GABARITO"
    second_block_match = re.search(r'QUESTÃO\s+GABARITO\s+([\s\S]+?)LINGUAGENS', text)
    second_block = second_block_match.group(1) if second_block_match else ''

    # Extract the answers for questions 1-45
    rest_answers_raw = re.findall(r'(\d{1,2})\s+([A-E])', second_block)
    rest_answers = [(int(q), a) for q, a in rest_answers_raw if int(q) > 5]

    # Step 3: Build final list
    final_answers = lang_answers + rest_answers

    # print(final_answers)
    return final_answers

def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            test_id INTEGER REFERENCES tests(id),
            question_number INTEGER,
            subject TEXT,
            question_text TEXT
        );
        CREATE TABLE IF NOT EXISTS alternatives (
            id SERIAL PRIMARY KEY,
            question_id INTEGER REFERENCES questions(id),
            alternative_text TEXT,
            alternative_number CHAR(1),
            is_correct BOOLEAN DEFAULT FALSE
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def store_data(question_data, answers):
    conn = connect_db()
    cur = conn.cursor()

    # Ensure the test exists
    cur.execute("INSERT INTO tests (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id", ('Enem 2023',))
    test_id = cur.fetchone()
    if not test_id:
        cur.execute("SELECT id FROM tests WHERE name = %s", ('Enem 2023',))
        test_id = cur.fetchone()[0]
    else:
        test_id = test_id[0]

    # Build a mapping from question_number to correct_letter
    answer_map = {}
    for qnum, letter in answers:
        if qnum not in answer_map:
            answer_map[qnum] = letter
        else:
            # If the question number repeats (for language questions 1–5),
            # we keep the second one separately
            if isinstance(answer_map[qnum], list):
                answer_map[qnum].append(letter)
            else:
                answer_map[qnum] = [answer_map[qnum], letter]

    # Tracking how many times we inserted 1–5 (for distinguishing Inglês/Espanhol duplicates)
    inserted_counter = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    alternative_letters = ['A', 'B', 'C', 'D', 'E']

    for question in question_data:
        question_number = question['number']

        # Get the correct letter
        if question_number in {1, 2, 3, 4, 5}:
            idx = inserted_counter[question_number]
            correct_letter = answer_map[question_number][idx]
            inserted_counter[question_number] += 1
        else:
            correct_letter = answer_map.get(question_number)

        cur.execute(
            "INSERT INTO questions (test_id, question_number, subject, question_text) VALUES (%s, %s, %s, %s) RETURNING id",
            (test_id, question['number'], question['subject'], question['question'])
        )
        question_id = cur.fetchone()[0]

        for idx, alternative in enumerate(question['alternatives']):
            letter = alternative_letters[idx]
            is_correct = (letter == correct_letter)
            cur.execute(
                "INSERT INTO alternatives (question_id, alternative_text, alternative_number, is_correct) VALUES (%s, %s, %s, %s)",
                (question_id, alternative, letter, is_correct)
            )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    create_tables()
    text = extract_text(QUESTIONS_PDF)
    question_data = extract_questions_and_alternatives(text)
    answers = extract_answers(ANSWERS_PDF)
    store_data(question_data, answers)
    print("Data extraction and storage completed!")
