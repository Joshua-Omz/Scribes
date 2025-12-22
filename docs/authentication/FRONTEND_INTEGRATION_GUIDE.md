# 🎨 Flutter Frontend Integration Guide for Authentication System

**Last Updated:** November 3, 2025  
**API Base URL:** `http://localhost:8000`  
**Framework:** Flutter/Dart  
**Target Platform:** iOS, Android, Web, Desktop

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Flutter Setup](#flutter-setup)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Authentication Flow](#authentication-flow)
5. [Token Management](#token-management)
6. [Flutter Implementation](#flutter-implementation)
7. [State Management with Riverpod](#state-management-with-riverpod)
8. [UI Components](#ui-components)
9. [Error Handling](#error-handling)
10. [Security Best Practices](#security-best-practices)
11. [Testing Checklist](#testing-checklist)

---

## 🌟 Overview

This guide provides everything you need to integrate the Scribes authentication system into your **Flutter** application. The backend uses **JWT tokens** with the following features:

- ✅ User registration with email verification
- ✅ Login with email/password
- ✅ Token refresh mechanism
- ✅ Password reset flow
- ✅ Email verification resend
- ✅ Admin user management
- ✅ Protected routes

---

## � Flutter Setup

### Required Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP client
  http: ^1.1.0
  dio: ^5.4.0  # Alternative, more feature-rich
  
  # State management
  flutter_riverpod: ^2.4.9
  
  # Secure storage
  flutter_secure_storage: ^9.0.0
  
  # Local storage
  shared_preferences: ^2.2.2
  
  # JSON serialization
  json_annotation: ^4.8.1
  
  # Routing
  go_router: ^12.1.3

dev_dependencies:
  build_runner: ^2.4.7
  json_serializable: ^6.7.1
```

Install dependencies:
```bash
flutter pub get
```

### Platform-Specific Configuration

#### Android (`android/app/src/main/AndroidManifest.xml`)

```xml
<manifest>
    <!-- Add internet permission -->
    <uses-permission android:name="android.permission.INTERNET"/>
    
    <application
        android:usesCleartextTraffic="true">  <!-- For localhost development -->
        ...
    </application>
</manifest>
```

#### iOS (`ios/Runner/Info.plist`)

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <!-- For localhost development -->
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

---

## �🔌 API Endpoints Reference

### Base Configuration

```dart
// lib/core/constants/api_constants.dart
class ApiConstants {
  // Use 10.0.2.2 for Android emulator, localhost for iOS simulator
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',  // Android emulator
    // defaultValue: 'http://localhost:8000',  // iOS simulator
  );
  
  static const String authBase = '$baseUrl/auth';
  static const String notesBase = '$baseUrl/notes';
  
  // Endpoints
  static const String register = '$authBase/register';
  static const String login = '$authBase/login';
  static const String refresh = '$authBase/refresh';
  static const String verifyEmail = '$authBase/verify-email';
  static const String resendVerification = '$authBase/resend-verification';
  static const String forgotPassword = '$authBase/forgot-password';
  static const String resetPassword = '$authBase/reset-password';
  static const String me = '$authBase/me';
  static const String changePassword = '$authBase/change-password';
}
```

### 1️⃣ **User Registration**

**Endpoint:** `POST /auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123",
  "full_name": "John Doe"  // optional
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "is_verified": false,
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-11-03T10:30:00Z",
  "updated_at": null
}
```

**Error Response (400):**
```json
{
  "detail": "Email already registered"
}
```

**Password Requirements:**
- Minimum 8 characters
- Must contain uppercase letter
- Must contain lowercase letter
- Must contain digit

---

### 2️⃣ **User Login**

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800  // 30 minutes in seconds
}
```

**Error Responses:**
- `401`: Invalid credentials
- `403`: User not verified or inactive

---

### 3️⃣ **Email Verification**

**Endpoint:** `POST /auth/verify-email`

**Request Body:**
```json
{
  "token": "abc123def456ghi789jkl012mno345pqr678"
}
```

**Success Response (200):**
```json
{
  "message": "Email verified successfully",
  "detail": "You can now access all features"
}
```

**Error Responses:**
- `400`: Invalid or expired token
- `404`: User not found

---

### 4️⃣ **Resend Verification Email**

**Endpoint:** `POST /auth/resend-verification`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "If the email exists and is unverified, a verification email has been sent",
  "detail": "Check your inbox and spam folder"
}
```

**Note:** Always returns 200 to prevent email enumeration attacks.

---

### 5️⃣ **Token Refresh**

**Endpoint:** `POST /auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Response (401):**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

---

### 6️⃣ **Forgot Password**

**Endpoint:** `POST /auth/forgot-password`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset email sent",
  "detail": "Check your email for password reset instructions"
}
```

---

### 7️⃣ **Reset Password**

**Endpoint:** `POST /auth/reset-password`

**Request Body:**
```json
{
  "token": "xyz789abc123def456ghi012jkl345mno678",
  "new_password": "NewSecurePass123"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully",
  "detail": "You can now login with your new password"
}
```

---

### 8️⃣ **Get Current User**

**Endpoint:** `GET /auth/me`

**Headers Required:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "is_verified": true,
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-11-03T10:30:00Z",
  "updated_at": "2025-11-03T11:00:00Z"
}
```

---

### 9️⃣ **Change Password**

**Endpoint:** `POST /auth/change-password`

**Headers Required:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

### 🔟 **Logout (Client-Side)**

**No backend endpoint needed** - simply remove tokens from storage.

```javascript
// Clear tokens
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
localStorage.removeItem('user');
```

---

## 🔄 Authentication Flow

### Complete User Journey

```
┌─────────────────────────────────────────────────────────────┐
│                    REGISTRATION FLOW                         │
└─────────────────────────────────────────────────────────────┘

1. User fills registration form
   └─> POST /auth/register
       ├─> Success: Show "Check email for verification"
       └─> Error: Display error message

2. User receives verification email
   └─> User clicks verification link
       └─> Frontend extracts token from URL
           └─> POST /auth/verify-email
               ├─> Success: Redirect to login
               └─> Error: Show error, offer resend

3. User can now login
   └─> POST /auth/login
       ├─> Success: Store tokens, redirect to dashboard
       └─> Error: Display error message

┌─────────────────────────────────────────────────────────────┐
│                       LOGIN FLOW                             │
└─────────────────────────────────────────────────────────────┘

1. User enters email and password
   └─> POST /auth/login
       ├─> Success (200):
       │   ├─> Store access_token in memory/state
       │   ├─> Store refresh_token in secure storage
       │   └─> Redirect to dashboard
       │
       ├─> Error (401): Invalid credentials
       │   └─> Show error message
       │
       └─> Error (403): Not verified
           └─> Show "Please verify email" + Resend button

┌─────────────────────────────────────────────────────────────┐
│                   TOKEN REFRESH FLOW                         │
└─────────────────────────────────────────────────────────────┘

1. API request fails with 401
   └─> Check if refresh_token exists
       ├─> Yes: POST /auth/refresh
       │   ├─> Success: Retry original request with new token
       │   └─> Error: Logout user (refresh token expired)
       │
       └─> No: Logout user

┌─────────────────────────────────────────────────────────────┐
│                 PASSWORD RESET FLOW                          │
└─────────────────────────────────────────────────────────────┘

1. User clicks "Forgot Password"
   └─> POST /auth/forgot-password
       └─> Show "Check email for reset instructions"

2. User receives password reset email
   └─> User clicks reset link
       └─> Frontend shows reset password form
           └─> POST /auth/reset-password
               ├─> Success: Redirect to login
               └─> Error: Show error, offer resend
```

---

## 🔐 Token Management

### Token Storage Strategy

```javascript
// ✅ RECOMMENDED: Access Token in Memory (React Example)
const [accessToken, setAccessToken] = useState(null);

// ✅ RECOMMENDED: Refresh Token in HttpOnly Cookie (Backend-managed)
// OR Secure localStorage with encryption

// ❌ NOT RECOMMENDED: Storing sensitive tokens in plain localStorage
```

### Token Refresh Implementation

```javascript
// Auto-refresh before token expires
let refreshTimer;

function scheduleTokenRefresh(expiresIn) {
  // Refresh 5 minutes before expiry
  const refreshTime = (expiresIn - 300) * 1000;
  
  refreshTimer = setTimeout(async () => {
    try {
      const newToken = await refreshAccessToken();
      setAccessToken(newToken);
      scheduleTokenRefresh(1800); // Reset timer
    } catch (error) {
      // Refresh failed, logout user
      logout();
    }
  }, refreshTime);
}

// Clear timer on logout
function clearRefreshTimer() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
  }
}
```

### HTTP Interceptor Pattern

```javascript
// Automatically add token to requests
axios.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors with token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const newToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout
        logout();
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

## 💻 Flutter Implementation

### Project Structure

```
lib/
├── core/
│   ├── constants/
│   │   └── api_constants.dart
│   ├── network/
│   │   ├── api_client.dart
│   │   └── api_interceptor.dart
│   ├── storage/
│   │   └── secure_storage_service.dart
│   └── utils/
│       └── validators.dart
├── features/
│   └── auth/
│       ├── data/
│       │   ├── models/
│       │   │   ├── user_model.dart
│       │   │   └── token_response.dart
│       │   ├── repositories/
│       │   │   └── auth_repository.dart
│       │   └── services/
│       │       └── auth_service.dart
│       ├── presentation/
│       │   ├── providers/
│       │   │   └── auth_provider.dart
│       │   ├── screens/
│       │   │   ├── login_screen.dart
│       │   │   ├── register_screen.dart
│       │   │   ├── verify_email_screen.dart
│       │   │   └── forgot_password_screen.dart
│       │   └── widgets/
│       │       ├── auth_text_field.dart
│       │       └── auth_button.dart
│       └── domain/
│           └── entities/
│               └── user.dart
└── main.dart
```

### 1. Data Models

```dart
// lib/features/auth/data/models/user_model.dart
import 'package:json_annotation/json_annotation.dart';

part 'user_model.g.dart';

@JsonSerializable()
class UserModel {
  final int id;
  final String email;
  final String username;
  @JsonKey(name: 'full_name')
  final String? fullName;
  final String role;
  @JsonKey(name: 'is_verified')
  final bool isVerified;
  @JsonKey(name: 'is_active')
  final bool isActive;
  @JsonKey(name: 'is_superuser')
  final bool isSuperuser;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'updated_at')
  final DateTime? updatedAt;

  UserModel({
    required this.id,
    required this.email,
    required this.username,
    this.fullName,
    required this.role,
    required this.isVerified,
    required this.isActive,
    required this.isSuperuser,
    required this.createdAt,
    this.updatedAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);

  Map<String, dynamic> toJson() => _$UserModelToJson(this);
}

@JsonSerializable()
class TokenResponse {
  @JsonKey(name: 'access_token')
  final String accessToken;
  @JsonKey(name: 'refresh_token')
  final String refreshToken;
  @JsonKey(name: 'token_type')
  final String tokenType;
  @JsonKey(name: 'expires_in')
  final int expiresIn;

  TokenResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) =>
      _$TokenResponseFromJson(json);

  Map<String, dynamic> toJson() => _$TokenResponseToJson(this);
}

@JsonSerializable()
class RegisterRequest {
  final String email;
  final String username;
  final String password;
  @JsonKey(name: 'full_name')
  final String? fullName;

  RegisterRequest({
    required this.email,
    required this.username,
    required this.password,
    this.fullName,
  });

  Map<String, dynamic> toJson() => _$RegisterRequestToJson(this);
}
```

**Generate code:**
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### 2. Secure Storage Service

```dart
// lib/core/storage/secure_storage_service.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class SecureStorageService {
  static const _storage = FlutterSecureStorage();
  
  // Keys
  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userKey = 'user';

  // Save tokens
  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }

  Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await Future.wait([
      saveAccessToken(accessToken),
      saveRefreshToken(refreshToken),
    ]);
  }

  // Get tokens
  Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshTokenKey);
  }

  // Save user data
  Future<void> saveUser(UserModel user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userKey, jsonEncode(user.toJson()));
  }

  // Get user data
  Future<UserModel?> getUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString(_userKey);
    if (userJson != null) {
      return UserModel.fromJson(jsonDecode(userJson));
    }
    return null;
  }

  // Clear all auth data
  Future<void> clearAll() async {
    await _storage.deleteAll();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userKey);
  }

  // Check if user is logged in
  Future<bool> hasValidTokens() async {
    final accessToken = await getAccessToken();
    final refreshToken = await getRefreshToken();
    return accessToken != null && refreshToken != null;
  }
}
```

### 3. API Client with Interceptor

```dart
// lib/core/network/api_client.dart
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../constants/api_constants.dart';
import '../storage/secure_storage_service.dart';

class ApiClient {
  late final Dio _dio;
  final SecureStorageService _storage = SecureStorageService();

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Add interceptors
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Add access token to all requests
          final token = await _storage.getAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          
          if (kDebugMode) {
            print('🌐 REQUEST[${options.method}] => ${options.uri}');
            print('Headers: ${options.headers}');
            print('Body: ${options.data}');
          }
          
          return handler.next(options);
        },
        onResponse: (response, handler) {
          if (kDebugMode) {
            print('✅ RESPONSE[${response.statusCode}] => ${response.requestOptions.uri}');
            print('Data: ${response.data}');
          }
          return handler.next(response);
        },
        onError: (error, handler) async {
          if (kDebugMode) {
            print('❌ ERROR[${error.response?.statusCode}] => ${error.requestOptions.uri}');
            print('Message: ${error.message}');
            print('Data: ${error.response?.data}');
          }

          // Handle 401 - Try to refresh token
          if (error.response?.statusCode == 401) {
            try {
              final refreshToken = await _storage.getRefreshToken();
              if (refreshToken != null) {
                // Attempt token refresh
                final response = await _dio.post(
                  ApiConstants.refresh,
                  data: {'refresh_token': refreshToken},
                  options: Options(
                    headers: {'Authorization': null}, // Remove old token
                  ),
                );

                final newAccessToken = response.data['access_token'];
                await _storage.saveAccessToken(newAccessToken);

                // Retry original request with new token
                error.requestOptions.headers['Authorization'] = 
                    'Bearer $newAccessToken';
                return handler.resolve(await _dio.fetch(error.requestOptions));
              }
            } catch (e) {
              // Refresh failed, logout user
              await _storage.clearAll();
              // Navigate to login (handled in provider)
            }
          }

          return handler.next(error);
        },
      ),
    );

    // Add logging interceptor in debug mode
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        request: true,
        requestBody: true,
        responseBody: true,
        error: true,
      ));
    }
  }

  Dio get dio => _dio;
}
```

### 4. Auth Service

```dart
// lib/features/auth/data/services/auth_service.dart
import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/storage/secure_storage_service.dart';
import '../models/user_model.dart';

class AuthService {
  final ApiClient _apiClient = ApiClient();
  final SecureStorageService _storage = SecureStorageService();

  Dio get _dio => _apiClient.dio;

  // Register
  Future<UserModel> register({
    required String email,
    required String username,
    required String password,
    String? fullName,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.register,
        data: RegisterRequest(
          email: email,
          username: username,
          password: password,
          fullName: fullName,
        ).toJson(),
      );

      return UserModel.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Login
  Future<TokenResponse> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.login,
        data: {
          'email': email,
          'password': password,
        },
      );

      final tokenResponse = TokenResponse.fromJson(response.data);

      // Save tokens
      await _storage.saveTokens(
        accessToken: tokenResponse.accessToken,
        refreshToken: tokenResponse.refreshToken,
      );

      return tokenResponse;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Get current user
  Future<UserModel> getCurrentUser() async {
    try {
      final response = await _dio.get(ApiConstants.me);
      final user = UserModel.fromJson(response.data);
      
      // Cache user data
      await _storage.saveUser(user);
      
      return user;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Verify email
  Future<void> verifyEmail(String token) async {
    try {
      await _dio.post(
        ApiConstants.verifyEmail,
        data: {'token': token},
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Resend verification
  Future<void> resendVerification(String email) async {
    try {
      await _dio.post(
        ApiConstants.resendVerification,
        data: {'email': email},
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Forgot password
  Future<void> forgotPassword(String email) async {
    try {
      await _dio.post(
        ApiConstants.forgotPassword,
        data: {'email': email},
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Reset password
  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      await _dio.post(
        ApiConstants.resetPassword,
        data: {
          'token': token,
          'new_password': newPassword,
        },
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Change password
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _dio.post(
        ApiConstants.changePassword,
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
        },
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Logout
  Future<void> logout() async {
    await _storage.clearAll();
  }

  // Check if logged in
  Future<bool> isLoggedIn() async {
    return await _storage.hasValidTokens();
  }

  // Get cached user
  Future<UserModel?> getCachedUser() async {
    return await _storage.getUser();
  }

  // Error handling
  String _handleError(DioException error) {
    if (error.response != null) {
      final data = error.response!.data;
      if (data is Map && data.containsKey('detail')) {
        return data['detail'].toString();
      }
      return 'Server error: ${error.response!.statusCode}';
    } else if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'Connection timeout. Please check your internet connection.';
    } else if (error.type == DioExceptionType.unknown) {
      return 'No internet connection. Please check your network.';
    }
    return 'An unexpected error occurred.';
  }
}
```

### React Implementation

### 5. State Management with Riverpod

```dart
// lib/features/auth/presentation/providers/auth_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/user_model.dart';
import '../../data/services/auth_service.dart';

// Auth state
class AuthState {
  final UserModel? user;
  final bool isLoading;
  final bool isAuthenticated;
  final String? error;

  const AuthState({
    this.user,
    this.isLoading = false,
    this.isAuthenticated = false,
    this.error,
  });

  AuthState copyWith({
    UserModel? user,
    bool? isLoading,
    bool? isAuthenticated,
    String? error,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      error: error,
    );
  }
}

// Auth service provider
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

// Auth state notifier
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthNotifier(this._authService) : super(const AuthState()) {
    _initAuth();
  }

  // Initialize auth state
  Future<void> _initAuth() async {
    state = state.copyWith(isLoading: true);
    
    try {
      final isLoggedIn = await _authService.isLoggedIn();
      if (isLoggedIn) {
        final cachedUser = await _authService.getCachedUser();
        if (cachedUser != null) {
          // Try to fetch fresh user data
          try {
            final user = await _authService.getCurrentUser();
            state = state.copyWith(
              user: user,
              isAuthenticated: true,
              isLoading: false,
            );
          } catch (e) {
            // Use cached user if fetch fails
            state = state.copyWith(
              user: cachedUser,
              isAuthenticated: true,
              isLoading: false,
            );
          }
        }
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  // Register
  Future<void> register({
    required String email,
    required String username,
    required String password,
    String? fullName,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final user = await _authService.register(
        email: email,
        username: username,
        password: password,
        fullName: fullName,
      );
      
      state = state.copyWith(
        user: user,
        isLoading: false,
        isAuthenticated: false, // Not authenticated until verified
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Login
  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.login(email: email, password: password);
      final user = await _authService.getCurrentUser();
      
      state = state.copyWith(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Logout
  Future<void> logout() async {
    await _authService.logout();
    state = const AuthState();
  }

  // Verify email
  Future<void> verifyEmail(String token) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.verifyEmail(token);
      
      // Update user verification status
      if (state.user != null) {
        final updatedUser = UserModel(
          id: state.user!.id,
          email: state.user!.email,
          username: state.user!.username,
          fullName: state.user!.fullName,
          role: state.user!.role,
          isVerified: true,
          isActive: state.user!.isActive,
          isSuperuser: state.user!.isSuperuser,
          createdAt: state.user!.createdAt,
          updatedAt: DateTime.now(),
        );
        
        state = state.copyWith(
          user: updatedUser,
          isLoading: false,
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Resend verification
  Future<void> resendVerification(String email) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.resendVerification(email);
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Forgot password
  Future<void> forgotPassword(String email) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.forgotPassword(email);
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Reset password
  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.resetPassword(
        token: token,
        newPassword: newPassword,
      );
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Change password
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      rethrow;
    }
  }

  // Refresh user data
  Future<void> refreshUser() async {
    try {
      final user = await _authService.getCurrentUser();
      state = state.copyWith(user: user);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }
}

// Auth provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});
```

---

## 🎨 UI Components

### 6. Validators

```dart
// lib/core/utils/validators.dart
class Validators {
  static String? email(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email is required';
    }
    
    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(value)) {
      return 'Please enter a valid email';
    }
    
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return 'Password must contain an uppercase letter';
    }
    
    if (!value.contains(RegExp(r'[a-z]'))) {
      return 'Password must contain a lowercase letter';
    }
    
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain a digit';
    }
    
    return null;
  }

  static String? username(String? value) {
    if (value == null || value.isEmpty) {
      return 'Username is required';
    }
    
    if (value.length < 3) {
      return 'Username must be at least 3 characters';
    }
    
    if (value.length > 50) {
      return 'Username must be less than 50 characters';
    }
    
    final usernameRegex = RegExp(r'^[a-zA-Z0-9_]+$');
    if (!usernameRegex.hasMatch(value)) {
      return 'Username can only contain letters, numbers, and underscores';
    }
    
    return null;
  }

  static String? required(String? value, {String fieldName = 'This field'}) {
    if (value == null || value.isEmpty) {
      return '$fieldName is required';
    }
    return null;
  }
}
```

### 7. Register Screen

```dart
// lib/features/auth/presentation/screens/register_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/utils/validators.dart';
import '../providers/auth_provider.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _fullNameController = TextEditingController();
  
  bool _obscurePassword = true;
  bool _isSuccess = false;

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _fullNameController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      await ref.read(authProvider.notifier).register(
            email: _emailController.text.trim(),
            username: _usernameController.text.trim(),
            password: _passwordController.text,
            fullName: _fullNameController.text.trim().isEmpty
                ? null
                : _fullNameController.text.trim(),
          );

      setState(() => _isSuccess = true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    if (_isSuccess) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.check_circle,
                  color: Colors.green,
                  size: 80,
                ),
                const SizedBox(height: 24),
                Text(
                  'Registration Successful!',
                  style: Theme.of(context).textTheme.headlineSmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                const Text(
                  'Please check your email to verify your account.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: () => context.go('/login'),
                  child: const Text('Go to Login'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Register'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Text(
                'Create Account',
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Sign up to get started',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              
              // Email field
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                validator: Validators.email,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  hintText: 'your.email@example.com',
                  prefixIcon: Icon(Icons.email),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              
              // Username field
              TextFormField(
                controller: _usernameController,
                validator: Validators.username,
                decoration: const InputDecoration(
                  labelText: 'Username',
                  hintText: 'johndoe',
                  prefixIcon: Icon(Icons.person),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              
              // Password field
              TextFormField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                validator: Validators.password,
                decoration: InputDecoration(
                  labelText: 'Password',
                  hintText: 'Min 8 chars, uppercase, lowercase, digit',
                  prefixIcon: const Icon(Icons.lock),
                  border: const OutlineInputBorder(),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ? Icons.visibility : Icons.visibility_off,
                    ),
                    onPressed: () {
                      setState(() => _obscurePassword = !_obscurePassword);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 16),
              
              // Full name field (optional)
              TextFormField(
                controller: _fullNameController,
                decoration: const InputDecoration(
                  labelText: 'Full Name (Optional)',
                  hintText: 'John Doe',
                  prefixIcon: Icon(Icons.badge),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              
              // Register button
              ElevatedButton(
                onPressed: authState.isLoading ? null : _handleRegister,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: authState.isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Register'),
              ),
              const SizedBox(height: 16),
              
              // Login link
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Already have an account? '),
                  TextButton(
                    onPressed: () => context.go('/login'),
                    child: const Text('Login'),
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

### 8. Login Screen

```dart
// lib/features/auth/presentation/screens/login_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/utils/validators.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  
  bool _obscurePassword = true;
  bool _showResendButton = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      await ref.read(authProvider.notifier).login(
            email: _emailController.text.trim(),
            password: _passwordController.text,
          );

      if (mounted) {
        context.go('/dashboard');
      }
    } catch (e) {
      final errorMessage = e.toString();
      
      // Check if it's a verification error
      if (errorMessage.contains('verify') || errorMessage.contains('verified')) {
        setState(() => _showResendButton = true);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: Colors.red,
            action: _showResendButton
                ? SnackBarAction(
                    label: 'Resend',
                    textColor: Colors.white,
                    onPressed: _handleResendVerification,
                  )
                : null,
          ),
        );
      }
    }
  }

  Future<void> _handleResendVerification() async {
    try {
      await ref.read(authProvider.notifier).resendVerification(
            _emailController.text.trim(),
          );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Verification email sent! Check your inbox.'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Login'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Text(
                'Welcome Back',
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Login to your account',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              
              // Email field
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                validator: Validators.email,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  hintText: 'your.email@example.com',
                  prefixIcon: Icon(Icons.email),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              
              // Password field
              TextFormField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                validator: (value) => Validators.required(value, fieldName: 'Password'),
                decoration: InputDecoration(
                  labelText: 'Password',
                  hintText: 'Enter your password',
                  prefixIcon: const Icon(Icons.lock),
                  border: const OutlineInputBorder(),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ? Icons.visibility : Icons.visibility_off,
                    ),
                    onPressed: () {
                      setState(() => _obscurePassword = !_obscurePassword);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 8),
              
              // Forgot password link
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => context.push('/forgot-password'),
                  child: const Text('Forgot Password?'),
                ),
              ),
              const SizedBox(height: 16),
              
              // Login button
              ElevatedButton(
                onPressed: authState.isLoading ? null : _handleLogin,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: authState.isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Login'),
              ),
              const SizedBox(height: 16),
              
              // Register link
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text("Don't have an account? "),
                  TextButton(
                    onPressed: () => context.go('/register'),
                    child: const Text('Register'),
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

### 9. Routing with GoRouter

```dart
// lib/core/router/app_router.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/register_screen.dart';
import '../../features/auth/presentation/screens/verify_email_screen.dart';
import '../../features/auth/presentation/screens/forgot_password_screen.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isVerified = authState.user?.isVerified ?? false;
      final isLoading = authState.isLoading;
      
      final isGoingToLogin = state.matchedLocation == '/login';
      final isGoingToRegister = state.matchedLocation == '/register';
      final isGoingToAuth = isGoingToLogin || isGoingToRegister ||
          state.matchedLocation.startsWith('/verify') ||
          state.matchedLocation.startsWith('/forgot-password');

      // Still loading, don't redirect
      if (isLoading) return null;

      // Not authenticated, redirect to login (unless already going to auth pages)
      if (!isAuthenticated) {
        return isGoingToAuth ? null : '/login';
      }

      // Authenticated but not verified, redirect to verify required page
      if (!isVerified && !state.matchedLocation.startsWith('/verify')) {
        return '/verify-required';
      }

      // Authenticated and verified, redirect away from auth pages
      if (isGoingToAuth) {
        return '/dashboard';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        redirect: (context, state) => '/dashboard',
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/verify-email',
        builder: (context, state) {
          final token = state.uri.queryParameters['token'];
          return VerifyEmailScreen(token: token);
        },
      ),
      GoRoute(
        path: '/verify-required',
        builder: (context, state) => const VerifyRequiredScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const DashboardScreen(),
      ),
      // Add more protected routes here
    ],
  );
});
```

### 10. Verify Email Screen

```dart
// lib/features/auth/presentation/screens/verify_email_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';

class VerifyEmailScreen extends ConsumerStatefulWidget {
  final String? token;

  const VerifyEmailScreen({super.key, this.token});

  @override
  ConsumerState<VerifyEmailScreen> createState() => _VerifyEmailScreenState();
}

class _VerifyEmailScreenState extends ConsumerState<VerifyEmailScreen> {
  String _status = 'verifying';
  String _message = '';

  @override
  void initState() {
    super.initState();
    _verifyEmail();
  }

  Future<void> _verifyEmail() async {
    if (widget.token == null || widget.token!.isEmpty) {
      setState(() {
        _status = 'error';
        _message = 'Invalid verification link';
      });
      return;
    }

    try {
      await ref.read(authProvider.notifier).verifyEmail(widget.token!);
      
      setState(() {
        _status = 'success';
        _message = 'Email verified successfully!';
      });

      // Redirect to login after 3 seconds
      await Future.delayed(const Duration(seconds: 3));
      if (mounted) {
        context.go('/login');
      }
    } catch (e) {
      setState(() {
        _status = 'error';
        _message = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Email Verification'),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (_status == 'verifying') ...[
                const CircularProgressIndicator(),
                const SizedBox(height: 24),
                const Text('Verifying your email...'),
              ] else if (_status == 'success') ...[
                const Icon(
                  Icons.check_circle,
                  color: Colors.green,
                  size: 80,
                ),
                const SizedBox(height: 24),
                Text(
                  _message,
                  style: Theme.of(context).textTheme.headlineSmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                const Text('Redirecting to login...'),
              ] else ...[
                const Icon(
                  Icons.error,
                  color: Colors.red,
                  size: 80,
                ),
                const SizedBox(height: 24),
                Text(
                  _message,
                  style: Theme.of(context).textTheme.headlineSmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: () => context.go('/login'),
                  child: const Text('Go to Login'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
```

### 11. Main App Setup

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router/app_router.dart';

void main() {
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'Scribes',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
```

---

## 📦 State Management with Riverpod

### What to Store and Where

```dart
// ✅ Store in Riverpod State (Memory)
class AuthState {
  final UserModel? user;
  final bool isAuthenticated;
  final bool isLoading;
  final String? error;
}

// ✅ Store in FlutterSecureStorage (Encrypted)
- access_token
- refresh_token

// ✅ Store in SharedPreferences (Cache)
- user data (for quick load)

// ❌ NEVER store
- password (never persist)
- sensitive user data in plain SharedPreferences
```

### Riverpod Providers Overview

```dart
// Service provider
final authServiceProvider = Provider<AuthService>((ref) => AuthService());

// State notifier provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});

// Usage in widgets
Consumer(
  builder: (context, ref, child) {
    final authState = ref.watch(authProvider);
    // Use authState here
  },
)
```

---

## ⚠️ Error Handling

### Common Error Codes

```dart
// lib/core/utils/error_handler.dart
class ErrorHandler {
  static const Map<int, String> _errorMessages = {
    400: 'Invalid request. Please check your input.',
    401: 'Authentication failed. Please login again.',
    403: 'Access denied. You do not have permission.',
    404: 'Resource not found.',
    422: 'Validation error. Please check your input.',
    500: 'Server error. Please try again later.',
  };

  static String handleDioError(DioException error) {
    if (error.response != null) {
      final statusCode = error.response!.statusCode;
      final data = error.response!.data;
      
      // Extract detail from response
      String? detail;
      if (data is Map && data.containsKey('detail')) {
        detail = data['detail'].toString();
      }
      
      // Log error for debugging
      debugPrint('API Error: $statusCode - $detail');
      
      // Return specific error message
      return detail ?? _errorMessages[statusCode] ?? 'An error occurred';
    } else if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'Connection timeout. Please check your internet connection.';
    } else if (error.type == DioExceptionType.unknown) {
      return 'No internet connection. Please check your network.';
    }
    
    return 'An unexpected error occurred.';
  }

  static void showErrorSnackbar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'Dismiss',
          textColor: Colors.white,
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
  }

  static void showSuccessSnackbar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
```

### Validation Error Handling

```dart
// Backend returns 422 with validation details
// {
//   "detail": [
//     {
//       "type": "string_too_short",
//       "loc": ["body", "password"],
//       "msg": "String should have at least 8 characters",
//       "input": "short"
//     }
//   ]
// }

class ValidationError {
  static String parseValidationErrors(dynamic detail) {
    if (detail is List) {
      return detail.map((err) {
        final field = err['loc']?.last ?? 'field';
        final message = err['msg'] ?? 'Invalid value';
        return '$field: $message';
      }).join('\n');
    }
    return detail.toString();
  }
}
```

---

## 🔒 Security Best Practices

### 1. Token Storage

```dart
// ✅ BEST: Use FlutterSecureStorage for tokens
const storage = FlutterSecureStorage();
await storage.write(key: 'access_token', value: token);
await storage.write(key: 'refresh_token', value: refreshToken);

// ✅ ACCEPTABLE: SharedPreferences for non-sensitive cache
final prefs = await SharedPreferences.getInstance();
await prefs.setString('user', jsonEncode(userData));

// ❌ BAD: Plain SharedPreferences for tokens
await prefs.setString('access_token', token); // DON'T DO THIS
```

### 2. Platform-Specific Configuration

```dart
// lib/core/constants/api_constants.dart
class ApiConstants {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: kIsWeb
        ? 'http://localhost:8000'  // Web
        : Platform.isAndroid
            ? 'http://10.0.2.2:8000'  // Android emulator
            : 'http://localhost:8000',  // iOS simulator
  );
  
  // Production
  static const String prodUrl = 'https://api.scribes.com';
  
  static String get apiUrl {
    return kReleaseMode ? prodUrl : baseUrl;
  }
}
```

### 3. HTTPS/SSL Pinning (Production)

```dart
// For production, implement SSL pinning
class SecureHttpClient {
  static HttpClient getSecureClient() {
    final client = HttpClient();
    
    client.badCertificateCallback = 
        (X509Certificate cert, String host, int port) {
      // Implement certificate pinning here
      return false;  // Only accept valid certificates
    };
    
    return client;
  }
}
```

### 4. Password Validation

```dart
// Already implemented in Validators class
class Validators {
  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    
    final errors = <String>[];
    
    if (value.length < 8) {
      errors.add('at least 8 characters');
    }
    if (!RegExp(r'[A-Z]').hasMatch(value)) {
      errors.add('an uppercase letter');
    }
    if (!RegExp(r'[a-z]').hasMatch(value)) {
      errors.add('a lowercase letter');
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      errors.add('a digit');
    }
    
    if (errors.isNotEmpty) {
      return 'Password must contain ${errors.join(', ')}';
    }
    
    return null;
  }
}
```

### 5. Secure Input Handling

```dart
// ✅ Flutter automatically escapes text in Text widgets
Text(user.fullName)  // Safe

// ✅ Sanitize user input before storing
String sanitizeInput(String input) {
  return input.trim().replaceAll(RegExp(r'[<>]'), '');
}

// ❌ Be careful with HTML widgets
Html(data: userInput)  // Potential XSS risk
```

### 6. Biometric Authentication (Optional Enhancement)

```dart
// Add to pubspec.yaml: local_auth: ^2.1.7

import 'package:local_auth/local_auth.dart';

class BiometricService {
  final LocalAuthentication _auth = LocalAuthentication();

  Future<bool> authenticate() async {
    try {
      final canAuth = await _auth.canCheckBiometrics;
      if (!canAuth) return false;

      return await _auth.authenticate(
        localizedReason: 'Please authenticate to access your account',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: true,
        ),
      );
    } catch (e) {
      debugPrint('Biometric auth error: $e');
      return false;
    }
  }
}
```

### 7. Secure Logging

```dart
// Don't log sensitive information
void secureLog(String message, {Map<String, dynamic>? data}) {
  if (kDebugMode) {
    // Remove sensitive fields
    final sanitizedData = data?..remove('password')
        ..remove('token')
        ..remove('access_token')
        ..remove('refresh_token');
    
    debugPrint('$message: $sanitizedData');
  }
}
```

---

## ✅ Testing Checklist

### Registration Flow

- [ ] User can register with valid data
- [ ] Email validation works
- [ ] Password validation enforces requirements
- [ ] Duplicate email shows error
- [ ] Duplicate username shows error
- [ ] Success message displays after registration
- [ ] Verification email is sent

### Login Flow

- [ ] User can login with correct credentials
- [ ] Invalid credentials show error
- [ ] Unverified user sees verification prompt
- [ ] Inactive user cannot login
- [ ] Tokens are stored correctly
- [ ] User data is fetched after login
- [ ] Dashboard loads after successful login

### Email Verification

- [ ] Verification link works
- [ ] Invalid token shows error
- [ ] Expired token shows error
- [ ] Already verified user handled correctly
- [ ] Resend verification works
- [ ] User redirected to login after verification

### Token Management

- [ ] Access token is included in authenticated requests
- [ ] 401 errors trigger token refresh
- [ ] Expired refresh token logs out user
- [ ] Tokens cleared on logout
- [ ] Token refresh works automatically

### Password Reset

- [ ] Forgot password sends email
- [ ] Reset link works
- [ ] Invalid token shows error
- [ ] Expired token shows error
- [ ] Password can be reset successfully
- [ ] User redirected to login after reset

### Protected Routes

- [ ] Unauthenticated users redirected to login
- [ ] Unverified users see verification required page
- [ ] Authenticated users can access protected pages
- [ ] Token expiration handled gracefully

### Error Handling

- [ ] Network errors show user-friendly messages
- [ ] Validation errors display correctly
- [ ] 401 errors trigger proper flow
- [ ] 500 errors handled gracefully
- [ ] Loading states work correctly

---

## 🚀 Quick Start Commands

### Flutter Project Setup

```bash
# Create new Flutter project
flutter create scribes_app
cd scribes_app

# Add dependencies
flutter pub add http dio flutter_riverpod flutter_secure_storage shared_preferences json_annotation go_router
flutter pub add --dev build_runner json_serializable

# Generate model code
flutter pub run build_runner build --delete-conflicting-outputs

# Run on Android emulator (make sure emulator is running)
flutter run

# Run on iOS simulator (macOS only)
flutter run -d ios

# Run on Chrome (web)
flutter run -d chrome

# Build for production
flutter build apk  # Android
flutter build ios  # iOS
flutter build web  # Web
```

### Test Backend API (cURL)

```bash
# Test registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test123"}'

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123"}'

# Test authenticated request
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Android Emulator Network

```bash
# Use 10.0.2.2 to access localhost from Android emulator
http://10.0.2.2:8000

# For real device, use your computer's IP address
http://192.168.1.XXX:8000
```

---

## 📚 Additional Resources

- [Authentication Flow Diagram](./AUTH_FLOW.md)
- [API Setup Guide](./AUTH_SETUP_GUIDE.md)
- [Token Types Explanation](./VERIFICATION_TOKEN_EXPLANATION.md)
- [Backend Swagger UI](http://localhost:8000/docs)

---

## 🆘 Common Issues & Solutions

### Issue: "Invalid token" on every request

**Solution:** Make sure you're including "Bearer " prefix:
```javascript
headers: { Authorization: `Bearer ${accessToken}` }  // ✅ Correct
headers: { Authorization: accessToken }              // ❌ Wrong
```

### Issue: CORS errors

**Solution:** Check backend CORS settings allow your frontend origin:
```python
# Backend should have your frontend URL in CORS origins
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

### Issue: Tokens not persisting across page refresh

**Solution:** Store tokens in localStorage and restore on app load:
```javascript
useEffect(() => {
  const storedUser = localStorage.getItem('user');
  if (storedUser) {
    setUser(JSON.parse(storedUser));
  }
}, []);
```

### Issue: Can't login after registration

**Solution:** Make sure email verification is complete:
1. Check spam folder for verification email
2. Use resend verification if needed
3. Or use admin endpoint to manually verify

---

**Questions?** Check the [troubleshooting docs](../troubleshooting/) or review the [API documentation](http://localhost:8000/docs).

**Last Updated:** November 3, 2025
