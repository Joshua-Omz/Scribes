# Flutter Notes Feature Implementation Guide

## Overview

This guide provides a complete implementation of the Notes feature for your Flutter app, integrating with the Scribes backend API. The Notes feature allows users to create, read, update, delete, and search sermon notes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Data Models](#data-models)
4. [API Service](#api-service)
5. [Repository Layer](#repository-layer)
6. [State Management](#state-management)
7. [UI Screens](#ui-screens)
8. [Complete Code Examples](#complete-code-examples)

---

## Prerequisites

Ensure you have the following packages in your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP Client
  dio: ^5.4.0
  
  # State Management
  flutter_riverpod: ^2.4.9
  
  # Secure Storage
  flutter_secure_storage: ^9.0.0
  
  # Local Storage
  shared_preferences: ^2.2.2
  
  # JSON Serialization
  json_annotation: ^4.8.1
  
  # Date Formatting
  intl: ^0.18.1
  
  # UI Components
  flutter_slidable: ^3.0.1

dev_dependencies:
  # Code Generation
  build_runner: ^2.4.7
  json_serializable: ^6.7.1
```

---

## Project Structure

```
lib/
├── models/
│   ├── note.dart
│   └── note.g.dart (generated)
├── services/
│   ├── api_client.dart
│   └── notes_api_service.dart
├── repositories/
│   └── notes_repository.dart
├── providers/
│   └── notes_provider.dart
├── screens/
│   ├── notes_list_screen.dart
│   ├── note_detail_screen.dart
│   ├── note_create_screen.dart
│   └── note_edit_screen.dart
└── widgets/
    ├── note_card.dart
    └── note_search_delegate.dart
```

---

## Data Models

### 1. Note Model (`lib/models/note.dart`)

```dart
import 'package:json_annotation/json_annotation.dart';

part 'note.g.dart';

@JsonSerializable()
class Note {
  final int id;
  @JsonKey(name: 'user_id')
  final int userId;
  final String title;
  final String content;
  final String? preacher;
  final List<String>? tags;
  @JsonKey(name: 'scripture_refs')
  final String? scriptureRefs;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Note({
    required this.id,
    required this.userId,
    required this.title,
    required this.content,
    this.preacher,
    this.tags,
    this.scriptureRefs,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Note.fromJson(Map<String, dynamic> json) => _$NoteFromJson(json);
  Map<String, dynamic> toJson() => _$NoteToJson(this);

  Note copyWith({
    int? id,
    int? userId,
    String? title,
    String? content,
    String? preacher,
    List<String>? tags,
    String? scriptureRefs,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Note(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      title: title ?? this.title,
      content: content ?? this.content,
      preacher: preacher ?? this.preacher,
      tags: tags ?? this.tags,
      scriptureRefs: scriptureRefs ?? this.scriptureRefs,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

@JsonSerializable()
class NoteCreate {
  final String title;
  final String content;
  final String? preacher;
  final List<String>? tags;
  @JsonKey(name: 'scripture_refs')
  final String? scriptureRefs;

  NoteCreate({
    required this.title,
    required this.content,
    this.preacher,
    this.tags,
    this.scriptureRefs,
  });

  factory NoteCreate.fromJson(Map<String, dynamic> json) => 
      _$NoteCreateFromJson(json);
  Map<String, dynamic> toJson() => _$NoteCreateToJson(this);
}

@JsonSerializable()
class NoteUpdate {
  final String? title;
  final String? content;
  final String? preacher;
  final List<String>? tags;
  @JsonKey(name: 'scripture_refs')
  final String? scriptureRefs;

  NoteUpdate({
    this.title,
    this.content,
    this.preacher,
    this.tags,
    this.scriptureRefs,
  });

  factory NoteUpdate.fromJson(Map<String, dynamic> json) => 
      _$NoteUpdateFromJson(json);
  Map<String, dynamic> toJson() => _$NoteUpdateToJson(this);
}

@JsonSerializable()
class NotesListResponse {
  final List<Note> notes;
  final int total;
  final int skip;
  final int limit;

  NotesListResponse({
    required this.notes,
    required this.total,
    required this.skip,
    required this.limit,
  });

  factory NotesListResponse.fromJson(Map<String, dynamic> json) => 
      _$NotesListResponseFromJson(json);
  Map<String, dynamic> toJson() => _$NotesListResponseToJson(this);
}
```

After creating the model, run:
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

---

## API Service

### 1. Notes API Service (`lib/services/notes_api_service.dart`)

```dart
import 'package:dio/dio.dart';
import '../models/note.dart';

class NotesApiService {
  final Dio _dio;

  NotesApiService(this._dio);

  /// Create a new note
  Future<Note> createNote(NoteCreate noteData) async {
    try {
      final response = await _dio.post(
        '/notes/',
        data: noteData.toJson(),
      );
      return Note.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get all notes with pagination
  Future<NotesListResponse> getNotes({
    int skip = 0,
    int limit = 20,
  }) async {
    try {
      final response = await _dio.get(
        '/notes/',
        queryParameters: {
          'skip': skip,
          'limit': limit,
        },
      );
      return NotesListResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get a specific note by ID
  Future<Note> getNoteById(int noteId) async {
    try {
      final response = await _dio.get('/notes/$noteId');
      return Note.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Update an existing note
  Future<Note> updateNote(int noteId, NoteUpdate noteData) async {
    try {
      final response = await _dio.put(
        '/notes/$noteId',
        data: noteData.toJson(),
      );
      return Note.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Delete a note
  Future<void> deleteNote(int noteId) async {
    try {
      await _dio.delete('/notes/$noteId');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Search notes by query, preacher, or tags
  Future<NotesListResponse> searchNotes({
    String? query,
    String? preacher,
    List<String>? tags,
    int skip = 0,
    int limit = 20,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'skip': skip,
        'limit': limit,
      };

      if (query != null && query.isNotEmpty) {
        queryParams['query'] = query;
      }
      if (preacher != null && preacher.isNotEmpty) {
        queryParams['preacher'] = preacher;
      }
      if (tags != null && tags.isNotEmpty) {
        queryParams['tags'] = tags.join(',');
      }

      final response = await _dio.get(
        '/notes/search',
        queryParameters: queryParams,
      );
      return NotesListResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException e) {
    if (e.response != null) {
      final data = e.response!.data;
      if (data is Map && data.containsKey('detail')) {
        return data['detail'].toString();
      }
      return 'Server error: ${e.response!.statusCode}';
    }
    return 'Network error: ${e.message}';
  }
}
```

---

## Repository Layer

### 1. Notes Repository (`lib/repositories/notes_repository.dart`)

```dart
import '../models/note.dart';
import '../services/notes_api_service.dart';

class NotesRepository {
  final NotesApiService _apiService;

  NotesRepository(this._apiService);

  Future<Note> createNote(NoteCreate noteData) async {
    return await _apiService.createNote(noteData);
  }

  Future<NotesListResponse> getNotes({
    int skip = 0,
    int limit = 20,
  }) async {
    return await _apiService.getNotes(skip: skip, limit: limit);
  }

  Future<Note> getNoteById(int noteId) async {
    return await _apiService.getNoteById(noteId);
  }

  Future<Note> updateNote(int noteId, NoteUpdate noteData) async {
    return await _apiService.updateNote(noteId, noteData);
  }

  Future<void> deleteNote(int noteId) async {
    await _apiService.deleteNote(noteId);
  }

  Future<NotesListResponse> searchNotes({
    String? query,
    String? preacher,
    List<String>? tags,
    int skip = 0,
    int limit = 20,
  }) async {
    return await _apiService.searchNotes(
      query: query,
      preacher: preacher,
      tags: tags,
      skip: skip,
      limit: limit,
    );
  }
}
```

---

## State Management

### 1. Notes Provider (`lib/providers/notes_provider.dart`)

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/note.dart';
import '../repositories/notes_repository.dart';
import '../services/api_client.dart';
import '../services/notes_api_service.dart';

// Provider for NotesRepository
final notesRepositoryProvider = Provider<NotesRepository>((ref) {
  final dio = ref.watch(apiClientProvider);
  final apiService = NotesApiService(dio);
  return NotesRepository(apiService);
});

// State for notes list
class NotesState {
  final List<Note> notes;
  final bool isLoading;
  final String? error;
  final int total;
  final bool hasMore;

  NotesState({
    this.notes = const [],
    this.isLoading = false,
    this.error,
    this.total = 0,
    this.hasMore = true,
  });

  NotesState copyWith({
    List<Note>? notes,
    bool? isLoading,
    String? error,
    int? total,
    bool? hasMore,
  }) {
    return NotesState(
      notes: notes ?? this.notes,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      total: total ?? this.total,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}

// Notes Notifier
class NotesNotifier extends StateNotifier<NotesState> {
  final NotesRepository _repository;
  static const int _pageSize = 20;

  NotesNotifier(this._repository) : super(NotesState());

  Future<void> loadNotes({bool refresh = false}) async {
    if (state.isLoading) return;

    if (refresh) {
      state = NotesState(isLoading: true);
    } else {
      state = state.copyWith(isLoading: true, error: null);
    }

    try {
      final response = await _repository.getNotes(
        skip: refresh ? 0 : state.notes.length,
        limit: _pageSize,
      );

      final newNotes = refresh ? response.notes : [...state.notes, ...response.notes];

      state = NotesState(
        notes: newNotes,
        isLoading: false,
        total: response.total,
        hasMore: newNotes.length < response.total,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<Note?> createNote(NoteCreate noteData) async {
    try {
      final note = await _repository.createNote(noteData);
      state = state.copyWith(
        notes: [note, ...state.notes],
        total: state.total + 1,
      );
      return note;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return null;
    }
  }

  Future<Note?> updateNote(int noteId, NoteUpdate noteData) async {
    try {
      final updatedNote = await _repository.updateNote(noteId, noteData);
      final index = state.notes.indexWhere((n) => n.id == noteId);
      if (index != -1) {
        final newNotes = [...state.notes];
        newNotes[index] = updatedNote;
        state = state.copyWith(notes: newNotes);
      }
      return updatedNote;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return null;
    }
  }

  Future<bool> deleteNote(int noteId) async {
    try {
      await _repository.deleteNote(noteId);
      state = state.copyWith(
        notes: state.notes.where((n) => n.id != noteId).toList(),
        total: state.total - 1,
      );
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  Future<List<Note>> searchNotes({
    String? query,
    String? preacher,
    List<String>? tags,
  }) async {
    try {
      final response = await _repository.searchNotes(
        query: query,
        preacher: preacher,
        tags: tags,
        limit: 50,
      );
      return response.notes;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return [];
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

// Provider for NotesNotifier
final notesProvider = StateNotifierProvider<NotesNotifier, NotesState>((ref) {
  final repository = ref.watch(notesRepositoryProvider);
  return NotesNotifier(repository);
});

// Provider for a single note
final noteProvider = FutureProvider.family<Note, int>((ref, noteId) async {
  final repository = ref.watch(notesRepositoryProvider);
  return await repository.getNoteById(noteId);
});
```

---

## UI Screens

### 1. Notes List Screen (`lib/screens/notes_list_screen.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/notes_provider.dart';
import '../widgets/note_card.dart';
import '../widgets/note_search_delegate.dart';
import 'note_create_screen.dart';
import 'note_detail_screen.dart';

class NotesListScreen extends ConsumerStatefulWidget {
  const NotesListScreen({super.key});

  @override
  ConsumerState<NotesListScreen> createState() => _NotesListScreenState();
}

class _NotesListScreenState extends ConsumerState<NotesListScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // Load notes when screen is first created
    Future.microtask(() => ref.read(notesProvider.notifier).loadNotes(refresh: true));
    
    // Setup infinite scroll
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent * 0.9) {
      final state = ref.read(notesProvider);
      if (!state.isLoading && state.hasMore) {
        ref.read(notesProvider.notifier).loadNotes();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final notesState = ref.watch(notesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Sermon Notes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              showSearch(
                context: context,
                delegate: NoteSearchDelegate(ref),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(notesProvider.notifier).loadNotes(refresh: true);
            },
          ),
        ],
      ),
      body: _buildBody(notesState),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const NoteCreateScreen(),
            ),
          );
          if (result == true) {
            ref.read(notesProvider.notifier).loadNotes(refresh: true);
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody(NotesState state) {
    if (state.isLoading && state.notes.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.notes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'Error: ${state.error}',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.red),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                ref.read(notesProvider.notifier).loadNotes(refresh: true);
              },
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (state.notes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.note_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'No notes yet',
              style: TextStyle(fontSize: 18, color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              'Tap + to create your first note',
              style: TextStyle(color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(notesProvider.notifier).loadNotes(refresh: true),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(8),
        itemCount: state.notes.length + (state.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == state.notes.length) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final note = state.notes[index];
          return NoteCard(
            note: note,
            onTap: () async {
              await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => NoteDetailScreen(noteId: note.id),
                ),
              );
              ref.read(notesProvider.notifier).loadNotes(refresh: true);
            },
          );
        },
      ),
    );
  }
}
```

### 2. Note Detail Screen (`lib/screens/note_detail_screen.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../models/note.dart';
import '../providers/notes_provider.dart';
import 'note_edit_screen.dart';

class NoteDetailScreen extends ConsumerWidget {
  final int noteId;

  const NoteDetailScreen({super.key, required this.noteId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final noteAsync = ref.watch(noteProvider(noteId));

    return noteAsync.when(
      data: (note) => _buildDetailScreen(context, ref, note),
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('Loading...')),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (error, stack) => Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(noteProvider(noteId)),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailScreen(BuildContext context, WidgetRef ref, Note note) {
    final dateFormat = DateFormat('MMM d, yyyy \'at\' h:mm a');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Note Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () async {
              final result = await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => NoteEditScreen(note: note),
                ),
              );
              if (result == true) {
                ref.refresh(noteProvider(noteId));
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () => _showDeleteDialog(context, ref, note),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title
            Text(
              note.title,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),

            // Preacher
            if (note.preacher != null) ...[
              Row(
                children: [
                  const Icon(Icons.person, size: 16, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    note.preacher!,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[700],
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],

            // Scripture References
            if (note.scriptureRefs != null && note.scriptureRefs!.isNotEmpty) ...[
              Row(
                children: [
                  const Icon(Icons.menu_book, size: 16, color: Colors.grey),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      note.scriptureRefs!,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[700],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],

            // Tags
            if (note.tags != null && note.tags!.isNotEmpty) ...[
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: note.tags!.map((tag) {
                  return Chip(
                    label: Text(tag),
                    backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
            ],

            // Created/Updated timestamps
            Text(
              'Created: ${dateFormat.format(note.createdAt)}',
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
            if (note.updatedAt != note.createdAt)
              Text(
                'Updated: ${dateFormat.format(note.updatedAt)}',
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
            const Divider(height: 32),

            // Content
            Text(
              note.content,
              style: const TextStyle(fontSize: 16, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }

  void _showDeleteDialog(BuildContext context, WidgetRef ref, Note note) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Note'),
        content: Text('Are you sure you want to delete "${note.title}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context); // Close dialog
              final success = await ref.read(notesProvider.notifier).deleteNote(note.id);
              if (context.mounted) {
                if (success) {
                  Navigator.pop(context); // Go back to list
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Note deleted successfully')),
                  );
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Failed to delete note')),
                  );
                }
              }
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
```

### 3. Note Create Screen (`lib/screens/note_create_screen.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/note.dart';
import '../providers/notes_provider.dart';

class NoteCreateScreen extends ConsumerStatefulWidget {
  const NoteCreateScreen({super.key});

  @override
  ConsumerState<NoteCreateScreen> createState() => _NoteCreateScreenState();
}

class _NoteCreateScreenState extends ConsumerState<NoteCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _preacherController = TextEditingController();
  final _scriptureRefsController = TextEditingController();
  final _tagController = TextEditingController();
  final List<String> _tags = [];
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _preacherController.dispose();
    _scriptureRefsController.dispose();
    _tagController.dispose();
    super.dispose();
  }

  Future<void> _createNote() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final noteData = NoteCreate(
      title: _titleController.text.trim(),
      content: _contentController.text.trim(),
      preacher: _preacherController.text.trim().isEmpty
          ? null
          : _preacherController.text.trim(),
      scriptureRefs: _scriptureRefsController.text.trim().isEmpty
          ? null
          : _scriptureRefsController.text.trim(),
      tags: _tags.isEmpty ? null : _tags,
    );

    final note = await ref.read(notesProvider.notifier).createNote(noteData);

    if (mounted) {
      setState(() => _isLoading = false);
      
      if (note != null) {
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Note created successfully')),
        );
      } else {
        final error = ref.read(notesProvider).error;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${error ?? "Unknown error"}')),
        );
      }
    }
  }

  void _addTag() {
    final tag = _tagController.text.trim();
    if (tag.isNotEmpty && !_tags.contains(tag)) {
      setState(() {
        _tags.add(tag);
        _tagController.clear();
      });
    }
  }

  void _removeTag(String tag) {
    setState(() => _tags.remove(tag));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Note'),
        actions: [
          if (_isLoading)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: CircularProgressIndicator(color: Colors.white),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.check),
              onPressed: _createNote,
            ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Title field
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Title *',
                hintText: 'Enter note title',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Title is required';
                }
                return null;
              },
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),

            // Preacher field
            TextFormField(
              controller: _preacherController,
              decoration: const InputDecoration(
                labelText: 'Preacher',
                hintText: 'Enter preacher name',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.person),
              ),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),

            // Scripture References field
            TextFormField(
              controller: _scriptureRefsController,
              decoration: const InputDecoration(
                labelText: 'Scripture References',
                hintText: 'e.g., John 3:16, Romans 8:28',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.menu_book),
              ),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),

            // Tags section
            TextFormField(
              controller: _tagController,
              decoration: InputDecoration(
                labelText: 'Tags',
                hintText: 'Add a tag',
                border: const OutlineInputBorder(),
                prefixIcon: const Icon(Icons.label),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: _addTag,
                ),
              ),
              onFieldSubmitted: (_) => _addTag(),
            ),
            if (_tags.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _tags.map((tag) {
                  return Chip(
                    label: Text(tag),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () => _removeTag(tag),
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 16),

            // Content field
            TextFormField(
              controller: _contentController,
              decoration: const InputDecoration(
                labelText: 'Content *',
                hintText: 'Enter your notes here...',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Content is required';
                }
                return null;
              },
              maxLines: 12,
              textInputAction: TextInputAction.newline,
            ),
            const SizedBox(height: 24),

            // Create button
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _createNote,
              icon: const Icon(Icons.add),
              label: const Text('Create Note'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 4. Note Edit Screen (`lib/screens/note_edit_screen.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/note.dart';
import '../providers/notes_provider.dart';

class NoteEditScreen extends ConsumerStatefulWidget {
  final Note note;

  const NoteEditScreen({super.key, required this.note});

  @override
  ConsumerState<NoteEditScreen> createState() => _NoteEditScreenState();
}

class _NoteEditScreenState extends ConsumerState<NoteEditScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _contentController;
  late TextEditingController _preacherController;
  late TextEditingController _scriptureRefsController;
  final _tagController = TextEditingController();
  late List<String> _tags;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.note.title);
    _contentController = TextEditingController(text: widget.note.content);
    _preacherController = TextEditingController(text: widget.note.preacher ?? '');
    _scriptureRefsController = TextEditingController(text: widget.note.scriptureRefs ?? '');
    _tags = List.from(widget.note.tags ?? []);
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _preacherController.dispose();
    _scriptureRefsController.dispose();
    _tagController.dispose();
    super.dispose();
  }

  Future<void> _updateNote() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final noteData = NoteUpdate(
      title: _titleController.text.trim(),
      content: _contentController.text.trim(),
      preacher: _preacherController.text.trim().isEmpty
          ? null
          : _preacherController.text.trim(),
      scriptureRefs: _scriptureRefsController.text.trim().isEmpty
          ? null
          : _scriptureRefsController.text.trim(),
      tags: _tags.isEmpty ? null : _tags,
    );

    final updatedNote = await ref.read(notesProvider.notifier).updateNote(
      widget.note.id,
      noteData,
    );

    if (mounted) {
      setState(() => _isLoading = false);
      
      if (updatedNote != null) {
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Note updated successfully')),
        );
      } else {
        final error = ref.read(notesProvider).error;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${error ?? "Unknown error"}')),
        );
      }
    }
  }

  void _addTag() {
    final tag = _tagController.text.trim();
    if (tag.isNotEmpty && !_tags.contains(tag)) {
      setState(() {
        _tags.add(tag);
        _tagController.clear();
      });
    }
  }

  void _removeTag(String tag) {
    setState(() => _tags.remove(tag));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Note'),
        actions: [
          if (_isLoading)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: CircularProgressIndicator(color: Colors.white),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.check),
              onPressed: _updateNote,
            ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Title field
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Title *',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Title is required';
                }
                return null;
              },
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),

            // Preacher field
            TextFormField(
              controller: _preacherController,
              decoration: const InputDecoration(
                labelText: 'Preacher',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.person),
              ),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),

            // Scripture References field
            TextFormField(
              controller: _scriptureRefsController,
              decoration: const InputDecoration(
                labelText: 'Scripture References',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.menu_book),
              ),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),

            // Tags section
            TextFormField(
              controller: _tagController,
              decoration: InputDecoration(
                labelText: 'Tags',
                hintText: 'Add a tag',
                border: const OutlineInputBorder(),
                prefixIcon: const Icon(Icons.label),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: _addTag,
                ),
              ),
              onFieldSubmitted: (_) => _addTag(),
            ),
            if (_tags.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _tags.map((tag) {
                  return Chip(
                    label: Text(tag),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () => _removeTag(tag),
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 16),

            // Content field
            TextFormField(
              controller: _contentController,
              decoration: const InputDecoration(
                labelText: 'Content *',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Content is required';
                }
                return null;
              },
              maxLines: 12,
              textInputAction: TextInputAction.newline,
            ),
            const SizedBox(height: 24),

            // Update button
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _updateNote,
              icon: const Icon(Icons.save),
              label: const Text('Update Note'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## Widgets

### 1. Note Card Widget (`lib/widgets/note_card.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/note.dart';

class NoteCard extends StatelessWidget {
  final Note note;
  final VoidCallback onTap;

  const NoteCard({
    super.key,
    required this.note,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat('MMM d, yyyy');

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Title
              Text(
                note.title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),

              // Preacher
              if (note.preacher != null) ...[
                Row(
                  children: [
                    Icon(Icons.person, size: 14, color: Colors.grey[600]),
                    const SizedBox(width: 4),
                    Text(
                      note.preacher!,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
              ],

              // Content preview
              Text(
                note.content,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[700],
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),

              // Tags
              if (note.tags != null && note.tags!.isNotEmpty) ...[
                Wrap(
                  spacing: 4,
                  runSpacing: 4,
                  children: note.tags!.take(3).map((tag) {
                    return Chip(
                      label: Text(
                        tag,
                        style: const TextStyle(fontSize: 10),
                      ),
                      padding: EdgeInsets.zero,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      visualDensity: VisualDensity.compact,
                    );
                  }).toList(),
                ),
                const SizedBox(height: 8),
              ],

              // Date and scripture reference
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    dateFormat.format(note.createdAt),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[500],
                    ),
                  ),
                  if (note.scriptureRefs != null && note.scriptureRefs!.isNotEmpty)
                    Row(
                      children: [
                        Icon(Icons.menu_book, size: 12, color: Colors.grey[500]),
                        const SizedBox(width: 4),
                        Text(
                          note.scriptureRefs!,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[500],
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### 2. Note Search Delegate (`lib/widgets/note_search_delegate.dart`)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/note.dart';
import '../providers/notes_provider.dart';
import '../screens/note_detail_screen.dart';

class NoteSearchDelegate extends SearchDelegate<Note?> {
  final WidgetRef ref;

  NoteSearchDelegate(this.ref);

  @override
  List<Widget> buildActions(BuildContext context) {
    return [
      IconButton(
        icon: const Icon(Icons.clear),
        onPressed: () {
          query = '';
        },
      ),
    ];
  }

  @override
  Widget buildLeading(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () {
        close(context, null);
      },
    );
  }

  @override
  Widget buildResults(BuildContext context) {
    return _SearchResults(query: query, ref: ref);
  }

  @override
  Widget buildSuggestions(BuildContext context) {
    if (query.isEmpty) {
      return const Center(
        child: Text('Enter a search query'),
      );
    }
    return _SearchResults(query: query, ref: ref);
  }
}

class _SearchResults extends StatefulWidget {
  final String query;
  final WidgetRef ref;

  const _SearchResults({required this.query, required this.ref});

  @override
  State<_SearchResults> createState() => _SearchResultsState();
}

class _SearchResultsState extends State<_SearchResults> {
  late Future<List<Note>> _searchFuture;

  @override
  void initState() {
    super.initState();
    _searchFuture = _performSearch();
  }

  @override
  void didUpdateWidget(_SearchResults oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.query != widget.query) {
      _searchFuture = _performSearch();
    }
  }

  Future<List<Note>> _performSearch() {
    return widget.ref.read(notesProvider.notifier).searchNotes(
          query: widget.query,
        );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Note>>(
      future: _searchFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return Center(
            child: Text('Error: ${snapshot.error}'),
          );
        }

        final notes = snapshot.data ?? [];

        if (notes.isEmpty) {
          return const Center(
            child: Text('No notes found'),
          );
        }

        return ListView.builder(
          itemCount: notes.length,
          itemBuilder: (context, index) {
            final note = notes[index];
            return ListTile(
              title: Text(note.title),
              subtitle: Text(
                note.content,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => NoteDetailScreen(noteId: note.id),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}
```

---

## Complete Usage Example

### Main App Setup

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'screens/notes_list_screen.dart';

void main() {
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Scribes - Sermon Notes',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const NotesListScreen(),
    );
  }
}
```

---

## Testing the Implementation

1. **Run code generation:**
   ```bash
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

2. **Ensure your API client is properly configured** with base URL and authentication headers

3. **Test the flow:**
   - View notes list
   - Create a new note
   - View note details
   - Edit a note
   - Delete a note
   - Search for notes

---

## Key Features

✅ **Complete CRUD operations** for sermon notes  
✅ **Search functionality** by query, preacher, or tags  
✅ **Infinite scroll pagination** for efficient loading  
✅ **Pull-to-refresh** for manual data updates  
✅ **Tag management** with add/remove functionality  
✅ **Scripture reference tracking**  
✅ **Error handling** with user-friendly messages  
✅ **Loading states** for better UX  
✅ **Responsive UI** with Material Design 3  

---

## Next Steps

- Add offline support with local database (sqflite or Hive)
- Implement note sharing between users
- Add rich text editing for note content
- Implement note export (PDF, text)
- Add reminders and notifications for notes
- Implement cross-references between notes (see CrossRef guide)

---

This completes the Flutter implementation guide for the Notes feature! 🎉
