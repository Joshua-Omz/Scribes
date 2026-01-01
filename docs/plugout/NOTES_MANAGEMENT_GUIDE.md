# Notes Management Guide
**Create, Store, and Search Sermon Notes with AI-Powered Features**

## 📋 Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [For Frontend Developers](#for-frontend-developers)
4. [For DevOps Engineers](#for-devops-engineers)
5. [For Cloud Engineers](#for-cloud-engineers)
6. [API Reference](#api-reference)
7. [Data Model](#data-model)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Notes Management?

Scribes' Notes Management system enables users to:
- 📝 **Create and edit** rich sermon notes with markdown support
- 🏷️ **Organize** with tags, preacher names, and scripture references
- 🔍 **Search** semantically using AI embeddings
- 📊 **Auto-chunking** for efficient AI processing
- 🔗 **Cross-reference** related notes automatically
- 📤 **Export** notes to various formats

**Key Features:**
- ✅ Markdown support for formatting
- ✅ Automatic embedding generation (384-dim vectors)
- ✅ Intelligent chunking (512 tokens per chunk)
- ✅ Scripture reference parsing
- ✅ Tag-based organization
- ✅ Full-text and semantic search
- ✅ Version history (future)

**Technologies:**
- **PostgreSQL**: Primary storage with full-text search
- **pgvector**: Vector similarity search
- **Sentence Transformers**: Embedding generation (all-MiniLM-L6-v2)
- **SQLAlchemy**: ORM with async support

---

## How It Works

### Note Creation Flow

```
┌──────────────────────────────────────────────────────────┐
│              User Creates Note                            │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  POST /notes       │
         │  {title, content,  │
         │   preacher, tags}  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Validate Input    │
         │  - Title required  │
         │  - Content required│
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Save to Database  │
         │  (notes table)     │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Generate Embedding│
         │  - Combine fields  │
         │  - 384-dim vector  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Create Chunks     │
         │  (background task) │
         │  - 512 tokens each │
         │  - 50 token overlap│
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Invalidate Cache  │
         │  (L3 context cache)│
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Return Note       │
         │  with ID & metadata│
         └────────────────────┘
```

### Chunking Process

**Why Chunking?**
- Large notes exceed AI context windows
- Better semantic matching at paragraph level
- Improved retrieval relevance

**How It Works:**
```
Original Note (5000 words)
         │
         ├── Chunk 1 (512 tokens)
         │   "In the beginning..."
         │
         ├── Chunk 2 (512 tokens, 50 overlap)
         │   "...beginning God created..."
         │
         ├── Chunk 3 (512 tokens, 50 overlap)
         │   "...created the heavens..."
         │
         └── Chunk N (remaining tokens)
             "...and it was good."

Each chunk:
- Stored in note_chunks table
- Gets own 384-dim embedding
- Linked to parent note
- Used for semantic search
```

**Chunking Configuration:**
```python
# app/services/ai/chunking_service.py
CHUNK_SIZE = 512       # tokens per chunk
CHUNK_OVERLAP = 50     # token overlap between chunks
MIN_CHUNK_SIZE = 100   # minimum viable chunk size
```

### Embedding Generation

**Process:**
```
Note Content
    │
    ├── Combine Fields
    │   content + tags + scripture_refs
    │
    ├── Sentence Transformer Model
    │   (all-MiniLM-L6-v2)
    │   - Fast inference (~50ms)
    │   - 384 dimensions
    │
    └── Store Vector
        - note.embedding column
        - VECTOR(384) type (pgvector)
```

**Combined Text Format:**
```python
# Example combined text
"""
Content: In this sermon we explored the concept of faith...

Tags: faith, sermon, theology

Scripture: Hebrews 11:1, Romans 10:17
"""
```

---

## For Frontend Developers (Flutter/Dart)

### 1. Create a Note

**Endpoint:** `POST /notes`

**Request:**
```dart
import 'package:dio/dio.dart';

class Note {
  final int? id;
  final String title;
  final String content;
  final String? preacher;
  final String? tags;
  final String? scriptureRefs;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Note({
    this.id,
    required this.title,
    required this.content,
    this.preacher,
    this.tags,
    this.scriptureRefs,
    this.createdAt,
    this.updatedAt,
  });

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      preacher: json['preacher'],
      tags: json['tags'],
      scriptureRefs: json['scripture_refs'],
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : null,
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'content': content,
      'preacher': preacher,
      'tags': tags,
      'scripture_refs': scriptureRefs,
    };
  }
}

class NotesService {
  final Dio dio;

  NotesService(this.dio);

  Future<Note> createNote(Note note) async {
    final response = await dio.post('/notes', data: note.toJson());
    return Note.fromJson(response.data);
  }
}

// Usage
final note = await notesService.createNote(
  Note(
    title: 'Faith and Works',
    content: '# Main Theme\n\nFaith without works is dead...',
    preacher: 'John Smith',
    tags: 'faith,works,sermon',
    scriptureRefs: 'James 2:14-26, Ephesians 2:8-9',
  ),
);
```

**Response (201 Created):**
```json
{
  "id": 123,
  "title": "Faith and Works",
  "content": "# Main Theme\n\nFaith without works is dead...",
  "preacher": "John Smith",
  "tags": "faith,works,sermon",
  "scripture_refs": "James 2:14-26, Ephesians 2:8-9",
  "user_id": 1,
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T10:00:00Z",
  "chunk_count": 5
}
```

---

### 2. Get All Notes (Paginated)

**Endpoint:** `GET /notes`

**Request:**
```dart
class NotesListResponse {
  final List<Note> notes;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;

  NotesListResponse({
    required this.notes,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.totalPages,
  });

  factory NotesListResponse.fromJson(Map<String, dynamic> json) {
    return NotesListResponse(
      notes: (json['notes'] as List)
          .map((note) => Note.fromJson(note))
          .toList(),
      total: json['total'],
      page: json['page'],
      pageSize: json['page_size'],
      totalPages: json['total_pages'],
    );
  }
}

class NotesService {
  Future<NotesListResponse> getNotes({
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await dio.get(
      '/notes',
      queryParameters: {
        'page': page,
        'page_size': pageSize,
      },
    );
    return NotesListResponse.fromJson(response.data);
  }
}
```

**Response (200 OK):**
```json
{
  "notes": [
    {
      "id": 123,
      "title": "Faith and Works",
      "content": "...",
      "preacher": "John Smith",
      "tags": "faith,works,sermon",
      "created_at": "2025-12-24T10:00:00Z",
      "updated_at": "2025-12-24T10:00:00Z",
      "chunk_count": 5
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

### 3. Get Single Note

**Endpoint:** `GET /notes/{note_id}`

**Request:**
```dart
Future<Note> getNote(int noteId) async {
  final response = await dio.get('/notes/$noteId');
  return Note.fromJson(response.data);
}
```

---

### 4. Update Note

**Endpoint:** `PUT /notes/{note_id}`

**Request:**
```dart
Future<Note> updateNote(int noteId, Map<String, dynamic> updates) async {
  final response = await dio.put('/notes/$noteId', data: updates);
  return Note.fromJson(response.data);
}

// Usage
final updatedNote = await notesService.updateNote(
  123,
  {
    'title': 'Updated Title',
    'content': 'Updated content...'
  },
);
```

**Important Notes:**
- Only provided fields are updated (partial updates supported)
- Updating content triggers re-chunking (background task)
- Embeddings are regenerated automatically
- L3 cache is invalidated for fresh search results

---

### 5. Delete Note

**Endpoint:** `DELETE /notes/{note_id}`

**Request:**
```dart
Future<void> deleteNote(int noteId) async {
  await dio.delete('/notes/$noteId');
}
```

**What Gets Deleted:**
- Note record
- All associated chunks
- All embeddings
- Cross-references to/from this note
- L3 cache entries

---

### 6. Search Notes

**Endpoint:** `POST /notes/search`

**Full-Text Search:**
```dart
class SearchResult {
  final int noteId;
  final String title;
  final String snippet;
  final double? similarityScore;
  final String? preacher;
  final String? tags;

  SearchResult({
    required this.noteId,
    required this.title,
    required this.snippet,
    this.similarityScore,
    this.preacher,
    this.tags,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      noteId: json['note_id'],
      title: json['title'],
      snippet: json['snippet'],
      similarityScore: json['similarity_score']?.toDouble(),
      preacher: json['preacher'],
      tags: json['tags'],
    );
  }
}

Future<List<SearchResult>> searchNotes({
  required String query,
  bool semantic = false,
  int limit = 10,
}) async {
  final response = await dio.post(
    '/notes/search',
    data: {
      'query': query,
      'semantic': semantic,
      'limit': limit,
    },
  );

  return (response.data['results'] as List)
      .map((result) => SearchResult.fromJson(result))
      .toList();
}

// Usage
final results = await searchNotes(
  query: 'What does the Bible say about grace?',
  semantic: true,
  limit: 5,
);
```

---

### Flutter Widget Example

**notes_manager_screen.dart:**
```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class NotesProvider with ChangeNotifier {
  List<Note> _notes = [];
  bool _isLoading = false;
  int _currentPage = 1;
  final int _pageSize = 20;

  List<Note> get notes => _notes;
  bool get isLoading => _isLoading;
  int get currentPage => _currentPage;

  final NotesService _notesService;

  NotesProvider(this._notesService);

  Future<void> fetchNotes() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _notesService.getNotes(
        page: _currentPage,
        pageSize: _pageSize,
      );
      _notes = response.notes;
    } catch (e) {
      print('Failed to fetch notes: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> createNote(Note note) async {
    try {
      final createdNote = await _notesService.createNote(note);
      _notes.insert(0, createdNote);
      notifyListeners();
    } catch (e) {
      print('Failed to create note: $e');
      rethrow;
    }
  }

  Future<void> updateNote(int id, Map<String, dynamic> updates) async {
    try {
      final updatedNote = await _notesService.updateNote(id, updates);
      final index = _notes.indexWhere((n) => n.id == id);
      if (index != -1) {
        _notes[index] = updatedNote;
        notifyListeners();
      }
    } catch (e) {
      print('Failed to update note: $e');
      rethrow;
    }
  }

  Future<void> deleteNote(int id) async {
    try {
      await _notesService.deleteNote(id);
      _notes.removeWhere((n) => n.id == id);
      notifyListeners();
    } catch (e) {
      print('Failed to delete note: $e');
      rethrow;
    }
  }

  void nextPage() {
    _currentPage++;
    fetchNotes();
  }

  void previousPage() {
    if (_currentPage > 1) {
      _currentPage--;
      fetchNotes();
    }
  }
}

class NotesManagerScreen extends StatefulWidget {
  @override
  _NotesManagerScreenState createState() => _NotesManagerScreenState();
}

class _NotesManagerScreenState extends State<NotesManagerScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotesProvider>().fetchNotes();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('My Notes'),
        actions: [
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => _showCreateNoteDialog(context),
          ),
        ],
      ),
      body: Consumer<NotesProvider>(
        builder: (context, notesProvider, child) {
          if (notesProvider.isLoading) {
            return Center(child: CircularProgressIndicator());
          }

          if (notesProvider.notes.isEmpty) {
            return Center(
              child: Text('No notes yet. Create your first note!'),
            );
          }

          return Column(
            children: [
              Expanded(
                child: ListView.builder(
                  itemCount: notesProvider.notes.length,
                  itemBuilder: (context, index) {
                    final note = notesProvider.notes[index];
                    return NoteCard(
                      note: note,
                      onEdit: () => _showEditNoteDialog(context, note),
                      onDelete: () => _confirmDelete(context, note.id!),
                    );
                  },
                ),
              ),
              _buildPagination(context, notesProvider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPagination(BuildContext context, NotesProvider provider) {
    return Padding(
      padding: EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ElevatedButton(
            onPressed: provider.currentPage > 1
                ? () => provider.previousPage()
                : null,
            child: Text('Previous'),
          ),
          SizedBox(width: 16),
          Text('Page ${provider.currentPage}'),
          SizedBox(width: 16),
          ElevatedButton(
            onPressed: () => provider.nextPage(),
            child: Text('Next'),
          ),
        ],
      ),
    );
  }

  void _showCreateNoteDialog(BuildContext context) {
    final titleController = TextEditingController();
    final contentController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Create Note'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titleController,
              decoration: InputDecoration(labelText: 'Title'),
            ),
            TextField(
              controller: contentController,
              decoration: InputDecoration(labelText: 'Content'),
              maxLines: 5,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final note = Note(
                title: titleController.text,
                content: contentController.text,
              );
              await context.read<NotesProvider>().createNote(note);
              Navigator.pop(context);
            },
            child: Text('Create'),
          ),
        ],
      ),
    );
  }

  void _showEditNoteDialog(BuildContext context, Note note) {
    final titleController = TextEditingController(text: note.title);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Edit Note'),
        content: TextField(
          controller: titleController,
          decoration: InputDecoration(labelText: 'Title'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              await context.read<NotesProvider>().updateNote(
                note.id!,
                {'title': titleController.text},
              );
              Navigator.pop(context);
            },
            child: Text('Update'),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, int noteId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete Note'),
        content: Text('Are you sure you want to delete this note?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await context.read<NotesProvider>().deleteNote(noteId);
    }
  }
}

class NoteCard extends StatelessWidget {
  final Note note;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const NoteCard({
    required this.note,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              note.title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            if (note.preacher != null) ...[
              SizedBox(height: 4),
              Text('By: ${note.preacher}'),
            ],
            if (note.tags != null) ...[
              SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: note.tags!.split(',').map((tag) {
                  return Chip(
                    label: Text(tag.trim()),
                    backgroundColor: Colors.blue.shade100,
                  );
                }).toList(),
              ),
            ],
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: onEdit,
                  icon: Icon(Icons.edit),
                  label: Text('Edit'),
                ),
                TextButton.icon(
                  onPressed: onDelete,
                  icon: Icon(Icons.delete, color: Colors.red),
                  label: Text('Delete', style: TextStyle(color: Colors.red)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
```

**Markdown Editor Integration:**
```dart
import 'package:flutter_markdown/flutter_markdown.dart';

class NoteEditorScreen extends StatefulWidget {
  final Note? note;

  const NoteEditorScreen({this.note});

  @override
  _NoteEditorScreenState createState() => _NoteEditorScreenState();
}

class _NoteEditorScreenState extends State<NoteEditorScreen> {
  late TextEditingController _titleController;
  late TextEditingController _contentController;
  late TextEditingController _preacherController;
  late TextEditingController _tagsController;
  late TextEditingController _scriptureController;
  bool _showPreview = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.note?.title ?? '');
    _contentController = TextEditingController(text: widget.note?.content ?? '');
    _preacherController = TextEditingController(text: widget.note?.preacher ?? '');
    _tagsController = TextEditingController(text: widget.note?.tags ?? '');
    _scriptureController = TextEditingController(text: widget.note?.scriptureRefs ?? '');
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _preacherController.dispose();
    _tagsController.dispose();
    _scriptureController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.note == null ? 'New Note' : 'Edit Note'),
        actions: [
          IconButton(
            icon: Icon(_showPreview ? Icons.edit : Icons.preview),
            onPressed: () {
              setState(() {
                _showPreview = !_showPreview;
              });
            },
            tooltip: _showPreview ? 'Edit' : 'Preview',
          ),
          IconButton(
            icon: Icon(Icons.save),
            onPressed: _saveNote,
            tooltip: 'Save',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _titleController,
              decoration: InputDecoration(
                labelText: 'Note Title',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 16),
            _showPreview
                ? Container(
                    height: 400,
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Markdown(
                      data: _contentController.text,
                      selectable: true,
                    ),
                  )
                : TextField(
                    controller: _contentController,
                    decoration: InputDecoration(
                      labelText: 'Content (Markdown supported)',
                      border: OutlineInputBorder(),
                      hintText: 'Write your note in Markdown...',
                    ),
                    maxLines: 20,
                    keyboardType: TextInputType.multiline,
                  ),
            SizedBox(height: 16),
            TextField(
              controller: _preacherController,
              decoration: InputDecoration(
                labelText: 'Preacher Name',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 16),
            TextField(
              controller: _tagsController,
              decoration: InputDecoration(
                labelText: 'Tags (comma-separated)',
                border: OutlineInputBorder(),
                hintText: 'faith, grace, sermon',
              ),
            ),
            SizedBox(height: 16),
            TextField(
              controller: _scriptureController,
              decoration: InputDecoration(
                labelText: 'Scripture References',
                border: OutlineInputBorder(),
                hintText: 'John 3:16, Romans 8:28',
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _saveNote() async {
    final note = Note(
      id: widget.note?.id,
      title: _titleController.text,
      content: _contentController.text,
      preacher: _preacherController.text.isEmpty ? null : _preacherController.text,
      tags: _tagsController.text.isEmpty ? null : _tagsController.text,
      scriptureRefs: _scriptureController.text.isEmpty ? null : _scriptureController.text,
    );

    try {
      if (widget.note == null) {
        await context.read<NotesProvider>().createNote(note);
      } else {
        await context.read<NotesProvider>().updateNote(
          widget.note!.id!,
          note.toJson(),
        );
      }
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Note saved successfully')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to save note: $e')),
      );
    }
  }
}
```

**Dependencies (pubspec.yaml):**
```yaml
dependencies:
  flutter:
    sdk: flutter
  dio: ^5.4.0
  provider: ^6.1.1
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  flutter_markdown: ^0.6.18
```

---

## For DevOps Engineers

### Database Setup

**Required Extensions:**
```sql
-- Enable pgvector for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**Run Migrations:**
```bash
# Apply all migrations
alembic upgrade head

# Check current migration
alembic current

# View migration history
alembic history --verbose
```

---

### Monitoring

**Database Queries:**
```sql
-- Count notes by user
SELECT user_id, COUNT(*) as note_count
FROM notes
GROUP BY user_id
ORDER BY note_count DESC;

-- Find notes without embeddings
SELECT id, title, created_at
FROM notes
WHERE embedding IS NULL;

-- Average chunk count per note
SELECT AVG(chunk_count) as avg_chunks
FROM (
    SELECT note_id, COUNT(*) as chunk_count
    FROM note_chunks
    GROUP BY note_id
) subquery;

-- Storage size of embeddings
SELECT 
    pg_size_pretty(pg_total_relation_size('notes')) as notes_size,
    pg_size_pretty(pg_total_relation_size('note_chunks')) as chunks_size;
```

**Application Metrics:**
```python
# Monitor note creation rate
from prometheus_client import Counter, Histogram

notes_created = Counter('notes_created_total', 'Total notes created')
note_creation_duration = Histogram('note_creation_seconds', 'Note creation duration')

@note_creation_duration.time()
async def create_note(...):
    notes_created.inc()
    # ... creation logic
```

---

### Background Jobs

**Chunking Worker:**
```bash
# Start chunking worker (processes new notes)
celery -A app.worker.celery_app worker \
  --loglevel=info \
  --queues=chunking \
  --concurrency=2

# Monitor queue
celery -A app.worker.celery_app inspect active

# View failed tasks
celery -A app.worker.celery_app inspect failed
```

**Manual Reprocessing:**
```bash
# Re-chunk all notes (if algorithm changes)
python scripts/admin/rechunk_all_notes.py

# Regenerate embeddings
python scripts/admin/regenerate_embeddings.py
```

---

### Docker Configuration

**docker-compose.yml:**
```yaml
services:
  app:
    # ... app configuration
    environment:
      # Chunking settings
      CHUNK_SIZE: 512
      CHUNK_OVERLAP: 50
      MIN_CHUNK_SIZE: 100
      # Embedding model
      EMBEDDING_MODEL: sentence-transformers/all-MiniLM-L6-v2
    volumes:
      # Cache model files to avoid re-downloading
      - model_cache:/root/.cache/huggingface

  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: scribes
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Tune for vector operations
    command: >
      postgres
      -c shared_buffers=512MB
      -c effective_cache_size=2GB
      -c maintenance_work_mem=256MB
      -c max_parallel_workers_per_gather=4

  worker:
    build: .
    command: celery -A app.worker.celery_app worker --loglevel=info --queues=chunking
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
  model_cache:
```

---

### Performance Tuning

**PostgreSQL Indexes:**
```sql
-- Create indexes for common queries
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_created_at ON notes(created_at DESC);
CREATE INDEX idx_notes_tags ON notes USING gin(tags gin_trgm_ops);

-- Vector similarity index (HNSW for fast approximate nearest neighbor)
CREATE INDEX idx_notes_embedding ON notes USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_chunks_embedding ON note_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Query Performance:**
```sql
-- Analyze query plan for search
EXPLAIN ANALYZE
SELECT id, title, (embedding <=> '[0.1, 0.2, ...]'::vector) as distance
FROM notes
WHERE user_id = 1
ORDER BY distance
LIMIT 10;
```

---

## For Cloud Engineers

### AWS Deployment

**S3 for Model Cache:**
```bash
# Store embedding model in S3 to avoid re-downloading
aws s3 sync ~/.cache/huggingface/ s3://scribes-models/huggingface/

# In application startup:
aws s3 sync s3://scribes-models/huggingface/ ~/.cache/huggingface/
```

**RDS PostgreSQL:**
```bash
# Create RDS instance with pgvector
aws rds create-db-instance \
  --db-instance-identifier scribes-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password <password> \
  --allocated-storage 100 \
  --storage-type gp3 \
  --backup-retention-period 7

# Enable pgvector after creation
psql -h <rds-endpoint> -U admin -d scribes -c "CREATE EXTENSION vector;"
```

**ECS Task Definition:**
```json
{
  "family": "scribes-app",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "scribes:latest",
      "memory": 2048,
      "cpu": 1024,
      "environment": [
        {"name": "EMBEDDING_MODEL", "value": "sentence-transformers/all-MiniLM-L6-v2"},
        {"name": "CHUNK_SIZE", "value": "512"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:scribes/db-url"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "model-cache",
          "containerPath": "/root/.cache/huggingface"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "model-cache",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

---

### GCP Deployment

**Cloud SQL with pgvector:**
```bash
# Create instance
gcloud sql instances create scribes-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-7680 \
  --region=us-central1

# Enable pgvector (manually via Cloud SQL proxy)
gcloud sql connect scribes-db --user=postgres
> CREATE EXTENSION vector;
```

**Cloud Storage for Models:**
```bash
# Store models in GCS
gsutil -m rsync -r ~/.cache/huggingface/ gs://scribes-models/huggingface/

# Mount in GKE pod
apiVersion: v1
kind: Pod
spec:
  volumes:
  - name: model-cache
    gcePersistentDisk:
      pdName: model-cache-disk
  containers:
  - name: app
    volumeMounts:
    - name: model-cache
      mountPath: /root/.cache/huggingface
```

---

### Azure Deployment

**Azure Database for PostgreSQL:**
```bash
# Create server
az postgres flexible-server create \
  --name scribes-db \
  --resource-group scribes-rg \
  --location eastus \
  --admin-user admin \
  --admin-password <password> \
  --sku-name Standard_D2s_v3

# Enable pgvector
az postgres flexible-server execute \
  --name scribes-db \
  --admin-user admin \
  --admin-password <password> \
  --query "CREATE EXTENSION vector;"
```

---

## API Reference

### Note Endpoints

#### POST /notes
Create a new note.

**Request Body:**
```json
{
  "title": "string (1-255 chars, required)",
  "content": "string (required)",
  "preacher": "string (optional)",
  "tags": "string (comma-separated, optional)",
  "scripture_refs": "string (optional)"
}
```

**Responses:**
- `201 Created`: Note created successfully
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Not authenticated

---

#### GET /notes
Get paginated list of notes.

**Query Parameters:**
- `page` (integer, default=1): Page number
- `page_size` (integer, default=20, max=100): Items per page

**Responses:**
- `200 OK`: List of notes with pagination metadata
- `401 Unauthorized`: Not authenticated

---

#### GET /notes/{note_id}
Get a single note by ID.

**Path Parameters:**
- `note_id` (integer): Note ID

**Responses:**
- `200 OK`: Note details
- `404 Not Found`: Note doesn't exist or not owned by user
- `401 Unauthorized`: Not authenticated

---

#### PUT /notes/{note_id}
Update an existing note.

**Path Parameters:**
- `note_id` (integer): Note ID

**Request Body (all optional):**
```json
{
  "title": "string",
  "content": "string",
  "preacher": "string",
  "tags": "string",
  "scripture_refs": "string"
}
```

**Responses:**
- `200 OK`: Updated note
- `404 Not Found`: Note doesn't exist or not owned by user
- `401 Unauthorized`: Not authenticated

---

#### DELETE /notes/{note_id}
Delete a note.

**Path Parameters:**
- `note_id` (integer): Note ID

**Responses:**
- `200 OK`: Deletion confirmed
- `404 Not Found`: Note doesn't exist or not owned by user
- `401 Unauthorized`: Not authenticated

---

#### POST /notes/search
Search notes (full-text or semantic).

**Request Body:**
```json
{
  "query": "string (required)",
  "semantic": "boolean (default=false)",
  "limit": "integer (default=10, max=50)"
}
```

**Responses:**
- `200 OK`: Search results with similarity scores
- `401 Unauthorized`: Not authenticated

---

## Data Model

### Notes Table

```sql
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    preacher VARCHAR(255),
    tags TEXT,
    scripture_refs TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    embedding VECTOR(384),  -- Semantic embedding
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
```sql
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_created_at ON notes(created_at DESC);
CREATE INDEX idx_notes_embedding ON notes USING hnsw (embedding vector_cosine_ops);
```

---

### Note Chunks Table

```sql
CREATE TABLE note_chunks (
    id SERIAL PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,  -- Order of chunk
    content TEXT NOT NULL,
    embedding VECTOR(384),
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Why Chunks?**
- Enable processing of large notes
- Better semantic matching at paragraph level
- Used by AI assistant for context retrieval

---

## Troubleshooting

### Issue: "Embedding generation failed"

**Symptoms:**
- Note created but `embedding` is NULL
- Search doesn't return expected results

**Solutions:**
1. Check model is downloaded:
   ```bash
   ls ~/.cache/huggingface/hub/
   ```

2. Verify model path in config:
   ```bash
   echo $EMBEDDING_MODEL
   # Should be: sentence-transformers/all-MiniLM-L6-v2
   ```

3. Test embedding service:
   ```python
   from app.services.ai.embedding_service import get_embedding_service
   
   service = get_embedding_service()
   embedding = service.generate("test text")
   print(f"Embedding shape: {len(embedding)}")  # Should be 384
   ```

4. Check logs:
   ```bash
   grep "Failed to generate embedding" /var/log/scribes/app.log
   ```

---

### Issue: "Chunking not happening"

**Symptoms:**
- Large notes created but no chunks in database
- `note_chunks` table is empty

**Solutions:**
1. Check worker is running:
   ```bash
   celery -A app.worker.celery_app inspect active
   ```

2. Check Redis connection:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. Manual chunking:
   ```python
   from app.services.ai.chunking_service import ChunkingService
   from app.models.note_model import Note
   
   chunking_service = ChunkingService()
   note = Note.query.get(note_id)
   chunks = chunking_service.chunk_note(note)
   print(f"Created {len(chunks)} chunks")
   ```

---

### Issue: "Slow search performance"

**Symptoms:**
- Search takes > 1 second
- High database CPU usage

**Solutions:**
1. Check indexes exist:
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename IN ('notes', 'note_chunks');
   ```

2. Create HNSW index if missing:
   ```sql
   CREATE INDEX CONCURRENTLY idx_notes_embedding 
   ON notes USING hnsw (embedding vector_cosine_ops)
   WITH (m = 16, ef_construction = 64);
   ```

3. Analyze query plan:
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM notes
   WHERE embedding <=> '[...]'::vector < 0.5
   LIMIT 10;
   ```

4. Tune PostgreSQL:
   ```sql
   -- Increase shared buffers for vector ops
   ALTER SYSTEM SET shared_buffers = '512MB';
   ALTER SYSTEM SET effective_cache_size = '2GB';
   SELECT pg_reload_conf();
   ```

---

### Issue: "Note not found after creation"

**Symptoms:**
- POST returns 201 but GET returns 404
- Note visible in database but not via API

**Solutions:**
1. Check user ownership:
   ```sql
   SELECT id, title, user_id FROM notes WHERE id = ?;
   ```

2. Verify authentication:
   ```typescript
   // Ensure using same token for both requests
   const token = localStorage.getItem('access_token');
   ```

3. Check authorization logic:
   ```python
   # In note_service.py
   note = await note_repo.get_by_id(note_id)
   if note.user_id != current_user.id:
       raise HTTPException(404, "Note not found")
   ```

---

## Performance Metrics

### Target Response Times
- **Create Note:** < 500ms (without chunking)
- **Get Notes (paginated):** < 200ms
- **Get Single Note:** < 100ms
- **Update Note:** < 300ms
- **Delete Note:** < 200ms
- **Search (semantic):** < 1000ms

### Storage Estimates
- **Average Note:** 5KB content + 1.5KB embedding = 6.5KB
- **1000 notes:** ~6.5MB
- **Average Chunks:** 5 per note
- **1000 notes with chunks:** ~40MB total

### Embedding Generation
- **Model:** all-MiniLM-L6-v2
- **Time per note:** ~50ms (CPU), ~20ms (GPU)
- **Batch processing:** 100 notes/second (GPU)

---

## Summary

### Key Points
✅ **Rich sermon notes** with markdown, tags, and scripture refs  
✅ **AI-powered search** using 384-dim embeddings  
✅ **Automatic chunking** for efficient processing  
✅ **Full-text and semantic** search capabilities  
✅ **Background workers** for heavy operations  
✅ **Production-ready** with monitoring and optimization  

### Quick Commands
```bash
# Create note via API
curl -X POST http://localhost:8000/notes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Content..."}'

# Check chunking queue
celery -A app.worker.celery_app inspect active

# Monitor database size
psql -c "SELECT pg_size_pretty(pg_database_size('scribes'));"
```

---

**Document Version:** 1.0  
**Last Updated:** December 24, 2025  
**Related Docs:** [AI Assistant Guide](./AI_ASSISTANT_GUIDE.md) | [Cross-References Guide](./CROSS_REFERENCES_GUIDE.md)
