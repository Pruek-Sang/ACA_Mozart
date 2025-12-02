"""
Privacy Guard - The Shield of Sensitive Data
Handles PII anonymization and grounding validation

Philosophy: Sententia ex Veritate (Truth from Source)
- Anonymize before processing
- Validate grounding to prevent hallucination
- Privacy by design
"""

import re
import logging

# Optional vertexai import (for Docker lightweight mode)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    vertexai = None
    GenerativeModel = None
    GenerationConfig = None

from app.config import settings

logger = logging.getLogger("Aura.Privacy")


class PrivacyGuard:
    """
    Privacy and grounding validation service
    
    Responsibilities:
    - Anonymize PII (phone, email, Thai ID)
    - Validate LLM answers against context (grounding check)
    """
    
    def __init__(self):
        """Initialize privacy guard with LLM judge model"""
        from dotenv import load_dotenv
        import os
        import google.generativeai as genai
        
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if api_key:
            genai.configure(api_key=api_key)
            self.judge_model = genai.GenerativeModel(settings.MODEL_NAME_JUDGE)
            logger.info("PrivacyGuard initialized with Google AI")
        else:
            logger.warning("GOOGLE_API_KEY not found. PrivacyGuard disabled.")
            self.judge_model = None
        
        # PII patterns (Thai-specific + common)
        self.patterns = [
            (r'0[689]\d{8}', '<PHONE_NUMBER>'),      # Thai phone numbers
            (r'[\w\.-]+@[\w\.-]+', '<EMAIL>'),       # Emails
            (r'\b\d{13}\b', '<THAI_ID>'),            # Thai ID (13 digits)
        ]
        
        logger.info("PrivacyGuard initialized")
    
    def anonymize(self, text: str) -> str:
        """
        Anonymize PII in text
        
        Args:
            text: Input text with potential PII
        
        Returns:
            Text with PII replaced by placeholders
        """
        cleaned_text = text
        for pattern, replacement in self.patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        return cleaned_text
    
    def validate_grounding(self, answer: str, context: str) -> tuple[bool, str]:
        """
        Validate that answer is grounded in context
        
        Uses LLM as judge to detect hallucinations
        
        Args:
            answer: Generated answer
            context: Source context
        
        Returns:
            (is_grounded, status_message)
        """
        # Special case: If answer admits not finding info, it's grounded
        if "ไม่พบข้อมูล" in answer:
            return True, "NOT_FOUND_ADMITTED"
        
        prompt = f"""TASK: Check if the ANSWER is strictly supported by the CONTEXT.

        CONTEXT:
        {context[:20000]}...

        ANSWER:
        {answer}

        INSTRUCTION:
        - If supported by context, return 'SUPPORTED'.
        - If the answer contains hallucinations, return 'UNSUPPORTED'.
        - Only return one word.
        """
        
        if not self.judge_model:
            return True, "CHECK_SKIPPED_NO_MODEL"
            
        try:
            resp = self.judge_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 10
                }
            )
            res_text = resp.text.strip().upper()
            
            if "UNSUPPORTED" in res_text:
                logger.warning("Hallucination detected by judge model")
                return False, "HALLUCINATION_DETECTED"
            
            return True, "SUPPORTED"
            
        except Exception as e:
            logger.error(f"Grounding check failed: {e}")
            return True, "CHECK_SKIPPED"
