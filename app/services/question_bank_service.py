import fitz  # PyMuPDF
import json
import logging
import datetime
import math
import re
from pathlib import Path
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("question_bank_service")
logger.setLevel(logging.INFO)

class QuestionBankService:
    @staticmethod
    async def process_pdf() -> dict:
        """
        Main entry point to read the first PDF from uploads/question_bank/,
        extract text, batch it to GPT for question extraction, deduplicate,
        and store it into MongoDB.
        """
        logger.info("Starting Question Bank Service...")
        
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        bank_dir = BASE_DIR / "uploads" / "question_bank"
        
        if not bank_dir.exists():
            raise FileNotFoundError(f"Directory not found: {bank_dir}")
            
        # 1. Detect PDF
        pdf_files = list(bank_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError("No PDF files found in uploads/question_bank/")
            
        pdf_path = pdf_files[0]
        logger.info(f"Reading PDF... {pdf_path.name}")
        
        # 2. Extract Text
        logger.info("Extracting text...")
        pages = []
        try:
            doc = fitz.open(str(pdf_path))
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                if text:
                    pages.append(text)
        except Exception as e:
            logger.error(f"Failed to read PDF: {e}")
            raise ValueError(f"Failed to extract text from PDF: {e}")
            
        if not pages:
            raise ValueError("PDF is empty or no text could be extracted.")
            
        logger.info(f"Total pages extracted: {len(pages)}")
        
        # 3. Batch and Extract Questions
        logger.info("Extracting questions via LLM...")
        all_extracted_questions = []
        
        # We batch pages (e.g., 5 pages per chunk) to avoid hitting token limits.
        BATCH_SIZE = 5
        num_batches = math.ceil(len(pages) / BATCH_SIZE)
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """You are an AI that extracts interview questions from a text syllabus or question bank.
Extract only actual questions. 
Ignore: headers, footers, page numbers, copyright text, empty lines.

Return ONLY a JSON object with a "questions" array containing strings:
{
    "questions": [
        "What is Inclusive Education?",
        "Explain RPWD Act 2016.",
        "Describe IEP."
    ]
}
If no questions are found, return an empty array. Do not number the questions in the output, just return the text.
"""

        for i in range(num_batches):
            batch_pages = pages[i*BATCH_SIZE : (i+1)*BATCH_SIZE]
            batch_text = "\n\n".join(batch_pages)
            
            logger.info(f"Processing batch {i+1}/{num_batches} (Pages {i*BATCH_SIZE + 1} to min({(i+1)*BATCH_SIZE}, {len(pages)}))")
            
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Text:\n{batch_text}"}
                    ],
                    temperature=0.1
                )
                
                result_content = response.choices[0].message.content
                data = json.loads(result_content)
                questions = data.get("questions", [])
                
                # Clean whitespace
                for q in questions:
                    clean_q = " ".join(q.split()).strip()
                    # Strip any accidental numbering like "1. " or "Q1: "
                    clean_q = re.sub(r"^(?:Q?\d+[\.\)\:]\s*)", "", clean_q, flags=re.IGNORECASE)
                    if clean_q:
                        all_extracted_questions.append(clean_q)
                        
            except Exception as e:
                logger.error(f"Error extracting questions from batch {i+1}: {e}")
                
        total_found = len(all_extracted_questions)
        logger.info(f"Cleaning questions... Found {total_found} questions before deduplication.")
        
        # 4. Save to MongoDB with deduplication
        logger.info("Saving to MongoDB...")
        db = get_db()
        collection = db["question_bank"]
        
        inserted = 0
        duplicates = 0
        
        # Local deduplication first to avoid unnecessary DB calls for the exact same question in the same batch
        seen_local = set()
        unique_extracted = []
        for q in all_extracted_questions:
            q_lower = q.lower()
            if q_lower not in seen_local:
                seen_local.add(q_lower)
                unique_extracted.append(q)
            else:
                duplicates += 1

        # Database deduplication
        for q in unique_extracted:
            # Check if exists (case insensitive via regex)
            # Re.escape is important to avoid regex syntax errors with question marks
            escaped_q = re.escape(q)
            exists = await collection.find_one({
                "question": {"$regex": f"^{escaped_q}$", "$options": "i"},
                "exam": "KVS-NVS",
                "subject": "Special Educator"
            })
            
            if exists:
                duplicates += 1
            else:
                await collection.insert_one({
                    "question": q,
                    "exam": "KVS-NVS",
                    "subject": "Special Educator",
                    "language": "English",
                    "active": True,
                    "created_at": datetime.datetime.utcnow()
                })
                inserted += 1
                
        logger.info("Completed successfully.")
        return {
            "total_found": total_found,
            "inserted": inserted,
            "duplicates": duplicates
        }
