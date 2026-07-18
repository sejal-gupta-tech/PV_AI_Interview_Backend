import os
import json
from pathlib import Path

# Frontend paths
FRONTEND_DIR = Path(r"c:\Users\PC6\projects\PV_Classes_Website")
QUESTIONS_DIR = FRONTEND_DIR / "src" / "mockInterview" / "questions"

# Exam definitions
SUBJECT_MAPPING = {
  "SSC CGL": ["General Awareness", "Quantitative Aptitude", "Reasoning", "English Language"],
  "SSC CHSL": ["General Awareness", "Quantitative Aptitude", "Reasoning", "English Language"],
  "SSC MTS": ["General Awareness", "Quantitative Aptitude", "Reasoning", "English Language"],
  "SSC GD": ["General Awareness", "Elementary Mathematics", "Reasoning", "English/Hindi"],
  "SSC CPO": ["General Awareness", "Quantitative Aptitude", "Reasoning", "English Comprehension"],
  "KVS PRT": ["English", "Hindi", "Reasoning", "Quantitative Aptitude", "Computer", "General Knowledge", "Current Affairs", "Child Development & Pedagogy (CDP)", "Teaching Aptitude", "Environmental Studies (EVS)", "Mathematics", "English Pedagogy", "Hindi Pedagogy"],
  "KVS TGT": ["Common Subjects", "English", "Hindi", "Mathematics", "Science", "Social Science", "Sanskrit", "Computer Science", "Art Education", "Physical Education", "Music"],
  "KVS PGT": ["Common Subjects", "Physics", "Chemistry", "Biology", "Mathematics", "English", "Hindi", "Commerce", "Economics", "History", "Geography", "Political Science", "Computer Science", "Sociology", "Psychology", "Home Science"],
  "NVS PRT": ["English", "Hindi", "Reasoning", "Quantitative Aptitude", "Computer", "General Knowledge", "Current Affairs", "Child Development & Pedagogy (CDP)", "Teaching Aptitude", "Environmental Studies (EVS)", "Mathematics", "English Pedagogy", "Hindi Pedagogy"],
  "NVS TGT": ["Common Subjects", "English", "Hindi", "Mathematics", "Science", "Social Science", "Sanskrit", "Computer Science", "Art Education", "Physical Education", "Music"],
  "NVS PGT": ["Common Subjects", "Physics", "Chemistry", "Biology", "Mathematics", "English", "Hindi", "Commerce", "Economics", "History", "Geography", "Political Science", "Computer Science", "Sociology", "Psychology", "Home Science"]
}

def sanitize_for_path(s: str) -> str:
    import re
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

def get_exam_path(exam: str) -> str:
    parts = exam.lower().split(" ")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return sanitize_for_path(exam)

def generate_dummy_subject(exam: str, subject: str, target_file: Path):
    if target_file.exists():
        return

    print(f"Generating dummy questions for {exam} - {subject}...")
    
    questions = []
    for i in range(1, 16):
        difficulty = "Easy" if i <= 5 else ("Medium" if i <= 10 else "Hard")
        
        q = {
            "id": i,
            "question_en": f"This is a sample {difficulty} question for {subject} in the {exam} examination. Which option is correct?",
            "question_hi": f"यह {exam} परीक्षा में {subject} के लिए एक नमूना {difficulty} प्रश्न है। कौन सा विकल्प सही है?",
            "options_en": [
                "Option A (Incorrect)",
                "Option B (Correct)",
                "Option C (Incorrect)",
                "Option D (Incorrect)"
            ],
            "options_hi": [
                "विकल्प A (गलत)",
                "विकल्प B (सही)",
                "विकल्प C (गलत)",
                "विकल्प D (गलत)"
            ],
            "correctAnswer": 1,
            "explanation_en": f"This is a placeholder explanation for the {subject} question.",
            "explanation_hi": f"यह {subject} प्रश्न के लिए एक प्लेसहोल्डर स्पष्टीकरण है।",
            "difficulty": difficulty
        }
        questions.append(q)
        
    # Write to TypeScript file
    target_file.parent.mkdir(parents=True, exist_ok=True)
    
    ts_content = 'import { InterviewQuestion } from "../../../config/types";\n\n'
    ts_content += 'export const questions: InterviewQuestion[] = '
    ts_content += json.dumps(questions, indent=2, ensure_ascii=False)
    ts_content += ';\n'
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(ts_content)

def main():
    for exam, subjects in SUBJECT_MAPPING.items():
        exam_path = get_exam_path(exam)
        for subject in subjects:
            subject_path = sanitize_for_path(subject)
            target_file = QUESTIONS_DIR / exam_path / f"{subject_path}.ts"
            generate_dummy_subject(exam, subject, target_file)
            
    print("All dummy generation tasks completed!")

if __name__ == "__main__":
    main()
