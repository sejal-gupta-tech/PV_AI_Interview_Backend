import hashlib

class DuplicateCheckerService:
    @staticmethod
    def generate_hash(question: str) -> str:
        """
        Generate SHA256 hash
        Lowercase question
        Trim spaces
        """
        normalized_q = question.strip().lower()
        return hashlib.sha256(normalized_q.encode('utf-8')).hexdigest()

    @staticmethod
    async def is_duplicate(question: str, db) -> bool:
        """
        If duplicate, return True
        """
        q_hash = DuplicateCheckerService.generate_hash(question)
        existing = await db["question_bank"].find_one({"questionHash": q_hash}, {"_id": 1})
        return existing is not None
