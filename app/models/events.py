"""
SQLAlchemy event listeners for automatic embedding generation.

These listeners ensure embeddings are generated automatically whenever
a note is created or updated, eliminating the need for manual regeneration.
"""

import logging
from sqlalchemy import event
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def register_note_events():
    """
    Register all event listeners for the Note model.
    
    This function should be called during application startup to ensure
    embeddings are automatically generated on note creation and updates.
    """
    from app.models.note_model import Note
    from app.services.ai.embedding_service import get_embedding_service, EmbeddingGenerationError
    
    @event.listens_for(Note, 'before_insert')
    @event.listens_for(Note, 'before_update')
    def generate_embedding_on_save(mapper, connection, target):
        """
        Generate embedding for a note before it's saved to the database.
        
        This runs synchronously within the database transaction, ensuring
        the embedding is always saved with the note.
        
        Args:
            mapper: SQLAlchemy mapper
            connection: Database connection
            target: The Note instance being saved
        """
        # Only generate if the note has content
        if not target.content or not target.content.strip():
            logger.debug(f"Skipping embedding generation for note {target.id or 'new'} - no content")
            return
        
        try:
            embedding_service = get_embedding_service()
            
            # Combine all relevant fields for embedding
            combined_text = embedding_service.combine_text_for_embedding(
                content=target.content,
                scripture_refs=target.scripture_refs,
                tags=target.tags.split(',') if target.tags else None
            )
            
            # Generate the embedding with retry logic built-in
            embedding = embedding_service.generate(combined_text)
            target.embedding = embedding
            
            logger.info(f"Generated embedding for note {target.id or 'new'}")
            
        except EmbeddingGenerationError as e:
            # Log the error but don't block the save
            # The note will be saved without an embedding
            logger.error(f"Failed to generate embedding for note {target.id or 'new'}: {e}")
            target.embedding = None
            
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error generating embedding for note {target.id or 'new'}: {e}", exc_info=True)
            target.embedding = None
