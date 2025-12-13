"""
Create Test Data for AssistantService Manual Testing

This script:
1. Creates a test user
2. Creates 5 theological notes with real sermon content
3. Chunks each note using TokenizerService
4. Generates embeddings for each chunk
5. Saves everything to database

Usage:
    python create_test_data.py
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user_model import User
from app.models.note_model import Note
from app.models.note_chunk_model import NoteChunk
from app.services.tokenizer_service import get_tokenizer_service
from app.services.embedding_service import get_embedding_service
from datetime import datetime
from sqlalchemy import select


# ===========================
# TEST DATA - THEOLOGICAL NOTES
# ===========================

TEST_NOTES = [
    {
        "title": "Understanding God's Grace",
        "content": """
Grace is the unmerited favor of God towards humanity. It is not something we can earn 
through our good works or righteous deeds. As Ephesians 2:8-9 teaches us, "For by grace 
you have been saved through faith, and that not of yourselves; it is the gift of God, 
not of works, lest anyone should boast."

The grace of God is freely given to all who believe. Romans 3:24 reminds us that we are 
"justified freely by His grace through the redemption that is in Christ Jesus." This means 
our standing before God is not based on our performance but on Christ's finished work on 
the cross.

Grace empowers us to live righteously. Titus 2:11-12 declares, "For the grace of God that 
brings salvation has appeared to all men, teaching us that, denying ungodliness and worldly 
lusts, we should live soberly, righteously, and godly in the present age."

When we truly understand grace, it transforms how we relate to God and others. We no longer 
approach Him with fear and shame, but with confidence, knowing we are accepted in Christ. 
This liberating truth frees us to serve Him out of love rather than obligation.
        """,
        "tags": ["grace", "salvation", "theology"]
    },
    {
        "title": "The Power of Faith",
        "content": """
Faith is the foundation of our relationship with God. Hebrews 11:1 defines faith as 
"the substance of things hoped for, the evidence of things not seen." Faith is not blind 
belief, but confident trust in God's character and promises.

Without faith, it is impossible to please God (Hebrews 11:6). Faith is what moves the 
heart of God and releases His power into our lives. When we exercise faith, we demonstrate 
our trust in His goodness and sovereignty.

The Bible is filled with examples of men and women who pleased God through their faith. 
Abraham believed God's promise of a son even in his old age. Moses chose to suffer with 
God's people rather than enjoy the pleasures of Egypt. David faced Goliath with nothing 
but a sling and unwavering trust in the Lord.

Our faith grows as we hear God's Word (Romans 10:17) and step out in obedience to His 
leading. Small acts of faith build spiritual muscle for greater challenges ahead. As we 
walk by faith and not by sight (2 Corinthians 5:7), we discover God's faithfulness in 
every season of life.
        """,
        "tags": ["faith", "trust", "spiritual growth"]
    },
    {
        "title": "God's Unfailing Love",
        "content": """
The love of God is the central message of the Gospel. John 3:16 declares, "For God so 
loved the world that He gave His only begotten Son, that whoever believes in Him should 
not perish but have everlasting life." This verse encapsulates the depth and breadth of 
divine love.

God's love is unconditional and unchanging. Romans 8:38-39 assures us that nothing can 
separate us from the love of God in Christ Jesus. Not our failures, not our circumstances, 
not even death itself can sever this bond of love.

We love because He first loved us (1 John 4:19). Understanding God's love transforms how 
we love others. It enables us to forgive as we have been forgiven, to show mercy as we 
have received mercy, and to extend grace as grace has been given to us.

The cross is the ultimate demonstration of God's love. While we were still sinners, Christ 
died for us (Romans 5:8). This sacrificial love calls us to a life of loving service to 
God and others, knowing that we are deeply loved and fully accepted.
        """,
        "tags": ["love", "gospel", "compassion"]
    },
    {
        "title": "The Practice of Prayer",
        "content": """
Prayer is our direct line of communication with the Father. Jesus taught His disciples to 
pray with confidence and persistence. In Matthew 6:9-13, He gave us the Lord's Prayer as 
a model for approaching God with reverence, petition, and trust.

Effective prayer combines faith with perseverance. James 5:16 tells us that "the effective, 
fervent prayer of a righteous man avails much." Our prayers have power not because of our 
eloquence, but because of the One who hears them.

Prayer should be a constant practice in our lives. 1 Thessalonians 5:17 encourages us to 
"pray without ceasing." This doesn't mean we're always on our knees, but that we maintain 
an ongoing conversation with God throughout our day.

When we pray according to God's will, we can have confidence that He hears us (1 John 5:14-15). 
Prayer aligns our hearts with God's purposes and opens the door for His power to work in 
and through us. It is both a privilege and a powerful weapon in spiritual warfare.
        """,
        "tags": ["prayer", "communication", "spiritual discipline"]
    },
    {
        "title": "Walking in the Spirit",
        "content": """
The Holy Spirit is our Helper, Comforter, and Guide. Jesus promised in John 14:16-17 that 
the Father would send the Spirit of truth to be with us forever. This promise was fulfilled 
on the day of Pentecost when the Spirit was poured out on believers.

Walking in the Spirit means yielding to His control and following His leading. Galatians 
5:16 instructs us to "walk in the Spirit, and you shall not fulfill the lust of the flesh." 
The Spirit empowers us to overcome sinful desires and live in righteousness.

The fruit of the Spirit - love, joy, peace, patience, kindness, goodness, faithfulness, 
gentleness, and self-control (Galatians 5:22-23) - is evidence of His work in our lives. 
These qualities are not produced by human effort but by surrender to the Spirit's influence.

We are sealed with the Holy Spirit as a guarantee of our inheritance (Ephesians 1:13-14). 
He convicts us of sin, guides us into truth, and empowers us for service. As we learn to 
listen to and obey His gentle promptings, we experience the abundant life Jesus promised.
        """,
        "tags": ["holy spirit", "spiritual life", "sanctification"]
    }
]


async def create_test_user(db: AsyncSession) -> User:
    """Create or get test user"""
    test_email = "test@scribes.local"
    
    # Check if user exists
    result = await db.execute(select(User).filter(User.email == test_email))
    user = result.scalar_one_or_none()
    
    if user:
        print(f"✅ Test user already exists: {test_email} (ID: {user.id})")
        return user
    
    # Create new user
    user = User(
        email=test_email,
        username="Test User",
        hashed_password="$2b$12$dummyhashedpassword",  # Dummy bcrypt hash
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    print(f"✅ Created test user: {test_email} (ID: {user.id})")
    return user


async def create_note_with_chunks(
    db: AsyncSession,
    user_id: int,
    title: str,
    content: str,
    tags: list
) -> Note:
    """
    Create a note and automatically generate chunks with embeddings
    
    Steps:
    1. Create and save note
    2. Chunk the content using TokenizerService
    3. Generate embeddings for each chunk
    4. Save chunks to database
    """
    
    # Initialize services (these are synchronous singletons)
    tokenizer = get_tokenizer_service()
    embedding_service = get_embedding_service()
    
    # 1. Create note
    # Convert tags list to comma-separated string
    tags_str = ", ".join(tags) if isinstance(tags, list) else tags
    
    note = Note(
        user_id=user_id,
        title=title,
        content=content,
        tags=tags_str,  # Convert list to string
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    print(f"\n📝 Created note: '{title}' (ID: {note.id})")
    
    # 2. Chunk the content (synchronous operation)
    chunks_text = tokenizer.chunk_text(
        text=content,
        chunk_size=200,  # Same as settings.chunking_size
        overlap=50       # Same as settings.chunking_overlap
    )
    
    print(f"   └─ Generated {len(chunks_text)} chunks")
    
    # 3. Generate embeddings and save chunks
    for i, chunk_text in enumerate(chunks_text):
        # Generate embedding (synchronous - returns list of floats)
        embedding_array = embedding_service.generate(chunk_text)
        
        # Convert to list if needed (generate() already returns a list)
        embedding_list = embedding_array if isinstance(embedding_array, list) else embedding_array.tolist()
        
        # Create chunk with embedding
        chunk = NoteChunk(
            note_id=note.id,
            chunk_idx=i,  # chunk_idx is the correct field name
            chunk_text=chunk_text,  # chunk_text is the correct field name
            embedding=embedding_list  # pgvector expects list
        )
        
        db.add(chunk)
    
    await db.commit()
    print(f"   └─ Saved {len(chunks_text)} chunks with embeddings to database")
    
    return note


async def verify_data(db: AsyncSession, user_id: int):
    """Verify test data was created successfully"""
    
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)
    
    # Count notes
    notes_result = await db.execute(select(Note).filter(Note.user_id == user_id))
    notes = notes_result.scalars().all()
    notes_count = len(notes)
    print(f"✅ Notes created: {notes_count}")
    
    # Count chunks (join with notes to filter by user_id)
    from sqlalchemy import and_
    chunks_result = await db.execute(
        select(NoteChunk)
        .join(Note, NoteChunk.note_id == Note.id)
        .filter(Note.user_id == user_id)
    )
    chunks = chunks_result.scalars().all()
    chunks_count = len(chunks)
    print(f"✅ Chunks created: {chunks_count}")
    
    # Verify embeddings
    if chunks:
        sample_chunk = chunks[0]
        if sample_chunk.embedding is not None and len(sample_chunk.embedding) > 0:
            embedding_dim = len(sample_chunk.embedding)
            print(f"✅ Embedding dimension: {embedding_dim}")
            
            if embedding_dim == 384:
                print("✅ Embeddings are correct dimension (384)")
            else:
                print(f"⚠️  Warning: Expected 384 dimensions, got {embedding_dim}")
        else:
            print("❌ Sample chunk has no embedding!")
    
    print("\n" + "=" * 60)
    print("✅ TEST DATA CREATION COMPLETE!")
    print("=" * 60)
    print(f"\nTest User ID: {user_id}")
    print(f"Test User Email: test@scribes.local")
    print(f"Total Notes: {notes_count}")
    print(f"Total Chunks: {chunks_count}")
    print(f"\n💡 You can now use this data for manual testing!")
    print(f"   See: docs/guides/backend implementations/ASSISTANT_MANUAL_TESTING_GUIDE.md")
    print("\nYou can now run manual tests using this user ID.")


async def main():
    """Main execution"""
    
    print("=" * 60)
    print("SCRIBES - TEST DATA CREATION SCRIPT")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Create a test user")
    print("  2. Create 5 theological notes")
    print("  3. Generate chunks for each note")
    print("  4. Generate embeddings for each chunk")
    print("  5. Save everything to database\n")
    
    # Get database session using async context manager
    async with AsyncSessionLocal() as db:
        try:
            # Create test user
            user = await create_test_user(db)
            
            # Create notes with chunks
            for note_data in TEST_NOTES:
                await create_note_with_chunks(
                    db=db,
                    user_id=user.id,
                    title=note_data["title"],
                    content=note_data["content"],
                    tags=note_data["tags"]
                )
            
            # Verify data
            await verify_data(db, user.id)
            
        except Exception as e:
            print(f"\n❌ Error creating test data: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    # Run async main function
    asyncio.run(main())