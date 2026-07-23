import json
import logging
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("live_interview_ai")

class LiveInterviewAIService:
    @staticmethod
    async def generate_question(exam: str, subject: str, difficulty: str, language: str) -> str:
        """
        Generates a single live interview question using GPT-4o-mini (GPT-5 mini mapping).
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """You are an experienced interviewer.
Generate only ONE interview question.

Rules:
- Ask only one question.
- Do not generate answers.
- Do not explain.
- Do not number the question.
- Difficulty must match the requested level.
- Language must match the requested language.
- Make the question suitable for a real interview.

Interview Language:
{language}

Rules for Language:
If language is Hindi:
- Speak only Hindi.
- Use natural spoken Hindi.
- Avoid unnecessary English words.
- Do not translate literally.
- Speak like a real Indian interviewer.

If language is English:
- Use fluent English.
- Make the question suitable for a real interview.
"""
        
        user_prompt = f"""Exam:
{exam}

Subject:
{subject}

Difficulty:
{difficulty}

Language:
{language}

Return JSON:
{{
   "question":"..."
}}"""
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Mapping to GPT-5 mini spec request
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            result_content = response.choices[0].message.content
            data = json.loads(result_content)
            
            question = data.get("question")
            if not question:
                raise ValueError("AI did not return a valid question field in JSON.")
                
            return question
            
        except Exception as e:
            logger.exception(f"Error generating live interview question: {e}")
            raise RuntimeError(f"Failed to generate question: {str(e)}")

    @staticmethod
    async def generate_chat_response(
        interview_id: str,
        candidate_message: str,
        exam: str,
        subject: str,
        language: str,
        experience_level: str,
        conversation_history: list
    ) -> dict:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = f"""You are a professional interviewer.

Conduct interviews exactly like a human interviewer.

Start by greeting the candidate.

Example flow:

Greeting
↓
How are you?
↓
Introduce yourself.
↓
Education
↓
Experience
↓
Projects
↓
Strengths
↓
Weaknesses
↓
Career Goals
↓
Technical Questions
↓
Scenario Questions
↓
Candidate Questions
↓
Closing

Rules:
- Speak naturally.
- Never sound robotic.
- Ask one question only.
- React to candidate answers.
- Use previous conversation.
- Never repeat questions.
- Transition smoothly.
- Encourage the candidate politely.
- Do not reveal answers.
- The exam is {exam}, subject is {subject}, language is {language}, experience level is {experience_level}.
- For the "stage" field in JSON, strictly use one of: GREETING, INTRODUCTION, HR, PROJECT, TECHNICAL, SCENARIO, CLOSING.

Interview Language:
{language}

Rules for Language:
If language is Hindi:
- Speak only Hindi.
- Use natural spoken Hindi.
- Avoid unnecessary English words.
- Do not translate literally.
- Speak like a real Indian interviewer.

If language is English:
- Use fluent English.

Every response must include an avatar object that drives the 3D avatar's presence.
Set the values based on the conversation context:
- emotion: neutral, smile, happy, serious, thinking, listening, encouraging, surprised, confident
- animation: idle, greeting, speaking, listening, thinking, nod, agree, closing
- gesture: wave, hand_open, point, none
- head_direction: candidate, notes, away (default to candidate)
- eye_contact: true or false
- posture: professional, relaxed, leaning_forward (default to professional)
- speaking_speed: normal, slow, fast (default to normal)

Examples:
Greeting -> emotion=smile, animation=greeting, gesture=wave
Technical Question -> emotion=serious, animation=speaking, gesture=hand_open
Candidate gives good answer -> emotion=encouraging, animation=nod
Closing -> emotion=smile, animation=closing, gesture=wave

Return EXACTLY valid JSON matching:
{{
   "stage":"INTRODUCTION",
   "interviewer_message":"...",
   "next_action":"WAIT_FOR_RESPONSE",
   "avatar": {{
       "emotion": "smile",
       "animation": "greeting",
       "gesture": "wave",
       "head_direction": "candidate",
       "eye_contact": true,
       "posture": "professional",
       "speaking_speed": "normal"
   }}
}}"""

        # Format conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        for turn in conversation_history:
            # turn should be a dict with "role" and "content"
            if "role" in turn and "content" in turn:
                messages.append({"role": turn["role"], "content": turn["content"]})
                
        # Append latest candidate message if it exists (might be empty on first load)
        if candidate_message and candidate_message.strip():
            messages.append({"role": "user", "content": candidate_message})
            
        from app.services.question_selector_service import QuestionSelectorService
        
        is_technical = await QuestionSelectorService.is_initialized(interview_id)
        if is_technical:
            messages.append({"role": "system", "content": "The candidate just answered a technical question. Provide conversational feedback evaluating their answer, but DO NOT ask another technical question."})
            
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0.7
            )
            
            result_content = response.choices[0].message.content
            data = json.loads(result_content)
            
            # Post-process for TECHNICAL stage
            if data.get("stage") == "TECHNICAL":
                if not is_technical:
                    # Initialize it now
                    await QuestionSelectorService.initialize_technical_round(interview_id, limit=5)
                
                next_q = await QuestionSelectorService.get_next_question(interview_id)
                if next_q:
                    # Override to append the next technical question
                    if is_technical:
                        data["interviewer_message"] += f"\n\nHere is your next question: {next_q}"
                    else:
                        data["interviewer_message"] = f"Let's move on to the technical round. {next_q}"
                    await QuestionSelectorService.advance_question(interview_id)
                else:
                    data["stage"] = "CLOSING"
                    data["interviewer_message"] += "\n\nThat concludes our technical round. Let's wrap up the interview."
            
            # Save to MongoDB
            from app.core.database import get_db
            import datetime
            db = get_db()
            
            # Save candidate's message if present
            if candidate_message and candidate_message.strip():
                await db["live_interview_chat_history"].insert_one({
                    "interview_id": interview_id,
                    "role": "candidate",
                    "content": candidate_message,
                    "language": language,
                    "timestamp": datetime.datetime.utcnow()
                })
                
            # Save AI's response
            await db["live_interview_chat_history"].insert_one({
                "interview_id": interview_id,
                "role": "interviewer",
                "content": data.get("interviewer_message", ""),
                "stage": data.get("stage", "UNKNOWN"),
                "next_action": data.get("next_action", "WAIT_FOR_RESPONSE"),
                "avatar": data.get("avatar", {}),
                "language": language,
                "timestamp": datetime.datetime.utcnow()
            })
            
            return data
            
        except Exception as e:
            logger.exception(f"Error generating chat response: {e}")
            raise RuntimeError(f"Failed to generate chat response: {str(e)}")
