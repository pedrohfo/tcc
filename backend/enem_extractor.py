import re
import psycopg2
from PyPDF2 import PdfReader

PDF_PATH = 'C:/Users/pedro/Downloads/Enem-Extractor/Enem-Extractor/2023_PV_impresso_D1_CD1.pdf'

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
            sub_subject TEXT,
            question_text TEXT,
            UNIQUE (test_id, question_number, subject, sub_subject)
        );
        CREATE TABLE IF NOT EXISTS alternatives (
            id SERIAL PRIMARY KEY,
            question_id INTEGER REFERENCES questions(id),
            alternative_text TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def extract_questions_and_alternatives(text):
    # Find all subject blocks
    subject_pattern = r'([A-Z, ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ]+\s*E\s*SUAS\s*TECNOLOGIAS)\s*(?:Questões de (\d+) a (\d+))'
    subject_blocks = re.findall(subject_pattern, text)
    
    question_data = []
    
    for subject_info in subject_blocks:
        subject = subject_info[0].strip()
        start_q = int(subject_info[1])
        end_q = int(subject_info[2])
        
        # Find the text block for this subject
        subject_start_idx = text.find(subject)
        next_subject_idx = text.find("E SUAS TECNOLOGIAS", subject_start_idx + len(subject))
        if next_subject_idx == -1:
            next_subject_idx = len(text)
        
        subject_text = text[subject_start_idx:next_subject_idx]
        
        # Find sub-subjects if any
        sub_subject_pattern = r'Questões de \d+ a \d+ \(opção ([^)]+)\)'
        sub_subjects = re.findall(sub_subject_pattern, subject_text)
        
        if sub_subjects:
            # Handle text with sub-subjects
            for sub_subject in sub_subjects:
                # Find the sub-subject block
                sub_pattern = f'Questões de \\d+ a \\d+ \\(opção {sub_subject}\\)(.*?)(?=Questões de \\d+ a \\d+ \\(opção|{subject_info[0]}|$)'
                sub_blocks = re.findall(sub_pattern, subject_text, re.DOTALL)
                
                if sub_blocks:
                    sub_text = sub_blocks[0]
                    # Extract questions from this sub-subject
                    question_blocks = re.findall(r'QUESTÃO (\d+)(.*?)(?=QUESTÃO \d+|$)', sub_text, re.DOTALL)
                    
                    for q_num, q_content in question_blocks:
                        process_question(question_data, q_num, q_content, subject, sub_subject)
        else:
            # Handle text without sub-subjects
            question_blocks = re.findall(r'QUESTÃO (\d+)(.*?)(?=QUESTÃO \d+|$)', subject_text, re.DOTALL)
            
            for q_num, q_content in question_blocks:
                process_question(question_data, q_num, q_content, subject, None)
    
    return question_data

def process_question(question_data, q_num, q_content, subject, sub_subject):
    # Split the question into question text and alternatives
    question_split = re.split(r'\n[A-E]\s[A-E]\s', q_content)
    if len(question_split) > 0:
        question_text = clean_string(question_split[0].strip())
        alternatives = [alt.strip() for alt in question_split[1:] if alt.strip()]
        for j in range(len(alternatives)):
            if '.' in alternatives[j]:
                alternatives[j] = clean_string(alternatives[j].split('.')[0] + '.')
        
        question_data.append({
            'question_number': int(q_num),
            'subject': subject,
            'sub_subject': sub_subject,
            'question': question_text, 
            'alternatives': alternatives
        })

def store_data(question_data):
    conn = connect_db()
    cur = conn.cursor()
    
    # Ensure the test is in the database
    cur.execute("INSERT INTO tests (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id", ('Enem 2023',))
    test_id = cur.fetchone()
    if not test_id:
        cur.execute("SELECT id FROM tests WHERE name = %s", ('Enem 2023',))
        test_id = cur.fetchone()[0]
    else:
        test_id = test_id[0]
    
    for question in question_data:
        # Insert question with number, subject and sub_subject
        cur.execute("""
            INSERT INTO questions (test_id, question_number, subject, sub_subject, question_text) 
            VALUES (%s, %s, %s, %s, %s) 
            ON CONFLICT (test_id, question_number, subject, sub_subject) 
            DO UPDATE SET question_text = EXCLUDED.question_text
            RETURNING id
        """, (test_id, question['question_number'], question['subject'], question['sub_subject'], question['question']))
        question_id = cur.fetchone()[0]
        
        for alternative in question['alternatives']:
            cur.execute("INSERT INTO alternatives (question_id, alternative_text) VALUES (%s, %s)", (question_id, alternative))
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    # Create database tables if they don't exist
    create_tables()
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    text = extract_text(PDF_PATH)
    
    # Extract questions with subjects and sub-subjects
    print("Parsing questions and alternatives...")
    question_data = extract_questions_and_alternatives(text)
    
    # Store data in the database
    print(f"Storing {len(question_data)} questions in database...")
    store_data(question_data)
    
    print("Data extraction and storage completed successfully!")
    print(f"Processed {len(question_data)} questions across different subjects.")