# Cross-Reference Feature Implementation Guide

## Overview

The Cross-Reference (CrossRef) feature enables users to create semantic connections between their sermon notes, building a knowledge graph of related spiritual insights. This feature supports both manual and AI-generated cross-references with typed relationships and confidence scoring.

## Table of Contents

1. [Architecture](#architecture)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Examples](#requestresponse-examples)
5. [Business Rules](#business-rules)
6. [Frontend Integration](#frontend-integration)
7. [Future Enhancements](#future-enhancements)

---

## Architecture

The CrossRef feature follows the same layered architecture as other features:

```
┌─────────────────┐
│   API Routes    │  ← REST endpoints (cross_ref_routes.py)
└────────┬────────┘
         │
┌────────▼────────┐
│    Service      │  ← Business logic & validation (cross_ref_service.py)
└────────┬────────┘
         │
┌────────▼────────┐
│   Repository    │  ← Data access layer (cross_ref_repository.py)
└────────┬────────┘
         │
┌────────▼────────┐
│  SQLAlchemy     │  ← ORM model (cross_ref_model.py)
│     Model       │
└─────────────────┘
```

### Components

**1. Model (`app/models/cross_ref_model.py`)**
- SQLAlchemy ORM model for the `cross_refs` table
- Defines relationships with Note model (bidirectional)
- Handles cascade deletes when notes are removed

**2. Schemas (`app/schemas/cross_ref_schemas.py`)**
- Pydantic models for request/response validation
- Includes schemas for CRUD operations and bulk operations
- Validates reference types and confidence scores

**3. Repository (`app/repositories/cross_ref_repository.py`)**
- Async database operations using AsyncSession
- CRUD methods for cross-references
- Bidirectional query methods (outgoing/incoming refs)
- Bulk operations support

**4. Service (`app/services/cross_ref_service.py`)**
- Business logic and validation rules
- Ownership verification
- Duplicate prevention
- Note existence validation

**5. Routes (`app/api/cross_ref_routes.py`)**
- REST API endpoints with OpenAPI documentation
- Authentication required for all endpoints
- Comprehensive error handling

---

## Database Schema

### CrossRef Table

```sql
CREATE TABLE cross_refs (
    id SERIAL PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    other_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    reference_type VARCHAR(50) DEFAULT 'related',
    description TEXT,
    is_auto_generated VARCHAR(20) DEFAULT 'manual',
    confidence_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_different_notes CHECK (note_id != other_note_id),
    CONSTRAINT check_confidence_score CHECK (confidence_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_cross_refs_note_id ON cross_refs(note_id);
CREATE INDEX idx_cross_refs_other_note_id ON cross_refs(other_note_id);
CREATE INDEX idx_cross_refs_reference_type ON cross_refs(reference_type);
```

### Relationships

- **Note.outgoing_refs**: Cross-references from this note to other notes
- **Note.incoming_refs**: Cross-references from other notes to this note
- **Cascade Delete**: When a note is deleted, all associated cross-references are automatically removed

### Reference Types

- `related` - General relationship between notes
- `references` - One note references scripture or content from another
- `cited_by` - One note is cited by another
- `expands_on` - Note provides more detail on another note's topic
- `contradicts` - Notes present opposing viewpoints
- `supports` - Note supports arguments in another note
- `follows` - Sequential relationship (chronological or logical)
- `precedes` - Note comes before another in sequence

### Auto-Generated Types

- `manual` - Created by user
- `ai_suggested` - AI suggested but not auto-created
- `ai_auto` - Automatically created by AI

---

## API Endpoints

Base URL: `/cross-refs`

All endpoints require authentication via Bearer token.

### 1. Create Cross-Reference

**POST** `/cross-refs/`

Create a new cross-reference between two notes.

**Request Body:**
```json
{
  "note_id": 1,
  "other_note_id": 2,
  "reference_type": "expands_on",
  "description": "This note provides additional context on grace theology",
  "is_auto_generated": "manual",
  "confidence_score": null
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "note_id": 1,
  "other_note_id": 2,
  "reference_type": "expands_on",
  "description": "This note provides additional context on grace theology",
  "is_auto_generated": "manual",
  "confidence_score": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Cannot reference same note, duplicate exists
- `403 Forbidden` - User doesn't own one or both notes
- `404 Not Found` - One or both notes don't exist

---

### 2. Bulk Create Cross-References

**POST** `/cross-refs/bulk`

Create multiple cross-references at once.

**Request Body:**
```json
{
  "cross_refs": [
    {
      "note_id": 1,
      "other_note_id": 2,
      "reference_type": "related"
    },
    {
      "note_id": 1,
      "other_note_id": 3,
      "reference_type": "supports"
    }
  ],
  "skip_errors": true
}
```

**Response:** `201 Created`
```json
[
  {
    "id": 1,
    "note_id": 1,
    "other_note_id": 2,
    "reference_type": "related",
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "note_id": 1,
    "other_note_id": 3,
    "reference_type": "supports",
    "created_at": "2024-01-15T10:30:01Z"
  }
]
```

---

### 3. Get Cross-Reference by ID

**GET** `/cross-refs/{cross_ref_id}`

Retrieve a specific cross-reference with full note details.

**Response:** `200 OK`
```json
{
  "id": 1,
  "note_id": 1,
  "other_note_id": 2,
  "reference_type": "expands_on",
  "description": "This note provides additional context on grace theology",
  "is_auto_generated": "manual",
  "confidence_score": null,
  "created_at": "2024-01-15T10:30:00Z",
  "note_title": "Grace in the Old Testament",
  "note_preview": "Exploring how grace appears throughout Old Testament...",
  "other_note_title": "New Testament Grace",
  "other_note_preview": "Paul's teaching on grace and its implications..."
}
```

---

### 4. Get All Cross-References for a Note

**GET** `/cross-refs/note/{note_id}?skip=0&limit=100`

Get all cross-references (both incoming and outgoing) for a specific note.

**Response:** `200 OK`
```json
{
  "cross_refs": [
    {
      "id": 1,
      "note_id": 1,
      "other_note_id": 2,
      "reference_type": "expands_on",
      "note_title": "Grace in the Old Testament",
      "other_note_title": "New Testament Grace",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

---

### 5. Get Outgoing Cross-References

**GET** `/cross-refs/note/{note_id}/outgoing?skip=0&limit=100`

Get only outgoing references (references this note makes to other notes).

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "note_id": 1,
    "other_note_id": 2,
    "reference_type": "expands_on",
    "note_title": "Grace in the Old Testament",
    "other_note_title": "New Testament Grace",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### 6. Get Incoming Cross-References

**GET** `/cross-refs/note/{note_id}/incoming?skip=0&limit=100`

Get only incoming references (references other notes make to this note).

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "note_id": 3,
    "other_note_id": 1,
    "reference_type": "references",
    "note_title": "Faith and Works",
    "other_note_title": "Grace in the Old Testament",
    "created_at": "2024-01-15T11:00:00Z"
  }
]
```

---

### 7. Get Related Notes

**GET** `/cross-refs/note/{note_id}/related?reference_types=related,expands_on&skip=0&limit=100`

Get all notes that are cross-referenced with the given note, optionally filtered by reference type.

**Query Parameters:**
- `reference_types` (optional) - Comma-separated list of types to filter by
- `skip` (default: 0)
- `limit` (default: 100, max: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "user_id": 1,
    "title": "New Testament Grace",
    "content": "Paul's teaching on grace...",
    "preacher": "Pastor John",
    "tags": ["grace", "paul", "theology"],
    "scripture_refs": ["Ephesians 2:8-9", "Romans 3:24"],
    "created_at": "2024-01-10T09:00:00Z",
    "updated_at": "2024-01-10T09:00:00Z"
  }
]
```

---

### 8. Get Cross-Reference Count

**GET** `/cross-refs/note/{note_id}/count`

Get statistics on cross-references for a note.

**Response:** `200 OK`
```json
{
  "note_id": 1,
  "total_cross_refs": 5,
  "outgoing_refs": 3,
  "incoming_refs": 2
}
```

---

### 9. Update Cross-Reference

**PUT** `/cross-refs/{cross_ref_id}`

Update an existing cross-reference's metadata.

**Request Body:**
```json
{
  "reference_type": "supports",
  "description": "Updated description showing how this supports the argument",
  "confidence_score": 95
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "note_id": 1,
  "other_note_id": 2,
  "reference_type": "supports",
  "description": "Updated description showing how this supports the argument",
  "is_auto_generated": "manual",
  "confidence_score": 95,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### 10. Delete Cross-Reference

**DELETE** `/cross-refs/{cross_ref_id}`

Delete a cross-reference. Only the owner of the source note can delete.

**Response:** `204 No Content`

---

### 11. Get AI Suggestions (Future Feature)

**GET** `/cross-refs/suggestions/{note_id}?limit=10`

Get AI-suggested cross-references for a note.

**Response:** `200 OK`
```json
[]
```

*Note: This endpoint is a placeholder for future AI integration. Currently returns an empty array.*

---

## Business Rules

### 1. Ownership Validation

- Users can only create cross-references between their own notes
- Both source and target notes must belong to the authenticated user
- Users can view cross-references where they own either the source or target note

### 2. Duplicate Prevention

- The system checks for existing cross-references between two notes (bidirectional)
- A cross-reference from Note A → Note B prevents creating A → B or B → A
- This prevents redundant relationships in the knowledge graph

### 3. Self-Reference Prevention

- Notes cannot reference themselves
- Validation occurs at both schema and database levels

### 4. Cascade Deletion

- When a note is deleted, all associated cross-references are automatically removed
- This maintains referential integrity in the knowledge graph

### 5. Confidence Scoring

- Optional field for AI-generated cross-references
- Range: 0-100 (validated at schema and database levels)
- Manual references typically don't use this field

---

## Frontend Integration

### Flutter/Dart Example

#### 1. Data Models

```dart
class CrossRef {
  final int id;
  final int noteId;
  final int otherNoteId;
  final String referenceType;
  final String? description;
  final String isAutoGenerated;
  final int? confidenceScore;
  final DateTime createdAt;

  CrossRef({
    required this.id,
    required this.noteId,
    required this.otherNoteId,
    required this.referenceType,
    this.description,
    required this.isAutoGenerated,
    this.confidenceScore,
    required this.createdAt,
  });

  factory CrossRef.fromJson(Map<String, dynamic> json) {
    return CrossRef(
      id: json['id'],
      noteId: json['note_id'],
      otherNoteId: json['other_note_id'],
      referenceType: json['reference_type'],
      description: json['description'],
      isAutoGenerated: json['is_auto_generated'],
      confidenceScore: json['confidence_score'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'note_id': noteId,
      'other_note_id': otherNoteId,
      'reference_type': referenceType,
      'description': description,
      'is_auto_generated': isAutoGenerated,
      'confidence_score': confidenceScore,
    };
  }
}

class CrossRefWithDetails extends CrossRef {
  final String noteTitle;
  final String notePreview;
  final String otherNoteTitle;
  final String otherNotePreview;

  CrossRefWithDetails({
    required super.id,
    required super.noteId,
    required super.otherNoteId,
    required super.referenceType,
    super.description,
    required super.isAutoGenerated,
    super.confidenceScore,
    required super.createdAt,
    required this.noteTitle,
    required this.notePreview,
    required this.otherNoteTitle,
    required this.otherNotePreview,
  });

  factory CrossRefWithDetails.fromJson(Map<String, dynamic> json) {
    return CrossRefWithDetails(
      id: json['id'],
      noteId: json['note_id'],
      otherNoteId: json['other_note_id'],
      referenceType: json['reference_type'],
      description: json['description'],
      isAutoGenerated: json['is_auto_generated'],
      confidenceScore: json['confidence_score'],
      createdAt: DateTime.parse(json['created_at']),
      noteTitle: json['note_title'],
      notePreview: json['note_preview'],
      otherNoteTitle: json['other_note_title'],
      otherNotePreview: json['other_note_preview'],
    );
  }
}
```

#### 2. API Service

```dart
class CrossRefService {
  final Dio _dio;
  static const String _baseUrl = '/cross-refs';

  CrossRefService(this._dio);

  /// Create a new cross-reference
  Future<CrossRef> createCrossRef({
    required int noteId,
    required int otherNoteId,
    String referenceType = 'related',
    String? description,
  }) async {
    try {
      final response = await _dio.post(
        _baseUrl,
        data: {
          'note_id': noteId,
          'other_note_id': otherNoteId,
          'reference_type': referenceType,
          'description': description,
          'is_auto_generated': 'manual',
        },
      );

      return CrossRef.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get all cross-references for a note
  Future<List<CrossRefWithDetails>> getNoteCrossRefs(
    int noteId, {
    int skip = 0,
    int limit = 100,
  }) async {
    try {
      final response = await _dio.get(
        '$_baseUrl/note/$noteId',
        queryParameters: {
          'skip': skip,
          'limit': limit,
        },
      );

      final List<dynamic> crossRefs = response.data['cross_refs'];
      return crossRefs
          .map((json) => CrossRefWithDetails.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get outgoing cross-references
  Future<List<CrossRefWithDetails>> getOutgoingRefs(
    int noteId, {
    int skip = 0,
    int limit = 100,
  }) async {
    try {
      final response = await _dio.get(
        '$_baseUrl/note/$noteId/outgoing',
        queryParameters: {
          'skip': skip,
          'limit': limit,
        },
      );

      final List<dynamic> crossRefs = response.data;
      return crossRefs
          .map((json) => CrossRefWithDetails.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get incoming cross-references
  Future<List<CrossRefWithDetails>> getIncomingRefs(
    int noteId, {
    int skip = 0,
    int limit = 100,
  }) async {
    try {
      final response = await _dio.get(
        '$_baseUrl/note/$noteId/incoming',
        queryParameters: {
          'skip': skip,
          'limit': limit,
        },
      );

      final List<dynamic> crossRefs = response.data;
      return crossRefs
          .map((json) => CrossRefWithDetails.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get related notes
  Future<List<Note>> getRelatedNotes(
    int noteId, {
    List<String>? referenceTypes,
    int skip = 0,
    int limit = 100,
  }) async {
    try {
      final Map<String, dynamic> queryParams = {
        'skip': skip,
        'limit': limit,
      };

      if (referenceTypes != null && referenceTypes.isNotEmpty) {
        queryParams['reference_types'] = referenceTypes.join(',');
      }

      final response = await _dio.get(
        '$_baseUrl/note/$noteId/related',
        queryParameters: queryParams,
      );

      final List<dynamic> notes = response.data;
      return notes.map((json) => Note.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get cross-reference count
  Future<Map<String, int>> getCrossRefCount(int noteId) async {
    try {
      final response = await _dio.get('$_baseUrl/note/$noteId/count');
      return {
        'total': response.data['total_cross_refs'],
        'outgoing': response.data['outgoing_refs'],
        'incoming': response.data['incoming_refs'],
      };
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Update cross-reference
  Future<CrossRef> updateCrossRef(
    int crossRefId, {
    String? referenceType,
    String? description,
    int? confidenceScore,
  }) async {
    try {
      final Map<String, dynamic> data = {};
      if (referenceType != null) data['reference_type'] = referenceType;
      if (description != null) data['description'] = description;
      if (confidenceScore != null) data['confidence_score'] = confidenceScore;

      final response = await _dio.put(
        '$_baseUrl/$crossRefId',
        data: data,
      );

      return CrossRef.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Delete cross-reference
  Future<void> deleteCrossRef(int crossRefId) async {
    try {
      await _dio.delete('$_baseUrl/$crossRefId');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Bulk create cross-references
  Future<List<CrossRef>> bulkCreateCrossRefs(
    List<Map<String, dynamic>> crossRefs, {
    bool skipErrors = true,
  }) async {
    try {
      final response = await _dio.post(
        '$_baseUrl/bulk',
        data: {
          'cross_refs': crossRefs,
          'skip_errors': skipErrors,
        },
      );

      final List<dynamic> created = response.data;
      return created.map((json) => CrossRef.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException e) {
    if (e.response != null) {
      return e.response!.data['detail'] ?? 'An error occurred';
    }
    return 'Network error';
  }
}
```

#### 3. UI Example - Cross-Reference List

```dart
class CrossRefList extends ConsumerWidget {
  final int noteId;

  const CrossRefList({required this.noteId, super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<List<CrossRefWithDetails>>(
      future: ref.read(crossRefServiceProvider).getNoteCrossRefs(noteId),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return Center(
            child: Text('Error: ${snapshot.error}'),
          );
        }

        final crossRefs = snapshot.data ?? [];

        if (crossRefs.isEmpty) {
          return const Center(
            child: Text('No cross-references yet'),
          );
        }

        return ListView.builder(
          itemCount: crossRefs.length,
          itemBuilder: (context, index) {
            final crossRef = crossRefs[index];
            final isOutgoing = crossRef.noteId == noteId;

            return Card(
              child: ListTile(
                leading: Icon(
                  _getReferenceTypeIcon(crossRef.referenceType),
                  color: _getReferenceTypeColor(crossRef.referenceType),
                ),
                title: Text(
                  isOutgoing
                      ? crossRef.otherNoteTitle
                      : crossRef.noteTitle,
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isOutgoing
                          ? crossRef.otherNotePreview
                          : crossRef.notePreview,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${crossRef.referenceType} ${isOutgoing ? "→" : "←"}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
                trailing: IconButton(
                  icon: const Icon(Icons.delete),
                  onPressed: () => _deleteCrossRef(context, ref, crossRef.id),
                ),
                onTap: () => _navigateToNote(
                  context,
                  isOutgoing ? crossRef.otherNoteId : crossRef.noteId,
                ),
              ),
            );
          },
        );
      },
    );
  }

  IconData _getReferenceTypeIcon(String type) {
    switch (type) {
      case 'related':
        return Icons.link;
      case 'expands_on':
        return Icons.add_circle;
      case 'supports':
        return Icons.thumb_up;
      case 'contradicts':
        return Icons.warning;
      case 'references':
        return Icons.menu_book;
      default:
        return Icons.link;
    }
  }

  Color _getReferenceTypeColor(String type) {
    switch (type) {
      case 'supports':
        return Colors.green;
      case 'contradicts':
        return Colors.red;
      case 'expands_on':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  Future<void> _deleteCrossRef(
    BuildContext context,
    WidgetRef ref,
    int crossRefId,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Cross-Reference'),
        content: const Text('Are you sure you want to delete this reference?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ref.read(crossRefServiceProvider).deleteCrossRef(crossRefId);
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Cross-reference deleted')),
          );
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }
      }
    }
  }

  void _navigateToNote(BuildContext context, int noteId) {
    // Navigate to note detail screen
    // Implementation depends on your routing setup
  }
}
```

#### 4. UI Example - Create Cross-Reference Dialog

```dart
class CreateCrossRefDialog extends ConsumerStatefulWidget {
  final int sourceNoteId;
  final List<Note> availableNotes;

  const CreateCrossRefDialog({
    required this.sourceNoteId,
    required this.availableNotes,
    super.key,
  });

  @override
  ConsumerState<CreateCrossRefDialog> createState() =>
      _CreateCrossRefDialogState();
}

class _CreateCrossRefDialogState extends ConsumerState<CreateCrossRefDialog> {
  int? selectedNoteId;
  String referenceType = 'related';
  final descriptionController = TextEditingController();

  final List<String> referenceTypes = [
    'related',
    'expands_on',
    'supports',
    'references',
    'contradicts',
    'follows',
    'precedes',
    'cited_by',
  ];

  @override
  void dispose() {
    descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Cross-Reference'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<int>(
              value: selectedNoteId,
              hint: const Text('Select target note'),
              items: widget.availableNotes
                  .where((note) => note.id != widget.sourceNoteId)
                  .map((note) => DropdownMenuItem(
                        value: note.id,
                        child: Text(
                          note.title,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  selectedNoteId = value;
                });
              },
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: referenceType,
              items: referenceTypes
                  .map((type) => DropdownMenuItem(
                        value: type,
                        child: Text(type.replaceAll('_', ' ').toUpperCase()),
                      ))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  referenceType = value!;
                });
              },
            ),
            const SizedBox(height: 16),
            TextField(
              controller: descriptionController,
              decoration: const InputDecoration(
                labelText: 'Description (optional)',
                hintText: 'Explain the relationship...',
              ),
              maxLines: 3,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: selectedNoteId == null ? null : _createCrossRef,
          child: const Text('Create'),
        ),
      ],
    );
  }

  Future<void> _createCrossRef() async {
    try {
      await ref.read(crossRefServiceProvider).createCrossRef(
            noteId: widget.sourceNoteId,
            otherNoteId: selectedNoteId!,
            referenceType: referenceType,
            description: descriptionController.text.isEmpty
                ? null
                : descriptionController.text,
          );

      if (mounted) {
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Cross-reference created')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
}
```

---

## Future Enhancements

### 1. AI-Powered Suggestions

**Implementation Plan:**
- Analyze note content using natural language processing
- Compare semantic similarity between notes using embeddings
- Suggest related notes based on:
  - Topic modeling (LDA, BERT)
  - Scripture reference overlap
  - Tag similarity
  - Preacher connections
  - Temporal proximity

**Endpoint:** `GET /cross-refs/suggestions/{note_id}`

**Technology Options:**
- OpenAI embeddings API
- Sentence transformers (open source)
- Custom fine-tuned models

**Response Example:**
```json
[
  {
    "other_note_id": 5,
    "other_note_title": "Faith and Works in James",
    "suggested_type": "supports",
    "confidence_score": 87,
    "reasoning": "Both notes discuss the relationship between faith and action, with similar scripture references"
  }
]
```

### 2. Knowledge Graph Visualization

**Frontend Implementation:**
- Use D3.js, Cytoscape.js, or vis.js for graph visualization
- Interactive nodes representing notes
- Edges colored by reference type
- Zoom and pan capabilities
- Click nodes to view note details

**Features:**
- Filter by reference type
- Highlight paths between notes
- Show clusters of related notes
- Time-based animation (show knowledge growth over time)

### 3. Bi-directional Reference Types

**Concept:**
- Some reference types have natural opposites:
  - `follows` ↔ `precedes`
  - `supports` ↔ `contradicts`
  - `expands_on` ↔ `summarizes`

**Implementation:**
- When creating certain reference types, automatically create inverse
- UI shows both perspectives
- Maintains single database entry to avoid duplication

### 4. Reference Strength/Weight

**Use Cases:**
- Rank related notes by strength of connection
- Weight graph edges for better visualization
- Prioritize suggestions

**Implementation:**
- Add `strength` field (0.0 - 1.0)
- Calculate based on:
  - Description length
  - Confidence score
  - Manual vs AI-generated
  - User interactions (clicks, edits)

### 5. Cross-Reference Categories

**Concept:**
- Group reference types into categories:
  - **Logical**: supports, contradicts, expands_on
  - **Sequential**: follows, precedes
  - **Citational**: references, cited_by
  - **General**: related

**Benefits:**
- Better filtering in UI
- Category-based visualization
- Simplified bulk operations

### 6. Auto-Reference Detection

**Implementation:**
- Scan note content for:
  - Mentions of other note titles
  - Shared scripture references
  - Similar tags
- Suggest creating cross-references automatically
- Require user confirmation before creating

### 7. Reference Templates

**Concept:**
- Save common reference patterns
- Example: "Sermon series" template creates `follows` references between all notes

**Use Cases:**
- Multi-part sermon series
- Topical studies
- Character studies through scripture

---

## Testing Checklist

### API Endpoint Tests

- [ ] Create cross-reference successfully
- [ ] Create cross-reference with all optional fields
- [ ] Bulk create multiple cross-references
- [ ] Prevent duplicate cross-references
- [ ] Prevent self-references
- [ ] Verify ownership validation (403 errors)
- [ ] Handle non-existent notes (404 errors)
- [ ] Get cross-reference by ID
- [ ] Get all cross-references for note (with pagination)
- [ ] Get outgoing references only
- [ ] Get incoming references only
- [ ] Get related notes with type filter
- [ ] Get cross-reference count statistics
- [ ] Update cross-reference metadata
- [ ] Delete cross-reference successfully
- [ ] Verify cascade delete when note is removed

### Business Logic Tests

- [ ] Cross-reference prevents referencing same note
- [ ] Bidirectional duplicate check works correctly
- [ ] User can only create refs between own notes
- [ ] Confidence score validation (0-100)
- [ ] Reference type validation
- [ ] Description field is optional
- [ ] Bulk create with skip_errors=true continues on error
- [ ] Bulk create with skip_errors=false fails on first error

### Integration Tests

- [ ] Create note, add cross-refs, delete note (verify cascade)
- [ ] Create multiple cross-refs, verify counts match
- [ ] Pagination works correctly with large datasets
- [ ] Related notes query returns correct results

---

## Troubleshooting

### Common Issues

**1. "Cross-reference between these notes already exists"**
- **Cause:** Bidirectional duplicate check
- **Solution:** Check if A → B or B → A already exists
- **Note:** This is intentional to prevent redundant relationships

**2. "You can only create cross-references between your own notes"**
- **Cause:** Target note belongs to different user
- **Solution:** Only create cross-refs between your own notes
- **Future:** Consider shared circle cross-references

**3. "Cannot create a cross-reference to the same note"**
- **Cause:** note_id equals other_note_id
- **Solution:** Select a different target note
- **Note:** Self-references don't provide value in knowledge graph

**4. Cascade delete removes all cross-refs**
- **Expected Behavior:** When deleting a note, all associated cross-refs are removed
- **Rationale:** Maintains referential integrity
- **Alternative:** Soft delete notes to preserve history

---

## API Testing with cURL

### Create Cross-Reference
```bash
curl -X POST http://localhost:8000/cross-refs/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "note_id": 1,
    "other_note_id": 2,
    "reference_type": "expands_on",
    "description": "Provides more detail on grace theology"
  }'
```

### Get Note Cross-References
```bash
curl -X GET "http://localhost:8000/cross-refs/note/1?skip=0&limit=100" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Related Notes
```bash
curl -X GET "http://localhost:8000/cross-refs/note/1/related?reference_types=related,expands_on" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Cross-Reference
```bash
curl -X PUT http://localhost:8000/cross-refs/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reference_type": "supports",
    "description": "Updated description"
  }'
```

### Delete Cross-Reference
```bash
curl -X DELETE http://localhost:8000/cross-refs/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Conclusion

The Cross-Reference feature provides a powerful way to build a knowledge graph of sermon notes, enabling users to:

- Connect related spiritual insights
- Track theological themes across sermons
- Build a network of scriptural understanding
- Navigate between related notes easily

The feature is built with scalability in mind, supporting future AI-powered suggestions and advanced visualization capabilities.

For questions or issues, refer to the troubleshooting section or check the API documentation at `/docs` when running the application.
