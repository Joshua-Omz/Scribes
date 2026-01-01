# Cross-References Engine Guide
**AI-Powered Semantic Linking Between Sermon Notes**

## 📋 Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [For Frontend Developers](#for-frontend-developers)
4. [For DevOps Engineers](#for-devops-engineers)
5. [For Cloud Engineers](#for-cloud-engineers)
6. [API Reference](#api-reference)
7. [Algorithms](#algorithms)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the Cross-References Engine?

The Cross-References Engine **automatically discovers and manages connections** between sermon notes using AI-powered semantic similarity.

**Key Features:**
- ✅ **Automatic suggestions:** AI finds related notes based on content similarity
- ✅ **Manual linking:** Users can create custom cross-references
- ✅ **Bidirectional references:** Navigate between related notes
- ✅ **Confidence scoring:** AI provides similarity scores (0-1)
- ✅ **Type classification:** "similar," "related," "contrast," or "custom"
- ✅ **Bulk operations:** Process multiple references at once

**Use Cases:**
- 📖 **Series linking:** Connect sermon series automatically
- 🔗 **Topic clustering:** Find notes on similar themes
- 🎯 **Scripture connections:** Link notes discussing same passages
- 💡 **Idea expansion:** Discover related insights from past sermons

---

## How It Works

### Auto-Suggestion Flow

```
┌──────────────────────────────────────────────────────────┐
│          User Views Note Details                          │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  GET /cross-refs/  │
         │  suggestions/{id}  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Load Note         │
         │  Get embedding     │
         │  (384-dim vector)  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Vector Similarity │
         │  Search (pgvector) │
         │  - Cosine distance │
         │  - Top 10 results  │
         │  - Min score: 0.7  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Filter Results    │
         │  - Exclude self    │
         │  - Exclude existing│
         │  - Same user only  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Return Suggestions│
         │  {title, preview,  │
         │   similarity: 0.89}│
         └────────────────────┘
```

### Manual Creation Flow

```
┌──────────────────────────────────────────────────────────┐
│         User Creates Cross-Reference                      │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  POST /cross-refs  │
         │  {note_id, other_  │
         │   note_id, type}   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Validate Request  │
         │  - Notes exist?    │
         │  - User owns both? │
         │  - Not same note?  │
         │  - Not duplicate?  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Create Reference  │
         │  - Save to DB      │
         │  - Set is_auto=false│
         │  - Calculate score │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Create Reciprocal │
         │  (optional)        │
         │  - Bidirectional   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Return Reference  │
         │  with details      │
         └────────────────────┘
```

### Similarity Calculation

**Cosine Similarity Formula:**
```
similarity = 1 - cosine_distance
           = embedding_a · embedding_b
             ─────────────────────────
             ||embedding_a|| × ||embedding_b||
```

**Example:**
```python
# Note A embedding: [0.5, 0.3, 0.8, ...]  (384 dims)
# Note B embedding: [0.6, 0.2, 0.7, ...]  (384 dims)

# Cosine similarity:
# - 1.0 = identical content
# - 0.7+ = very related
# - 0.5-0.7 = somewhat related
# - <0.5 = not related

# In database (using pgvector):
SELECT 
    id, 
    title,
    1 - (embedding <=> target_embedding) as similarity
FROM notes
WHERE 1 - (embedding <=> target_embedding) > 0.7
ORDER BY similarity DESC
LIMIT 10;
```

---

## For Frontend Developers (Flutter/Dart)

### 1. Get Suggestions for a Note

**Endpoint:** `GET /cross-refs/suggestions/{note_id}`

**Request:**
```dart
class CrossRefSuggestion {
  final int noteId;
  final String title;
  final String preview;
  final double similarityScore;
  final String? preacher;
  final String? tags;

  CrossRefSuggestion({
    required this.noteId,
    required this.title,
    required this.preview,
    required this.similarityScore,
    this.preacher,
    this.tags,
  });

  factory CrossRefSuggestion.fromJson(Map<String, dynamic> json) {
    return CrossRefSuggestion(
      noteId: json['note_id'],
      title: json['title'],
      preview: json['preview'],
      similarityScore: json['similarity_score'].toDouble(),
      preacher: json['preacher'],
      tags: json['tags'],
    );
  }
}

class CrossRefService {
  final Dio dio;

  CrossRefService(this.dio);

  Future<List<CrossRefSuggestion>> getSuggestions(
    int noteId, {
    int limit = 10,
    double minSimilarity = 0.7,
  }) async {
    final response = await dio.get(
      '/cross-refs/suggestions/$noteId',
      queryParameters: {
        'limit': limit,
        'min_similarity': minSimilarity,
      },
    );

    return (response.data as List)
        .map((item) => CrossRefSuggestion.fromJson(item))
        .toList();
  }
}
```

**Response (200 OK):**
```json
[
  {
    "note_id": 456,
    "title": "Grace and Mercy",
    "preview": "In this sermon, we explored the profound difference between grace (unmerited favor) and mercy...",
    "similarity_score": 0.89,
    "preacher": "John Smith",
    "tags": "grace,mercy,theology"
  },
  {
    "note_id": 789,
    "title": "Salvation by Faith",
    "preview": "Ephesians 2:8-9 clearly states that we are saved by grace through faith, not by works...",
    "similarity_score": 0.82,
    "preacher": "Jane Doe",
    "tags": "salvation,faith,grace"
  }
]
```

**Query Parameters:**
- `limit` (default=10, max=50): Number of suggestions
- `min_similarity` (default=0.7): Minimum similarity threshold

---

### 2. Create Cross-Reference

**Endpoint:** `POST /cross-refs`

**Request:**
```dart
class CrossRef {
  final int? id;
  final int noteId;
  final int otherNoteId;
  final String? referenceType;
  final String? description;
  final bool? isAutoGenerated;
  final double? confidenceScore;
  final DateTime? createdAt;
  final String? noteTitle;
  final String? otherNoteTitle;

  CrossRef({
    this.id,
    required this.noteId,
    required this.otherNoteId,
    this.referenceType,
    this.description,
    this.isAutoGenerated,
    this.confidenceScore,
    this.createdAt,
    this.noteTitle,
    this.otherNoteTitle,
  });

  factory CrossRef.fromJson(Map<String, dynamic> json) {
    return CrossRef(
      id: json['id'],
      noteId: json['note_id'],
      otherNoteId: json['other_note_id'],
      referenceType: json['reference_type'],
      description: json['description'],
      isAutoGenerated: json['is_auto_generated'],
      confidenceScore: json['confidence_score']?.toDouble(),
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : null,
      noteTitle: json['note_title'],
      otherNoteTitle: json['other_note_title'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'note_id': noteId,
      'other_note_id': otherNoteId,
      'reference_type': referenceType,
      'description': description,
    };
  }
}

Future<CrossRef> createCrossRef({
  required int noteId,
  required int otherNoteId,
  String referenceType = 'similar',
  String? description,
}) async {
  final response = await dio.post(
    '/cross-refs',
    data: {
      'note_id': noteId,
      'other_note_id': otherNoteId,
      'reference_type': referenceType,
      'description': description,
    },
  );

  return CrossRef.fromJson(response.data);
}
```

**Response (201 Created):**
```json
{
  "id": 78,
  "note_id": 123,
  "other_note_id": 456,
  "reference_type": "similar",
  "description": "Both discuss justification by faith",
  "is_auto_generated": false,
  "confidence_score": 0.89,
  "created_at": "2025-12-24T10:00:00Z",
  "note_title": "Faith and Works",
  "other_note_title": "Grace and Mercy"
}
```

---

### 3. Get All Cross-References for a Note

**Endpoint:** `GET /cross-refs/note/{note_id}`

**Request:**
```dart
Future<List<CrossRef>> getCrossRefs(int noteId) async {
  final response = await dio.get('/cross-refs/note/$noteId');

  return (response.data as List)
      .map((item) => CrossRef.fromJson(item))
      .toList();
}
```

---

### 4. Delete Cross-Reference

**Endpoint:** `DELETE /cross-refs/{cross_ref_id}`

**Request:**
```dart
Future<void> deleteCrossRef(int crossRefId) async {
  await dio.delete('/cross-refs/$crossRefId');
}
```

---

### 5. Bulk Create Cross-References

**Endpoint:** `POST /cross-refs/bulk`

**Request:**
```dart
Future<Map<String, dynamic>> bulkCreateCrossRefs({
  required int noteId,
  required List<Map<String, dynamic>> crossRefs,
}) async {
  final response = await dio.post(
    '/cross-refs/bulk',
    data: {
      'note_id': noteId,
      'cross_refs': crossRefs,
    },
  );

  return response.data;
}

// Usage
final result = await bulkCreateCrossRefs(
  noteId: 123,
  crossRefs: [
    {'other_note_id': 456, 'reference_type': 'similar'},
    {'other_note_id': 789, 'reference_type': 'related'},
    {'other_note_id': 101, 'reference_type': 'similar'},
  ],
);
```

---

### Flutter Widget Example

**cross_references_panel.dart:**
```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class CrossRefsProvider with ChangeNotifier {
  List<CrossRefSuggestion> _suggestions = [];
  List<CrossRef> _existing = [];
  bool _isLoading = false;

  List<CrossRefSuggestion> get suggestions => _suggestions;
  List<CrossRef> get existing => _existing;
  bool get isLoading => _isLoading;

  final CrossRefService _service;

  CrossRefsProvider(this._service);

  Future<void> fetchCrossRefs(int noteId) async {
    try {
      _existing = await _service.getCrossRefs(noteId);
      notifyListeners();
    } catch (e) {
      print('Failed to fetch cross-refs: $e');
    }
  }

  Future<void> fetchSuggestions(int noteId) async {
    _isLoading = true;
    notifyListeners();

    try {
      _suggestions = await _service.getSuggestions(noteId);
    } catch (e) {
      print('Failed to fetch suggestions: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> createCrossRef(int noteId, int otherNoteId) async {
    try {
      await _service.createCrossRef(
        noteId: noteId,
        otherNoteId: otherNoteId,
        referenceType: 'similar',
      );

      // Refresh both lists
      await fetchCrossRefs(noteId);
      await fetchSuggestions(noteId);
    } catch (e) {
      print('Failed to create cross-ref: $e');
      rethrow;
    }
  }

  Future<void> deleteCrossRef(int crossRefId, int noteId) async {
    try {
      await _service.deleteCrossRef(crossRefId);
      _existing.removeWhere((cr) => cr.id == crossRefId);
      notifyListeners();
    } catch (e) {
      print('Failed to delete cross-ref: $e');
      rethrow;
    }
  }
}

class CrossReferencesPanel extends StatefulWidget {
  final int noteId;

  const CrossReferencesPanel({required this.noteId});

  @override
  _CrossReferencesPanelState createState() => _CrossReferencesPanelState();
}

class _CrossReferencesPanelState extends State<CrossReferencesPanel> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<CrossRefsProvider>();
      provider.fetchCrossRefs(widget.noteId);
      provider.fetchSuggestions(widget.noteId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CrossRefsProvider>(
      builder: (context, provider, child) {
        return SingleChildScrollView(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Existing Cross-References Section
              _buildExistingSection(context, provider),
              SizedBox(height: 24),
              // AI Suggestions Section
              _buildSuggestionsSection(context, provider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildExistingSection(BuildContext context, CrossRefsProvider provider) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Linked Notes (${provider.existing.length})',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            SizedBox(height: 16),
            if (provider.existing.isEmpty)
              Text('No cross-references yet. Check suggestions below.')
            else
              ...provider.existing.map((crossRef) {
                return CrossRefCard(
                  crossRef: crossRef,
                  onDelete: () => _confirmDelete(context, provider, crossRef.id!),
                );
              }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildSuggestionsSection(BuildContext context, CrossRefsProvider provider) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Suggested Related Notes',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            SizedBox(height: 16),
            if (provider.isLoading)
              Center(child: CircularProgressIndicator())
            else if (provider.suggestions.isEmpty)
              Text('No suggestions found.')
            else
              ...provider.suggestions.map((suggestion) {
                return SuggestionCard(
                  suggestion: suggestion,
                  onAdd: () => _addCrossRef(context, provider, suggestion.noteId),
                );
              }).toList(),
          ],
        ),
      ),
    );
  }

  Future<void> _addCrossRef(
    BuildContext context,
    CrossRefsProvider provider,
    int otherNoteId,
  ) async {
    try {
      await provider.createCrossRef(widget.noteId, otherNoteId);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Cross-reference added')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to add cross-reference')),
      );
    }
  }

  Future<void> _confirmDelete(
    BuildContext context,
    CrossRefsProvider provider,
    int crossRefId,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Remove Cross-Reference'),
        content: Text('Are you sure you want to remove this link?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Remove'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await provider.deleteCrossRef(crossRefId, widget.noteId);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Cross-reference removed')),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to remove cross-reference')),
        );
      }
    }
  }
}

class CrossRefCard extends StatelessWidget {
  final CrossRef crossRef;
  final VoidCallback onDelete;

  const CrossRefCard({
    required this.crossRef,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final similarityPercent = ((crossRef.confidenceScore ?? 0) * 100).round();

    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    crossRef.otherNoteTitle ?? 'Untitled Note',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '$similarityPercent% similar',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: () {
                    // Navigate to note detail
                  },
                  icon: Icon(Icons.visibility),
                  label: Text('View Note'),
                ),
                TextButton.icon(
                  onPressed: onDelete,
                  icon: Icon(Icons.delete, color: Colors.red),
                  label: Text('Remove', style: TextStyle(color: Colors.red)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class SuggestionCard extends StatelessWidget {
  final CrossRefSuggestion suggestion;
  final VoidCallback onAdd;

  const SuggestionCard({
    required this.suggestion,
    required this.onAdd,
  });

  @override
  Widget build(BuildContext context) {
    final similarityPercent = (suggestion.similarityScore * 100).round();

    return Card(
      margin: EdgeInsets.only(bottom: 12),
      color: Colors.blue.shade50,
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    suggestion.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.blue,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '$similarityPercent% match',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text(
              suggestion.preview,
              style: TextStyle(color: Colors.grey.shade700),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                ElevatedButton.icon(
                  onPressed: onAdd,
                  icon: Icon(Icons.add),
                  label: Text('Add Link'),
                ),
                SizedBox(width: 8),
                TextButton.icon(
                  onPressed: () {
                    // Navigate to note detail
                  },
                  icon: Icon(Icons.visibility),
                  label: Text('View Note'),
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

---

## For DevOps Engineers

### Database Configuration

**Vector Similarity Index:**
```sql
-- Essential for fast similarity search
CREATE INDEX CONCURRENTLY idx_notes_embedding 
ON notes USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Tune HNSW parameters:
-- m = max connections per node (16 = good balance)
-- ef_construction = size of dynamic candidate list (64 = good quality)
```

**Cross-References Table:**
```sql
CREATE TABLE cross_refs (
    id SERIAL PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    other_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    reference_type VARCHAR(50) DEFAULT 'related',
    description TEXT,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT no_self_reference CHECK (note_id != other_note_id),
    CONSTRAINT unique_cross_ref UNIQUE (note_id, other_note_id)
);

-- Indexes for fast lookup
CREATE INDEX idx_cross_refs_note_id ON cross_refs(note_id);
CREATE INDEX idx_cross_refs_other_note_id ON cross_refs(other_note_id);
CREATE INDEX idx_cross_refs_confidence ON cross_refs(confidence_score DESC);
```

---

### Monitoring

**Query Performance:**
```sql
-- Monitor similarity search performance
EXPLAIN ANALYZE
SELECT 
    id, 
    title,
    1 - (embedding <=> '[0.1,0.2,...]'::vector) as similarity
FROM notes
WHERE user_id = 1
  AND id != 123
  AND 1 - (embedding <=> '[0.1,0.2,...]'::vector) > 0.7
ORDER BY similarity DESC
LIMIT 10;

-- Should use index scan, not sequential scan
-- Target: < 100ms for 10,000 notes
```

**Cross-Reference Statistics:**
```sql
-- Count auto vs manual references
SELECT 
    is_auto_generated,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM cross_refs
GROUP BY is_auto_generated;

-- Most referenced notes
SELECT 
    n.id,
    n.title,
    COUNT(cr.id) as ref_count
FROM notes n
JOIN cross_refs cr ON (cr.note_id = n.id OR cr.other_note_id = n.id)
GROUP BY n.id, n.title
ORDER BY ref_count DESC
LIMIT 10;

-- Average references per note
SELECT 
    AVG(ref_count) as avg_refs_per_note
FROM (
    SELECT note_id, COUNT(*) as ref_count
    FROM cross_refs
    GROUP BY note_id
) subquery;
```

---

### Background Jobs

**Batch Auto-Linking:**
```python
# scripts/admin/auto_link_all_notes.py
"""
Batch process to create auto-generated cross-references
for all notes that don't have them yet.
"""

from app.services.business.cross_ref_service import CrossRefService
from app.core.database import get_db

async def auto_link_all_notes():
    async for db in get_db():
        cross_ref_service = CrossRefService(db)
        
        # Get all notes
        notes = await db.query(Note).all()
        
        for note in notes:
            print(f"Processing note {note.id}...")
            
            # Get suggestions
            suggestions = await cross_ref_service.get_suggestions(
                note.id,
                user_id=note.user_id,
                limit=5,
                min_similarity=0.75
            )
            
            # Create auto-references
            for suggestion in suggestions:
                await cross_ref_service.create_cross_ref(
                    note_id=note.id,
                    other_note_id=suggestion['note_id'],
                    is_auto=True,
                    confidence_score=suggestion['similarity_score']
                )
            
            await db.commit()
            print(f"  Created {len(suggestions)} auto-references")

# Run: python scripts/admin/auto_link_all_notes.py
```

---

### Docker Configuration

**docker-compose.yml:**
```yaml
services:
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
      -c random_page_cost=1.1  # Lower for SSD
```

---

## For Cloud Engineers

### AWS Aurora PostgreSQL

**Enable pgvector:**
```bash
# Create Aurora PostgreSQL cluster
aws rds create-db-cluster \
  --db-cluster-identifier scribes-cluster \
  --engine aurora-postgresql \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password <password>

# Connect and enable extension
psql -h <aurora-endpoint> -U admin -d scribes
> CREATE EXTENSION vector;

# Create indexes
> CREATE INDEX idx_notes_embedding 
  ON notes USING hnsw (embedding vector_cosine_ops);
```

**Parameter Group:**
```bash
# Create custom parameter group
aws rds create-db-cluster-parameter-group \
  --db-cluster-parameter-group-name scribes-params \
  --db-parameter-group-family aurora-postgresql15 \
  --description "Optimized for vector operations"

# Modify parameters
aws rds modify-db-cluster-parameter-group \
  --db-cluster-parameter-group-name scribes-params \
  --parameters \
    "ParameterName=shared_buffers,ParameterValue='{DBInstanceClassMemory/4}',ApplyMethod=pending-reboot" \
    "ParameterName=effective_cache_size,ParameterValue='{DBInstanceClassMemory/2}',ApplyMethod=immediate"
```

---

### GCP Cloud SQL

**Create Instance:**
```bash
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create scribes-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-4-15360 \
  --region=us-central1 \
  --database-flags=shared_buffers=2GB,effective_cache_size=8GB

# Enable pgvector
gcloud sql connect scribes-db --user=postgres
> CREATE EXTENSION vector;
```

---

### Azure Database for PostgreSQL

**Create Server:**
```bash
# Create flexible server
az postgres flexible-server create \
  --name scribes-db \
  --resource-group scribes-rg \
  --location eastus \
  --admin-user admin \
  --admin-password <password> \
  --sku-name Standard_D4s_v3 \
  --version 15

# Enable pgvector
az postgres flexible-server execute \
  --name scribes-db \
  --admin-user admin \
  --admin-password <password> \
  --querytext "CREATE EXTENSION vector;"

# Configure server parameters
az postgres flexible-server parameter set \
  --resource-group scribes-rg \
  --server-name scribes-db \
  --name shared_buffers \
  --value 2048MB
```

---

## API Reference

### GET /cross-refs/suggestions/{note_id}
Get AI-powered suggestions for related notes.

**Path Parameters:**
- `note_id` (integer): Source note ID

**Query Parameters:**
- `limit` (integer, default=10, max=50): Number of suggestions
- `min_similarity` (float, default=0.7, range=0-1): Minimum similarity threshold

**Responses:**
- `200 OK`: List of suggestions
- `404 Not Found`: Note doesn't exist
- `401 Unauthorized`: Not authenticated

---

### POST /cross-refs
Create a cross-reference.

**Request Body:**
```json
{
  "note_id": 123,
  "other_note_id": 456,
  "reference_type": "similar",
  "description": "Optional description"
}
```

**Responses:**
- `201 Created`: Cross-reference created
- `400 Bad Request`: Validation error (same note, duplicate, etc.)
- `404 Not Found`: One or both notes don't exist
- `401 Unauthorized`: Not authenticated

---

### GET /cross-refs/note/{note_id}
Get all cross-references for a note.

**Path Parameters:**
- `note_id` (integer): Note ID

**Responses:**
- `200 OK`: List of cross-references with details
- `404 Not Found`: Note doesn't exist
- `401 Unauthorized`: Not authenticated

---

### DELETE /cross-refs/{cross_ref_id}
Delete a cross-reference.

**Path Parameters:**
- `cross_ref_id` (integer): Cross-reference ID

**Responses:**
- `200 OK`: Deletion confirmed
- `404 Not Found`: Cross-reference doesn't exist
- `401 Unauthorized`: Not authenticated

---

### POST /cross-refs/bulk
Create multiple cross-references at once.

**Request Body:**
```json
{
  "note_id": 123,
  "cross_refs": [
    {"other_note_id": 456, "reference_type": "similar"},
    {"other_note_id": 789, "reference_type": "related"}
  ]
}
```

**Responses:**
- `200 OK`: Returns count of created references
- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Not authenticated

---

## Algorithms

### Similarity Threshold Calibration

**Recommended Thresholds:**
```python
SIMILARITY_THRESHOLDS = {
    'highly_related': 0.85,    # Very similar content
    'related': 0.70,           # Clearly related
    'somewhat_related': 0.55,  # Possibly related
    'unrelated': 0.50          # Likely not related
}
```

**Empirical Testing:**
```python
# Test different thresholds
thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

for threshold in thresholds:
    suggestions = get_suggestions(note_id=123, min_similarity=threshold)
    print(f"Threshold {threshold}: {len(suggestions)} suggestions")
    
    # Manually review and rate relevance
    # Adjust threshold based on precision/recall balance
```

---

### HNSW Index Tuning

**Parameters Explained:**
- **m (max connections):** More connections = better recall, slower index build
  - Default: 16
  - Low memory: 8
  - High accuracy: 32

- **ef_construction:** Larger = better index quality, slower build
  - Default: 64
  - Fast build: 32
  - High accuracy: 128

- **ef_search:** Larger = better search recall, slower queries
  - Set at query time via `SET hnsw.ef_search = 100;`

**Benchmark:**
```sql
-- Test search performance
SET hnsw.ef_search = 40;   -- Default
EXPLAIN ANALYZE SELECT ... ORDER BY embedding <=> target LIMIT 10;
-- Time: 50ms, Recall: 90%

SET hnsw.ef_search = 100;  -- Higher accuracy
EXPLAIN ANALYZE SELECT ... ORDER BY embedding <=> target LIMIT 10;
-- Time: 120ms, Recall: 98%

SET hnsw.ef_search = 200;  -- Maximum accuracy
EXPLAIN ANALYZE SELECT ... ORDER BY embedding <=> target LIMIT 10;
-- Time: 250ms, Recall: 99.5%
```

---

## Troubleshooting

### Issue: "No suggestions returned"

**Symptoms:**
- GET /cross-refs/suggestions returns empty array
- Notes exist and have embeddings

**Solutions:**
1. Check embedding exists:
   ```sql
   SELECT id, title, embedding IS NOT NULL as has_embedding
   FROM notes
   WHERE id = 123;
   ```

2. Lower similarity threshold:
   ```typescript
   // Try lower threshold
   const response = await api.get(
     `/cross-refs/suggestions/123?min_similarity=0.5`
   );
   ```

3. Check index:
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename = 'notes' AND indexdef LIKE '%embedding%';
   ```

4. Rebuild index:
   ```sql
   DROP INDEX idx_notes_embedding;
   CREATE INDEX idx_notes_embedding 
   ON notes USING hnsw (embedding vector_cosine_ops);
   ```

---

### Issue: "Slow similarity search"

**Symptoms:**
- Suggestions endpoint takes > 1 second
- High database CPU during search

**Solutions:**
1. Check if index is being used:
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM notes
   WHERE 1 - (embedding <=> '[...]'::vector) > 0.7
   ORDER BY embedding <=> '[...]'::vector
   LIMIT 10;
   
   -- Should show "Index Scan using idx_notes_embedding"
   -- NOT "Seq Scan on notes"
   ```

2. Tune ef_search:
   ```sql
   -- Lower ef_search for faster queries (slightly less accurate)
   SET hnsw.ef_search = 40;
   ```

3. Reduce result limit:
   ```typescript
   // Request fewer suggestions
   const response = await api.get(
     `/cross-refs/suggestions/123?limit=5`
   );
   ```

---

### Issue: "Duplicate cross-reference error"

**Symptoms:**
- 400 Bad Request: "Cross-reference already exists"

**Solutions:**
1. Check existing references:
   ```sql
   SELECT * FROM cross_refs
   WHERE (note_id = 123 AND other_note_id = 456)
      OR (note_id = 456 AND other_note_id = 123);
   ```

2. Delete duplicate before recreating:
   ```typescript
   await api.delete(`/cross-refs/${existingId}`);
   await api.post('/cross-refs', { ... });
   ```

---

## Performance Metrics

### Target Response Times
- **Get Suggestions:** < 200ms (with index)
- **Create Cross-Ref:** < 100ms
- **Get Cross-Refs for Note:** < 50ms
- **Delete Cross-Ref:** < 50ms

### Accuracy Metrics
- **Recall @10 (threshold=0.7):** > 85%
- **Precision @10 (threshold=0.7):** > 75%
- **False Positive Rate:** < 10%

### Scale Estimates
- **10,000 notes:** ~200ms search time
- **100,000 notes:** ~500ms search time
- **1,000,000 notes:** ~1000ms search time

---

## Summary

### Key Points
✅ **AI-powered suggestions** using semantic embeddings  
✅ **pgvector HNSW index** for fast similarity search  
✅ **Manual and automatic** cross-reference creation  
✅ **Bidirectional linking** between notes  
✅ **Confidence scoring** (0-1) for relevance  
✅ **Production-ready** with monitoring and optimization  

### Quick Commands
```bash
# Get suggestions
curl http://localhost:8000/cross-refs/suggestions/123 \
  -H "Authorization: Bearer $TOKEN"

# Create cross-reference
curl -X POST http://localhost:8000/cross-refs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note_id":123,"other_note_id":456,"reference_type":"similar"}'

# Check index performance
psql -c "EXPLAIN ANALYZE SELECT * FROM notes ORDER BY embedding <=> '[...]'::vector LIMIT 10;"
```

---

**Document Version:** 1.0  
**Last Updated:** December 24, 2025  
**Related Docs:** [Notes Management Guide](./NOTES_MANAGEMENT_GUIDE.md) | [AI Assistant Guide](./AI_ASSISTANT_GUIDE.md)
