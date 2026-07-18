import os
import json
import asyncio
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Frontend paths
FRONTEND_DIR = Path(r"c:\Users\PC6\projects\PV_Classes_Website")
QUESTIONS_DIR = FRONTEND_DIR / "src" / "mockInterview" / "questions"

# Exam definitions
SUBJECT_MAPPING = {
  "SSC CGL": [
    "General Awareness",
    "Quantitative Aptitude",
    "Reasoning",
    "English Language"
  ],
  "SSC CHSL": [
    "General Awareness",
    "Quantitative Aptitude",
    "Reasoning",
    "English Language"
  ],
  "SSC MTS": [
    "General Awareness",
    "Quantitative Aptitude",
    "Reasoning",
    "English Language"
  ],
  "SSC GD": [
    "General Awareness",
    "Elementary Mathematics",
    "Reasoning",
    "English/Hindi"
  ],
  "SSC CPO": [
    "General Awareness",
    "Quantitative Aptitude",
    "Reasoning",
    "English Comprehension"
  ],
  "KVS PRT": [
    "English",
    "Hindi",
    "Reasoning",
    "Computer",
    "General Knowledge",
    "Current Affairs",
    "Child Development & Pedagogy (CDP)",
    "Teaching Aptitude",
    "Environmental Studies (EVS)",
    "Mathematics",
    "English Pedagogy",
    "Hindi Pedagogy"
  ],
  "KVS TGT": [
    "Common Subjects",
    "English",
    "Hindi",
    "Mathematics",
    "Science",
    "Social Science",
    "Sanskrit",
    "Computer Science",
    "Art Education",
    "Physical Education",
    "Music"
  ],
  "KVS PGT": [
    "Common Subjects",
    "Physics",
    "Chemistry",
    "Biology",
    "Mathematics",
    "English",
    "Hindi",
    "Commerce",
    "Economics",
    "History",
    "Geography",
    "Political Science",
    "Computer Science",
    "Sociology",
    "Psychology",
    "Home Science"
  ],
  "NVS PRT": [
    "English",
    "Hindi",
    "Reasoning",
    "Computer",
    "General Knowledge",
    "Current Affairs",
    "Child Development & Pedagogy (CDP)",
    "Teaching Aptitude",
    "Environmental Studies (EVS)",
    "Mathematics",
    "English Pedagogy",
    "Hindi Pedagogy"
  ],
  "NVS TGT": [
    "Common Subjects",
    "English",
    "Hindi",
    "Mathematics",
    "Science",
    "Social Science",
    "Sanskrit",
    "Computer Science",
    "Art Education",
    "Physical Education",
    "Music"
  ],
  "NVS PGT": [
    "Common Subjects",
    "Physics",
    "Chemistry",
    "Biology",
    "Mathematics",
    "English",
    "Hindi",
    "Commerce",
    "Economics",
    "History",
    "Geography",
    "Political Science",
    "Computer Science",
    "Sociology",
    "Psychology",
    "Home Science"
  ]
}

def sanitize_for_path(s: str) -> str:
    import re
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

def get_exam_path(exam: str) -> str:
    parts = exam.lower().split(" ")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return sanitize_for_path(exam)

# Use AsyncOpenAI for concurrent generation
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_subject(exam: str, subject: str, target_file: Path):
    if target_file.exists():
        print(f"Skipping {target_file.name}, already exists.")
        return

    print(f"Generating questions for {exam} - {subject}...")
    
    # We ask for 15 questions per subject to save time/tokens but provide a solid bank
    prompt = f"""
    You are an expert exam setter for Indian competitive exams.
    Generate 15 realistic, syllabus-aligned multiple-choice questions for the following exam and subject:
    Exam: {exam}
    Subject: {subject}
    
    The questions MUST be bilingual (English and Hindi).
    The format MUST be exactly this JSON schema, returning an object with a 'questions' array:
    {{
      "questions": [
        {{
          "id": <incremental number>,
          "question_en": "Question text in English",
          "question_hi": "Question text in Hindi",
          "options_en": ["Opt 1", "Opt 2", "Opt 3", "Opt 4"],
          "options_hi": ["विकल्प 1", "विकल्प 2", "विकल्प 3", "विकल्प 4"],
          "correctAnswer": <0-3 index of correct option>,
          "explanation_en": "Explanation in English",
          "explanation_hi": "Explanation in Hindi",
          "difficulty": "Easy" | "Medium" | "Hard"
        }}
      ]
    }}
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        questions = data.get("questions", [])
        
        if not questions:
            print(f"Failed to parse questions for {exam} - {subject}")
            return
            
        # Write to TypeScript file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        ts_content = 'import { InterviewQuestion } from "../../../config/types";\n\n'
        ts_content += 'export const questions: InterviewQuestion[] = '
        ts_content += json.dumps(questions, indent=2, ensure_ascii=False)
        ts_content += ';\n'
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(ts_content)
            
        print(f"Successfully generated {len(questions)} questions for {exam} - {subject}")
    except Exception as e:
        print(f"Error generating {exam} - {subject}: {e}")

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not found in environment!")
        return

    tasks = []
    # To avoid rate limits, we'll process them in batches of 10
    semaphore = asyncio.Semaphore(10)
    
    async def sem_task(exam, subject, path):
        async with semaphore:
            await generate_subject(exam, subject, path)
            
    for exam, subjects in SUBJECT_MAPPING.items():
        exam_path = get_exam_path(exam)
        for subject in subjects:
            subject_path = sanitize_for_path(subject)
            target_file = QUESTIONS_DIR / exam_path / f"{subject_path}.ts"
            tasks.append(sem_task(exam, subject, target_file))
            
    await asyncio.gather(*tasks)
    print("All generation tasks completed!")

if __name__ == "__main__":
    asyncio.run(main())
