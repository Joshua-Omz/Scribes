

from typing import Dict, Any, Optional
import logging

from app.services.ai.tokenizer_service import get_tokenizer_service
from app.core.config import settings
import re

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Engine for constructing prompts with token awareness and safety.
    
    ⚠️  PLACEHOLDER - YOU MUST IMPLEMENT THIS WITH SAFETY IN MIND
    """
    SYSTEM_PROMPT = """You are a pastoral AI assistant for Scribes, an app that helps Christians organize and reflect on sermon notes.YOUR ROLE:
- Answer questions based ONLY on the user's sermon notes (provided as context below) and the bible KJV ,NIV and AMP version specifically
- Use a warm, supportive, and spiritually nurturing tone
- Speak as a knowledgeable Christian friend, not as a preacher or authority
- Help users discover insights from their own sermon collection and making sure that the insights drawn is scripture compliant
- When providing insights  always gives scripture partaining to the insights drawn , it does not necessarily have to be from their notes 

GUIDELINES:
1. ALWAYS cite your sources using note titles and scriptures (bible) (e.g., "According to 'Sermon on Faith'...")
2. If the answer isn't in the notes, say: "I don't see that topic covered in your notes yet." and offer answers from the bible "but i can provide you with what the scripture says "
3. Never make up information or add teachings not found in the provided notes or bible
4. If asked about sensitive topics (politics, denominational disputes), respond with:
   "That's a thoughtful question. I can only share what your sermon notes say about it." or i can draw insights on how God sees it by checking the bible (word of God)
5. Encourage deeper Bible study and conversation with spiritual mentors
6. Be concise but thoughtful - aim for 2-4 paragraphs

CITATION FORMAT:
- When referencing a note, use: "In '[Note Title]' by [Preacher Name]..." and referenacing from the scripture or quoting , e.g "in Galatians 3:7 ....."
- If multiple notes discuss the topic, mention all relevant sources
- End your response with: "Sources: [Note Title 1], [Note Title 2], scripture"

TONE EXAMPLES:
✅ GOOD: "Based on your notes, Pastor John's sermon on Hebrews 11 emphasizes that faith involves trusting God even when we can't see the outcome..."
✅ GOOD: "I notice a beautiful theme across three of your sermons about grace..."
 GOOD: "The Bible says..." (not too authoritative - focus on THEIR notes and the scripture in relation to thier notes)
 GOOD: "i recommend...  based on your notes and scriptures "
❌ BAD: "You should..." (too prescriptive - be supportive, not directive)
Remember: You're helping users explore their own sermon collection, not teaching new doctrine."""

        

    def __init__(self):
        """Initialize prompt engine."""
        self.tokenizer = get_tokenizer_service()
        self.model_context_window = settings.assistant_model_context_window
        logger.warning("PromptEngine initialized - PLACEHOLDER ONLY")
    
    def build_prompt(
        self,
        user_query: str,
        context_text: list,
        sources: list = None
    ) -> str:
        """
        Build complete prompt in Llama-2-chat format.
        
        Format:
        <s>[INST] <<SYS>>
        {system_prompt}
        <</SYS>>
        
        {context}
        
        {user_query} [/INST]
        
        Args:
            user_query: User's question (will be sanitized)
            context_text: Formatted context from ContextBuilder
            sources: List of source dicts (for additional context)
            
        Returns:
            Complete prompt string ready for LLM
            
        Raises:
            ValueError: If inputs invalid
        """
        if not user_query or not user_query.strip():
          raise ValueError("user_query cannot be empty")
        
        if not context_text or not context_text.strip():
            logger.warning("No context provided - assistant may not have relevant info")
            context_text = "(No relevant sermon notes found for this query)"
        
        # Sanitize user query (prevent injection)
        safe_query = self._sanitize_user_query(user_query)
        
        # Build source summary (helps LLM understand available notes)
        source_summary = ""
        if sources:
            source_list = [f"- {s['note_title']}" for s in sources[:5]]  # Top 5
            source_summary = (
                "\n\nNOTES AVAILABLE:\n" + 
                "\n".join(source_list) +
                ("\n... and more" if len(sources) > 5 else "")
            )

            # Assemble prompt in Llama-2-chat format
            prompt = f"""<s>[INST] <<SYS>>
{self.SYSTEM_PROMPT}
<</SYS>>

SERMON NOTE EXCERPTS:
{context_text}
{source_summary}

USER QUESTION:
{safe_query} [/INST]"""
            logger.info(
            f"Prompt built: {len(prompt)} chars, "
            f"query='{safe_query[:50]}...', "
            f"{len(sources) if sources else 0} sources"
        )
            
            return prompt 
        def _sanitize_user_query(self, query: str) -> str:
            """
        Sanitize user query to prevent prompt injection.
        
        Defenses:
        1. Detect and neutralize injection attempts
        2. Remove Llama-2 special tokens
        3. Limit length to prevent token exhaustion
        4. Remove excessive whitespace
        
        Args:
            query: Raw user input
            
        Returns:
            Sanitized query safe for prompt inclusion
        """
            #patterns indicating injection attempts
        injection_patterns = [
                r"ignore\s+(all\s+)?previous",
            r"disregard\s+(all\s+)?instructions",
            r"forget\s+everything",
            r"new\s+instructions",
            r"you\s+are\s+now",
            r"act\s+as\s+(a\s+)?",
            r"pretend\s+to\s+be",
            r"system\s*:",
            r"<<SYS>>",
            r"<</SYS>>",
            r"\[INST\]",
            r"\[/INST\]",
            r"<s>",
            r"</s>",

            ]
        query_lower = query.lower()
        for pattern in injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning(
                    f"Potential injection detected (pattern: {pattern}). "
                    f"Query: '{query[:100]}...'"
                )
                # Replace with safe generic query
                return "What do my sermon notes say about this topic?"
        
        # Remove special tokens (just in case)
        query = re.sub(r"<s>|</s>", "", query)
        query = re.sub(r"\[INST\]|\[/INST\]", "", query)
        query = re.sub(r"<<SYS>>|<</SYS>>", "", query)
        
        # Remove excessive whitespace
        query = re.sub(r"\s+", " ", query)
        query = query.strip()
        
        # Limit length (prevent token exhaustion)
        max_chars = 500  # ~150 tokens
        if len(query) > max_chars:
            query = query[:max_chars].rsplit(" ", 1)[0] + "..."
            logger.warning(f"Query truncated to {max_chars} chars")
        
        return query
    def build_no_context_response(self, user_query: str) -> str:
        """
        Build a polite response when no relevant context found.
        
        This is NOT sent to the LLM - it's a pre-generated response
        to save API costs when retrieval returns no chunks.
        
        Args:
            user_query: User's original question
            
        Returns:
            Helpful message encouraging note-taking
        """
        return (
            f"I don't have any sermon notes that discuss '{user_query}' yet. "
            f"As you add more notes to Scribes, I'll be able to help you explore "
            f"themes and connections across your sermon collection. "
            f"\n\nConsider adding notes from sermons you've heard on this topic!"
        )
    
    def extract_answer_from_response(self, raw_response: str) -> str:
        """
        Extract clean answer from LLM's raw response.
        
        Llama-2 sometimes includes extra tokens or formatting.
        This cleans it up.
        
        Args:
            raw_response: Raw text from LLM
            
        Returns:
            Cleaned answer text
        """
        # Remove any residual special tokens
        answer = re.sub(r"<s>|</s>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>", "", raw_response)
        
        # Remove leading/trailing whitespace 
        answer = answer.strip()
        
        # If empty, return fallback
        if not answer:
            logger.warning("LLM returned empty response")
            return "I'm having trouble generating a response. Please try rephrasing your question."
        
        return answer
    def get_system_prompt(self) -> str:
        """Get the current system prompt (for debugging/monitoring)."""
        return self.SYSTEM_PROMPT
    
    def update_system_prompt(self, new_prompt: str):
        """
        Update system prompt (advanced use - be careful!).
        
        Args:
            new_prompt: New system instruction text
        """
        if not new_prompt or len(new_prompt) < 50:
            raise ValueError("System prompt too short (min 50 chars)")
        
        self.SYSTEM_PROMPT = new_prompt
        logger.warning(f"System prompt updated ({len(new_prompt)} chars)")


# Singleton
_prompt_engine = None

def get_prompt_engine() -> PromptEngine:
    """Get or create prompt engine singleton."""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
    return _prompt_engine
    


            
            
      
       
          
    
    def get_default_system_prompt(self) -> str:
        """
        Get default system instructions.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Should define:
        - Assistant role and capabilities
        - How to use context
        - Citation requirements
        - Boundaries (what NOT to do)
        - Tone and style
        """
        raise NotImplementedError("System prompt not defined")
    
    def detect_prompt_injection(self, user_query: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Look for:
        - Instructions to ignore previous context
        - Role-playing attempts
        - System prompt leakage attempts
        - Malicious instructions
        """
        raise NotImplementedError("Prompt injection detection not implemented")


# Singleton
_prompt_engine = None


def get_prompt_engine() -> PromptEngine:
    """Get or create prompt engine singleton."""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
    return _prompt_engine

