import re
from PyPDF2 import PdfReader

PDF_PATH = 'C:/Users/pedro/Downloads/Enem-Extractor/Enem-Extractor/2023_GB_impresso_D1_CD1.pdf'

def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_answers(pdf_path):
    text = extract_text(pdf_path)

    # Match the first block of answers (after "QUESTÃO GABARITO")
    all_answers = re.findall(r'(\d{1,3})\s([A-E])', text)

    # Match the Inglês / Espanhol specific section
    lang_section_match = re.search(r'INGLÊS\s+ESPANHOL\s+((?:\d+\s+[A-E]\s+[A-E]\s*)+)', text)
    lang_block = lang_section_match.group(1) if lang_section_match else ''

    # Extract double answers for 1-5
    lang_answers = re.findall(r'(\d+)\s([A-E])\s([A-E])', lang_block)
    lang_answer_map = {}
    for num, eng, esp in lang_answers:
        lang_answer_map[int(num)] = (eng, esp)

    # Final answers list (with duplication for 1-5)
    final_answers = []
    used_lang_questions = set()
    for num, ans in all_answers:
        q_num = int(num)
        if q_num in lang_answer_map and q_num not in used_lang_questions:
            # Append both Inglês and Espanhol versions
            eng, esp = lang_answer_map[q_num]
            final_answers.append((q_num, eng))  # First version
            final_answers.append((q_num, esp))  # Second version
            used_lang_questions.add(q_num)
        elif q_num not in used_lang_questions:
            final_answers.append((q_num, ans))

    print(final_answers)
    return final_answers  # This is now ordered and duplicated properly


extract_answers(PDF_PATH)