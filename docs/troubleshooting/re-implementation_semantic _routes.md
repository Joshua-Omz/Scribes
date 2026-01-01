You are absolutely right to pause and reconsider. The debugging process we've been through highlights that your current implementation is **brittle**.

The core problem is that you are mixing raw SQL (`text()`), manual data type juggling (`np.array`, `.tolist()`, `::vector`), and ORM objects. This creates multiple points of failure.

Let's plan an "entirely new" approach that is much cleaner, more robust, and more "Pythonic" by leveraging the full power of the SQLAlchemy ORM and the `pgvector` library.

### The New Plan: The "ORM-Native Vector Search"

The goal is to **completely eliminate raw SQL** from your endpoints and let the `pgvector` library handle all the complex type conversions and database-specific operators for you.

Here is the step-by-step plan to refactor `app/routes/semantic_search.py`.

-----

### Step 1: Verify the `Note` Model

Before we change the route, we must ensure your `Note` model is correctly set up to use the `Vector` type from `pgvector`.

  * **File:** `app/models/note_model.py` (You don't need to show me this, just confirm it)

  * **Action:** Ensure the `embedding` column is defined like this:

    ```python
    from pgvector.sqlalchemy import Vector
    from sqlalchemy import Column, Integer, Text, ...

    class Note(Base):
        # ... other columns ...
        embedding = Column(Vector(1536), nullable=True) # 1536 or whatever your model dimension is
    ```

    (Based on your Alembic logs, this is likely already correct, but it's the foundation of this plan.)

### Step 2: Refactor the `semantic_search` Endpoint

This is the biggest change. We will replace the entire `text()` query with a native SQLAlchemy ORM query.

  * **File:** `app/routes/semantic_search.py`

  * **Current (Problematic) Logic:**

      * Manually builds a raw SQL string.
      * Manually converts `np.array` to `list`.
      * Manually casts `:query_vec::vector` in the SQL.
      * Manually constructs a `Note` object from raw `row` data.

  * **New (Refactored) Logic:**

    1.  Import the `pgvector` distance function (`cosine_distance`).
    2.  Use a standard SQLAlchemy `select(Note)` statement.
    3.  Use the `.cosine_distance()` function directly in the query.
    4.  Let SQLAlchemy build the `Note` objects automatically.

    <!-- end list -->

    ```python
    # In app/routes/semantic_search.py

    # ... other imports ...
    from app.models.note_model import Note # Import the ORM model

    # ...

    @router.post("/search", response_model=SemanticSearchResponse)
    async def semantic_search(
        search_request: SemanticSearchRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        try:
            embedding_service = get_embedding_service()
            query_embedding = embedding_service.generate(search_request.query)

            # We still need the NumPy validation
            if query_embedding is None:
                query_embedding_array = None
            else:
                query_embedding_array = np.array(query_embedding)

            if query_embedding_array is None or (query_embedding_array == 0.0).all():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to generate embedding for query"
                )

            # --- NEW ORM-NATIVE QUERY ---
            
            # 1. Define the similarity calculation using the ORM model
            #    pgvector's <=> is cosine distance. 1 - distance = similarity.
            #    The library provides .cosine_distance()
            similarity_score = (1 - Note.embedding.cosine_distance(query_embedding)).label("similarity")

            # 2. Build the query using select()
            stmt = (
                select(Note, similarity_score)
                .where(
                    Note.user_id == current_user.id,
                    Note.embedding.isnot(None),
                    similarity_score >= search_request.min_similarity
                )
                .order_by(Note.embedding.cosine_distance(query_embedding)) # Order by distance (ASC)
                .limit(search_request.limit)
            )

            # 3. Execute the query
            #    The pgvector driver will handle the list/ndarray conversion!
            result = await db.execute(stmt)
            rows = result.all() # This gives us (Note, similarity_score) tuples

            # 4. Build the response (MUCH simpler)
            search_results = []
            for note_obj, similarity in rows:
                search_results.append(
                    SemanticSearchResult(
                        note=NoteResponse.model_validate(note_obj), # Pydantic validates the ORM object
                        similarity_score=float(similarity)
                    )
                )
            
            return SemanticSearchResponse(
                results=search_results,
                query=search_request.query,
                total_results=len(search_results)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Semantic search failed: {str(e)}"
            )

    ```

### Step 3: Refactor the `find_similar_notes` Endpoint

We will apply the exact same pattern to this endpoint, replacing its `text()` query.

  * **File:** `app/routes/semantic_search.py`

  * **New (Refactored) Logic:**

    ```python
    @router.get("/similar/{note_id}", response_model=SemanticSearchResponse)
    async def find_similar_notes(
        # ... function arguments ...
    ):
        try:
            # 1. Get the source note (this is already good)
            result = await db.execute(
                select(Note).where(
                    Note.id == note_id,
                    Note.user_id == current_user.id
                )
            )
            source_note = result.scalar_one_or_none()
            
            if not source_note or source_note.embedding is None:
                 raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source note not found or does not have an embedding."
                )

            # --- NEW ORM-NATIVE QUERY ---
            source_embedding = source_note.embedding # This is already a list/array

            similarity_score = (1 - Note.embedding.cosine_distance(source_embedding)).label("similarity")

            stmt = (
                select(Note, similarity_score)
                .where(
                    Note.user_id == current_user.id,
                    Note.id != source_note.id, # Don't match the note with itself
                    Note.embedding.isnot(None),
                    similarity_score >= min_similarity
                )
                .order_by(Note.embedding.cosine_distance(source_embedding))
                .limit(limit)
            )

            result = await db.execute(stmt)
            rows = result.all()

            # 4. Build the response (same simple loop as before)
            search_results = []
            for note_obj, similarity in rows:
                search_results.append(
                    SemanticSearchResult(
                        note=NoteResponse.model_validate(note_obj),
                        similarity_score=float(similarity)
                    )
                )
            
            return SemanticSearchResponse(
                results=search_results,
                query=f"Similar to: {source_note.title}",
                total_results=len(search_results)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Similar notes search error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Similar notes search failed: {str(e)}"
            )

    ```

### Benefits of This New Plan

1.  **More Pythonic:** The logic is now expressed using SQLAlchemy's ORM, not raw SQL strings.
2.  **No More Type Errors:** The `pgvector` library, when used with the ORM, will **automatically handle the conversion** from your Python list/`ndarray` to the format the `asyncpg` driver needs. No more `.tolist()` or `::vector` casting.
3.  **More Maintainable:** If you ever change the `Note` model (e.g., add a column), the `select(Note)` query will automatically pick it up. Your old raw SQL query would not, and the manual `Note(...)` object creation would break.

What do you think of this plan? If you agree, I can generate the new `app/routes/semantic_search.py` file for you.