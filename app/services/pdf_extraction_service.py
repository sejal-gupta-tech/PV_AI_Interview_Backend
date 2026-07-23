import fitz  # PyMuPDF
import json
import logging
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("pdf_extraction_service")

class PdfExtractionService:
    @staticmethod
    def extract_pages(file_path: str) -> list[str]:
        """
        Extracts text from a PDF file page by page.
        Returns a list of strings, where each string is the text of a single page.
        """
        try:
            doc = fitz.open(file_path)
            pages = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text.strip():
                    pages.append(text)
            return pages
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    async def extract_questions(pages: list[str]) -> list[dict]:
        """
        Sends the extracted pages to GPT-4o-mini to extract questions.
        Returns a list of dictionaries with 'question', 'options' (optional), and 'answer' (optional).
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        all_questions = []
        
        # We can process pages one by one or in small batches to fit into context window
        # For simplicity, let's process page by page. In production, chunking might be better.
        for index, page_text in enumerate(pages):
            logger.info(f"Extracting questions from page {index + 1}/{len(pages)}")
            
            system_prompt = """You are an AI that extracts interview questions from a text syllabus or question bank.
Extract all valid questions found in the provided text.
If there are multiple-choice options, extract them.
If there is an answer, extract it.

Return ONLY a JSON object with a "questions" array containing objects:
{
    "questions": [
        {
            "question": "What is ...?",
            "options": ["A", "B", "C", "D"],
            "answer": "A"
        }
    ]
}
If there are no options or answers, omit those fields or pass null. If no questions are found, return an empty array.
"""
            
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Text:\n{page_text}"}
                    ],
                    temperature=0.1
                )
                
                result_content = response.choices[0].message.content
                data = json.loads(result_content)
                questions = data.get("questions", [])
                all_questions.extend(questions)
                
            except Exception as e:
                logger.error(f"Error extracting questions from page {index + 1}: {e}")
                
        return all_questions
