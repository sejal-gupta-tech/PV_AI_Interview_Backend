import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.database import get_db
from app.models.question_bank import QuestionGenerationJobDBModel, QuestionBankDBModel
from app.services.batch_generator import BatchGeneratorService
from app.services.question_validator import QuestionValidatorService
from app.services.duplicate_checker import DuplicateCheckerService

logger = logging.getLogger("job_manager")

class JobManagerService:
    """Service to manage question generation background jobs."""
    
    _active_tasks: Dict[str, asyncio.Task] = {}

    @staticmethod
    async def start_generation(job_id: str, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Starts a background generation job for the given configuration.

        Args:
            job_id (str): The unique identifier for this job.
            config (Dict[str, Any]): The loaded JSON configurations for all exams.

        Returns:
            Dict[str, str]: A dictionary containing the job_id and initial status.
        """
        db = get_db()
        
        # Calculate total batches roughly (3 difficulties * 2 languages = 6 combinations per topic)
        total_batches = 0
        for exam, exam_data in config.items():
            for subject, subject_data in exam_data.items():
                total_batches += len(subject_data.get("topics", [])) * 6

        job = QuestionGenerationJobDBModel(
            job_id=job_id,
            status="Running",
            total_batches=total_batches,
            started_at=datetime.utcnow()
        )
        
        await db["question_generation_jobs"].insert_one(job.model_dump())
        
        # Start background task
        task = asyncio.create_task(JobManagerService._generation_loop(job_id, config))
        JobManagerService._active_tasks[job_id] = task
        
        return {"job_id": job_id, "status": "Running"}

    @staticmethod
    async def get_status(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current status of a running generation job.

        Args:
            job_id (str): The unique identifier of the job.

        Returns:
            Optional[Dict[str, Any]]: The job status document from MongoDB, or None if not found.
        """
        db = get_db()
        job = await db["question_generation_jobs"].find_one({"job_id": job_id}, {"_id": 0})
        return job

    @staticmethod
    async def stop_generation(job_id: str) -> Dict[str, str]:
        """
        Stops and cancels an active background generation job.

        Args:
            job_id (str): The unique identifier of the job to cancel.

        Returns:
            Dict[str, str]: A dictionary indicating the cancellation status.
        """
        task = JobManagerService._active_tasks.get(job_id)
        if task:
            task.cancel()
            del JobManagerService._active_tasks[job_id]
            
        db = get_db()
        await db["question_generation_jobs"].update_one(
            {"job_id": job_id},
            {"$set": {"status": "Cancelled", "updated_at": datetime.utcnow()}}
        )
        return {"job_id": job_id, "status": "Cancelled"}

    @staticmethod
    async def _generation_loop(job_id: str, config: Dict[str, Any]) -> None:
        """
        The core asynchronous generation loop that iteratively generates, validates,
        checks for duplicates, and saves questions batch by batch.

        Args:
            job_id (str): The unique identifier of the job.
            config (Dict[str, Any]): The loaded exams configuration dict.

        Raises:
            Exception: If an unhandled fatal error occurs in the loop.
        """
        db = get_db()
        difficulties = ["Easy", "Medium", "Hard"]
        languages = ["English", "Hindi"]
        batch_size = 25
        
        try:
            for exam, exam_data in config.items():
                for subject, subject_data in exam_data.items():
                    for topic in subject_data.get("topics", []):
                        for difficulty in difficulties:
                            for language in languages:
                                
                                # Update current job state
                                await db["question_generation_jobs"].update_one(
                                    {"job_id": job_id},
                                    {"$set": {
                                        "current_exam": exam,
                                        "current_subject": subject,
                                        "current_topic": topic,
                                        "current_difficulty": difficulty,
                                        "current_language": language,
                                        "updated_at": datetime.utcnow()
                                    }}
                                )
                                
                                retries = 0
                                max_retries = 3
                                success = False
                                
                                while retries < max_retries and not success:
                                    try:
                                        logger.info(f"Starting batch generation: Exam={exam}, Subject={subject}, Topic={topic}, Difficulty={difficulty}, Language={language}")
                                        # Generate
                                        questions = await BatchGeneratorService.generate_batch(
                                            exam=exam, subject=subject, topic=topic,
                                            difficulty=difficulty, language=language, count=batch_size
                                        )
                                        
                                        valid_questions = []
                                        skipped_count = 0
                                        duplicate_count = 0
                                        
                                        logger.info(f"Batch generation complete. Received {len(questions)} questions. Starting Validation.")
                                        
                                        batch_hashes = set()
                                        
                                        for q in questions:
                                            # Validate
                                            is_valid, error_msg = QuestionValidatorService.validate(q, language, batch_hashes)
                                            if not is_valid:
                                                logger.warning(f"Validation failed for a question: {error_msg}")
                                                skipped_count += 1
                                                continue
                                                
                                            # Duplicate Check (DB)
                                            if await DuplicateCheckerService.is_duplicate(q["question"], db):
                                                logger.warning("Duplicate question found in MongoDB, skipping.")
                                                duplicate_count += 1
                                                continue
                                                
                                            # Prepare for DB
                                            q_hash = DuplicateCheckerService.generate_hash(q["question"])
                                            
                                            batch_hashes.add(q_hash)
                                            
                                            db_model = QuestionBankDBModel(
                                                exam=exam,
                                                subject=subject,
                                                topic=q.get("topic", topic),
                                                difficulty=difficulty,
                                                language=language,
                                                question=q["question"],
                                                options=q["options"],
                                                correctAnswer=q["correct_answer"],
                                                explanation=q["explanation"],
                                                questionHash=q_hash
                                            )
                                            valid_questions.append(db_model.model_dump())
                                            
                                        logger.info(f"Validation and Duplicate Check complete. Valid: {len(valid_questions)}, Skipped: {skipped_count}, Duplicates: {duplicate_count}")
                                        # Save to DB
                                        if valid_questions:
                                            logger.info(f"Saving {len(valid_questions)} questions to MongoDB.")
                                            await db["question_bank"].insert_many(valid_questions)
                                            
                                        logger.info("Batch saved. Updating Job Progress.")
                                        # Update Job Progress
                                        generated_this_batch = len(questions)
                                        saved_this_batch = len(valid_questions)
                                        
                                        job_data = await db["question_generation_jobs"].find_one({"job_id": job_id})
                                        if not job_data:
                                            raise ValueError("Job data unexpectedly missing during progress update.")
                                            
                                        # Calculate progress
                                        current_batches = job_data.get("total_batches", 1)
                                        current_progress = min(100.0, ((job_data.get("saved_count", 0) + saved_this_batch) / (current_batches * batch_size)) * 100) if current_batches > 0 else 0
                                        
                                        await db["question_generation_jobs"].update_one(
                                            {"job_id": job_id},
                                            {"$inc": {
                                                "generated_count": generated_this_batch,
                                                "saved_count": saved_this_batch,
                                                "skipped_count": skipped_count,
                                                "duplicate_count": duplicate_count
                                            }, "$set": {
                                                "progress_percentage": current_progress,
                                                "updated_at": datetime.utcnow()
                                            }}
                                        )
                                        
                                        success = True
                                        
                                    except asyncio.CancelledError:
                                        logger.info(f"Job {job_id} cancelled.")
                                        raise
                                    except Exception as e:
                                        retries += 1
                                        logger.exception(f"Batch failed for {topic} - {language} (Retry {retries}/{max_retries}): {str(e)}")
                                        if retries >= max_retries:
                                            await db["question_generation_jobs"].update_one(
                                                {"job_id": job_id},
                                                {"$inc": {"failed_batches": 1}, "$set": {"updated_at": datetime.utcnow()}}
                                            )
                                            
            # Job Complete
            await db["question_generation_jobs"].update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "Completed",
                    "progress_percentage": 100.0,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
        except asyncio.CancelledError:
            pass # Status already set to Cancelled in stop_generation
        except Exception as e:
            logger.exception(f"Job {job_id} failed completely due to an unexpected error: {str(e)}")
            await db["question_generation_jobs"].update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "Failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }}
            )
        finally:
            if job_id in JobManagerService._active_tasks:
                del JobManagerService._active_tasks[job_id]

