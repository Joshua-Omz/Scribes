# Authentication System Guide
**JWT-Based Authentication with Role-Based Access Control**

## 📋 Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [For Frontend Developers](#for-frontend-developers)
4. [For DevOps Engineers](#for-devops-engineers)
5. [For Cloud Engineers](#for-cloud-engineers)
6. [API Reference](#api-reference)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the Authentication System?

Scribes uses **JWT (JSON Web Tokens)** for stateless authentication with:
- User registration with email verification
- Login with access/refresh tokens
- Password reset flow
- Role-based access control (Admin/User)
- Token refresh mechanism

**Key Features:**
- ✅ Secure password hashing (bcrypt)
- ✅ JWT tokens with expiration
- ✅ Refresh token rotation
- ✅ Role-based authorization
- ✅ Password reset via email
- ✅ Account verification

---

## How It Works

### Authentication Flow

```
┌──────────────────────────────────────────────────────────┐
│                  User Registration                        │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  POST /auth/register
         │  {email, password,  │
         │   username}          │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Hash Password     │
         │  (bcrypt)          │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Save User to DB   │
         │  is_verified=false │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Send Verification│
         │  Email (optional)  │
         └────────────────────┘
```

### Login Flow

```
┌──────────────────────────────────────────────────────────┐
│                      User Login                           │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  POST /auth/login  │
         │  {email, password} │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Verify Password   │
         │  (bcrypt.check)    │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Generate Tokens   │
         │  - Access (30min)  │
         │  - Refresh (7days) │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Return Response   │
         │  {access_token,    │
         │   refresh_token,   │
         │   user_info}       │
         └────────────────────┘
```

### Token Validation

```
┌──────────────────────────────────────────────────────────┐
│              Protected Endpoint Request                   │
└──────────────────┬───────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  GET /notes        │
         │  Authorization:    │
         │  Bearer <token>    │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Extract Token     │
         │  from Header       │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Decode & Verify   │
         │  JWT Signature     │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Check Expiration  │
         │  & Extract user_id │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Load User from DB │
         │  Check is_active   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Process Request   │
         │  with User Context │
         └────────────────────┘
```

---

## For Frontend Developers (Flutter/Dart)

### 1. User Registration

**Endpoint:** `POST /auth/register`

**Request:**
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> registerUser({
  required String email,
  required String username,
  required String password,
  String? fullName,
}) async {
  final response = await http.post(
    Uri.parse('http://localhost:8000/auth/register'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'username': username,
      'password': password,
      'full_name': fullName,
    }),
  );

  if (response.statusCode == 201) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Registration failed: ${response.body}');
  }
}
```

**Response (Success - 201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-12-24T10:00:00Z"
}
```

**Response (Error - 400):**
```json
{
  "detail": "Email already registered"
}
```

---

### 2. User Login

**Endpoint:** `POST /auth/login`

**Request:**
```dart
Future<Map<String, dynamic>> loginUser({
  required String email,
  required String password,
}) async {
  final response = await http.post(
    Uri.parse('http://localhost:8000/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Login failed: ${response.body}');
  }
}
```

**Response (Success - 200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "user"
  }
}
```

**Store Tokens:**
```dart
import 'package:shared_preferences/shared_preferences.dart';

Future<void> storeTokens({
  required String accessToken,
  required String refreshToken,
  required Map<String, dynamic> user,
}) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString('access_token', accessToken);
  await prefs.setString('refresh_token', refreshToken);
  await prefs.setString('user', jsonEncode(user));
}

Future<String?> getAccessToken() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getString('access_token');
}
```

---

### 3. Making Authenticated Requests

**Add Authorization Header:**
```dart
import 'package:http/http.dart' as http;

Future<http.Response> makeAuthenticatedRequest(String endpoint) async {
  final prefs = await SharedPreferences.getInstance();
  final accessToken = prefs.getString('access_token');

  return await http.get(
    Uri.parse('http://localhost:8000$endpoint'),
    headers: {
      'Authorization': 'Bearer $accessToken',
      'Content-Type': 'application/json',
    },
  );
}
```

**Flutter Provider Example:**
```dart
// auth_provider.dart
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class User {
  final int id;
  final String email;
  final String username;
  final String role;

  User({
    required this.id,
    required this.email,
    required this.username,
    required this.role,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      username: json['username'],
      role: json['role'],
    );
  }
}

class AuthProvider with ChangeNotifier {
  User? _user;
  String? _accessToken;
  String? _refreshToken;
  bool _isLoading = true;

  User? get user => _user;
  bool get isAuthenticated => _user != null;
  bool get isLoading => _isLoading;
  String? get accessToken => _accessToken;

  Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('user');
    _accessToken = prefs.getString('access_token');
    _refreshToken = prefs.getString('refresh_token');

    if (userJson != null && _accessToken != null) {
      _user = User.fromJson(jsonDecode(userJson));
    }
    
    _isLoading = false;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('http://localhost:8000/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];
      _user = User.fromJson(data['user']);

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', _accessToken!);
      await prefs.setString('refresh_token', _refreshToken!);
      await prefs.setString('user', jsonEncode(data['user']));

      notifyListeners();
    } else {
      throw Exception('Login failed');
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    await prefs.remove('user');

    _user = null;
    _accessToken = null;
    _refreshToken = null;
    notifyListeners();
  }
}
```

---

### 4. Token Refresh

**Endpoint:** `POST /auth/refresh`

**When to refresh:**
- Access token expires (30 minutes)
- Before expiration (proactive refresh)
- After receiving 401 Unauthorized

**Request:**
```dart
Future<String> refreshAccessToken() async {
  final prefs = await SharedPreferences.getInstance();
  final refreshToken = prefs.getString('refresh_token');

  final response = await http.post(
    Uri.parse('http://localhost:8000/auth/refresh'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'refresh_token': refreshToken}),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    await prefs.setString('access_token', data['access_token']);
    return data['access_token'];
  } else {
    throw Exception('Token refresh failed');
  }
}
```

**Dio Interceptor Example (Recommended for Flutter):**
```dart
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthInterceptor extends Interceptor {
  final Dio dio;

  AuthInterceptor(this.dio);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioError err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      try {
        // Attempt to refresh token
        final prefs = await SharedPreferences.getInstance();
        final refreshToken = prefs.getString('refresh_token');

        final response = await dio.post(
          '/auth/refresh',
          data: {'refresh_token': refreshToken},
          options: Options(headers: {'Authorization': null}),
        );

        final newToken = response.data['access_token'];
        await prefs.setString('access_token', newToken);

        // Retry original request with new token
        err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
        final retryResponse = await dio.fetch(err.requestOptions);
        handler.resolve(retryResponse);
      } catch (e) {
        // Refresh failed, redirect to login
        final prefs = await SharedPreferences.getInstance();
        await prefs.clear();
        handler.next(err);
      }
    } else {
      handler.next(err);
    }
  }
}

// Setup Dio client
Dio createDioClient() {
  final dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000',
    connectTimeout: Duration(seconds: 5),
    receiveTimeout: Duration(seconds: 3),
  ));

  dio.interceptors.add(AuthInterceptor(dio));
  return dio;
}
```

---

### 5. Password Reset Flow

**Step 1: Request Reset**
```dart
Future<void> requestPasswordReset(String email) async {
  final response = await http.post(
    Uri.parse('http://localhost:8000/auth/password-reset/request'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'email': email}),
  );

  if (response.statusCode == 200) {
    // User receives email with reset link
    print('Password reset email sent');
  } else {
    throw Exception('Failed to request password reset');
  }
}
```

**Step 2: Reset Password**
```dart
Future<void> confirmPasswordReset({
  required String token,
  required String newPassword,
}) async {
  final response = await http.post(
    Uri.parse('http://localhost:8000/auth/password-reset/confirm'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'token': token,
      'new_password': newPassword,
    }),
  );

  if (response.statusCode == 200) {
    print('Password reset successful');
  } else {
    throw Exception('Failed to reset password');
  }
}
```

---

### 6. Role-Based UI Components

**Check User Role:**
```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class AdminPanel extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    
    if (authProvider.user?.role != 'admin') {
      return Scaffold(
        body: Center(
          child: Text('Access Denied'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text('Admin Panel')),
      body: Center(
        child: Text('Admin content here'),
      ),
    );
  }
}
```

**Conditional Rendering:**
```dart
class NavigationDrawer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.user;

    return Drawer(
      child: ListView(
        children: [
          DrawerHeader(
            child: Text(user?.email ?? 'Not logged in'),
          ),
          ListTile(
            leading: Icon(Icons.home),
            title: Text('Home'),
            onTap: () => Navigator.pushNamed(context, '/'),
          ),
          ListTile(
            leading: Icon(Icons.note),
            title: Text('My Notes'),
            onTap: () => Navigator.pushNamed(context, '/notes'),
          ),
          // Admin-only menu item
          if (user?.role == 'admin')
            ListTile(
              leading: Icon(Icons.admin_panel_settings),
              title: Text('Admin Panel'),
              onTap: () => Navigator.pushNamed(context, '/admin'),
            ),
          Divider(),
          ListTile(
            leading: Icon(user != null ? Icons.logout : Icons.login),
            title: Text(user != null ? 'Logout' : 'Login'),
            onTap: () {
              if (user != null) {
                authProvider.logout();
              } else {
                Navigator.pushNamed(context, '/login');
              }
            },
          ),
        ],
      ),
    );
  }
}
```

---

## For DevOps Engineers

### Environment Configuration

**Required Variables:**
```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-min-32-chars  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@scribes.app
SMTP_FROM_NAME="Scribes App"

# Security
BCRYPT_ROUNDS=12  # Password hashing rounds
```

**Generate Secure JWT Secret:**
```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Output: 64-character hex string
```

---

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m -u 1000 scribes && chown -R scribes:scribes /app
USER scribes

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db:5432/scribes
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      REDIS_URL: redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: scribes
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass yourpassword
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

### Kubernetes Deployment

**Secret Management:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: scribes-secrets
type: Opaque
stringData:
  jwt-secret: "your-jwt-secret-key-here"
  smtp-password: "your-smtp-password"
  database-url: "postgresql+asyncpg://user:pass@db:5432/scribes"
```

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scribes-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scribes
  template:
    metadata:
      labels:
        app: scribes
    spec:
      containers:
      - name: app
        image: scribes:latest
        ports:
        - containerPort: 8000
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: scribes-secrets
              key: jwt-secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: scribes-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

### Monitoring

**Health Check Endpoint:**
```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-12-24T10:00:00Z"
}
```

**Monitor Authentication:**
```bash
# Count failed login attempts
grep "Login failed" /var/log/scribes/app.log | wc -l

# Monitor token generation
grep "Token generated" /var/log/scribes/app.log | tail -20

# Check for unauthorized access attempts
grep "401 Unauthorized" /var/log/scribes/app.log
```

---

## For Cloud Engineers

### AWS Deployment

**Secrets Manager:**
```bash
# Store JWT secret
aws secretsmanager create-secret \
  --name scribes/jwt-secret \
  --secret-string "your-jwt-secret-key"

# Store SMTP password
aws secretsmanager create-secret \
  --name scribes/smtp-password \
  --secret-string "your-smtp-password"

# Reference in ECS task definition
{
  "secrets": [
    {
      "name": "JWT_SECRET_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:scribes/jwt-secret"
    }
  ]
}
```

**Cognito Integration (Alternative):**
```python
# Replace custom JWT with AWS Cognito
import boto3

cognito = boto3.client('cognito-idp')

# User registration
response = cognito.sign_up(
    ClientId='your-app-client-id',
    Username='user@example.com',
    Password='SecurePass123!',
    UserAttributes=[
        {'Name': 'email', 'Value': 'user@example.com'}
    ]
)
```

---

### GCP Deployment

**Secret Manager:**
```bash
# Create secrets
gcloud secrets create jwt-secret --data-file=jwt_secret.txt
gcloud secrets create smtp-password --data-file=smtp_pass.txt

# Grant access to service account
gcloud secrets add-iam-policy-binding jwt-secret \
  --member="serviceAccount:scribes@project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Access in application
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = "projects/PROJECT_ID/secrets/jwt-secret/versions/latest"
response = client.access_secret_version(request={"name": name})
jwt_secret = response.payload.data.decode("UTF-8")
```

---

### Azure Deployment

**Key Vault:**
```bash
# Create Key Vault
az keyvault create \
  --name scribes-keyvault \
  --resource-group scribes-rg \
  --location eastus

# Store secrets
az keyvault secret set \
  --vault-name scribes-keyvault \
  --name jwt-secret \
  --value "your-jwt-secret-key"

# Grant access
az keyvault set-policy \
  --name scribes-keyvault \
  --object-id <app-service-principal-id> \
  --secret-permissions get list
```

**App Service Configuration:**
```bash
# Set environment variable from Key Vault
az webapp config appsettings set \
  --name scribes-app \
  --resource-group scribes-rg \
  --settings JWT_SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://scribes-keyvault.vault.azure.net/secrets/jwt-secret/)"
```

---

## API Reference

### Endpoints

#### 1. POST /auth/register
**Description:** Register new user

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "full_name": "John Doe"  // optional
}
```

**Responses:**
- `201 Created`: User created successfully
- `400 Bad Request`: Email/username already exists or invalid data
- `422 Unprocessable Entity`: Validation errors

---

#### 2. POST /auth/login
**Description:** Login with credentials

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Responses:**
- `200 OK`: Login successful, returns tokens
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account inactive or unverified

---

#### 3. POST /auth/refresh
**Description:** Refresh access token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Responses:**
- `200 OK`: New access token
- `401 Unauthorized`: Invalid or expired refresh token

---

#### 4. POST /auth/logout
**Description:** Logout (invalidate refresh token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Responses:**
- `200 OK`: Logout successful
- `401 Unauthorized`: Invalid token

---

#### 5. GET /auth/me
**Description:** Get current user info

**Headers:**
```
Authorization: Bearer <access_token>
```

**Responses:**
- `200 OK`: User information
- `401 Unauthorized`: Invalid token

---

#### 6. POST /auth/password-reset/request
**Description:** Request password reset

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Responses:**
- `200 OK`: Reset email sent (always returns 200 to prevent email enumeration)

---

#### 7. POST /auth/password-reset/confirm
**Description:** Confirm password reset

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

**Responses:**
- `200 OK`: Password reset successful
- `400 Bad Request`: Invalid or expired token

---

## Security Best Practices

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

**Frontend Validation:**
```dart
class PasswordValidator {
  static bool validate(String password) {
    final minLength = password.length >= 8;
    final hasUpper = password.contains(RegExp(r'[A-Z]'));
    final hasLower = password.contains(RegExp(r'[a-z]'));
    final hasNumber = password.contains(RegExp(r'\d'));
    final hasSpecial = password.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'));

    return minLength && hasUpper && hasLower && hasNumber && hasSpecial;
  }

  static String? getErrorMessage(String password) {
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!password.contains(RegExp(r'[A-Z]'))) return 'Password must contain an uppercase letter';
    if (!password.contains(RegExp(r'[a-z]'))) return 'Password must contain a lowercase letter';
    if (!password.contains(RegExp(r'\d'))) return 'Password must contain a number';
    if (!password.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'))) {
      return 'Password must contain a special character';
    }
    return null;
  }
}

// Usage in a TextField
TextField(
  obscureText: true,
  decoration: InputDecoration(
    labelText: 'Password',
    errorText: PasswordValidator.getErrorMessage(passwordController.text),
  ),
  onChanged: (value) {
    setState(() {
      // Trigger validation
    });
  },
)
```

---

### Token Storage

**✅ Recommended:**
- **flutter_secure_storage:** Most secure (encrypted keychain/keystore)
- **shared_preferences:** For non-sensitive data
- **hive (encrypted):** For offline-first apps

**❌ Avoid:**
- Storing tokens in plain text files
- Storing in unencrypted databases
- Logging tokens in console

**Secure Storage Example:**
```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureTokenStorage {
  static final _storage = FlutterSecureStorage();

  static Future<void> storeTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: 'access_token', value: accessToken);
    await _storage.write(key: 'refresh_token', value: refreshToken);
  }

  static Future<String?> getAccessToken() async {
    return await _storage.read(key: 'access_token');
  }

  static Future<String?> getRefreshToken() async {
    return await _storage.read(key: 'refresh_token');
  }

  static Future<void> clearTokens() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }
}
```

---

### HTTPS Only

**Always use HTTPS in production:**
```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name api.scribes.app;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
}
```

---

### Rate Limiting

**Prevent brute force attacks:**
```python
# Already implemented in rate_limiter.py
# /auth/login: 5 requests per minute per IP
# /auth/register: 3 requests per hour per IP
# /auth/password-reset: 3 requests per hour per IP
```

---

## Troubleshooting

### Issue: "Invalid credentials"

**Symptoms:**
- Login fails with 401
- Correct email/password combination

**Solutions:**
1. Check if user exists:
   ```sql
   SELECT * FROM users WHERE email = 'user@example.com';
   ```
2. Check if account is active:
   ```sql
   SELECT is_active, is_verified FROM users WHERE email = 'user@example.com';
   ```
3. Verify password hash:
   ```python
   from app.core.security import verify_password
   # Check if password matches hash
   ```

---

### Issue: "Token has expired"

**Symptoms:**
- 401 Unauthorized on API requests
- Token worked before

**Solutions:**
1. Check token expiration:
   ```python
   import jwt
   import base64
   
   # Decode token (don't verify)
   token = "your-token-here"
   payload = jwt.decode(token, options={"verify_signature": False})
   print(f"Expires at: {payload['exp']}")
   ```

2. Implement token refresh:
   ```typescript
   // Use refresh token to get new access token
   const refreshResponse = await fetch('/auth/refresh', {
     method: 'POST',
     body: JSON.stringify({ refresh_token: refreshToken })
   });
   ```

---

### Issue: "JWT decoding failed"

**Symptoms:**
- 401 Unauthorized immediately
- Token format looks correct

**Solutions:**
1. Check JWT secret matches:
   ```bash
   # Verify JWT_SECRET_KEY in .env matches backend
   ```

2. Check token format:
   ```
   Should be: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Not: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. Verify algorithm:
   ```python
   # Must match JWT_ALGORITHM in config
   # Default: HS256
   ```

---

### Issue: Password reset email not received

**Symptoms:**
- Request succeeds but no email

**Solutions:**
1. Check SMTP configuration:
   ```bash
   # Test SMTP connection
   python -c "
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print('SMTP connection successful')
   "
   ```

2. Check email logs:
   ```bash
   grep "Email sent" /var/log/scribes/app.log
   ```

3. Check spam folder

---

## Performance Metrics

### Target Response Times
- **Registration:** < 500ms
- **Login:** < 200ms
- **Token Refresh:** < 100ms
- **Token Validation:** < 50ms

### Benchmarks
```bash
# Load test with Apache Bench
ab -n 1000 -c 10 -T application/json -p login.json http://localhost:8000/auth/login

# Results should show:
# - 95th percentile: < 300ms
# - Failures: < 1%
```

---

## Summary

### Key Points
✅ **JWT-based authentication** with access/refresh tokens  
✅ **Bcrypt password hashing** for security  
✅ **Role-based access control** (Admin/User)  
✅ **Token refresh mechanism** for seamless UX  
✅ **Password reset flow** via email  
✅ **Production-ready** with Docker/K8s templates  

### Quick Commands
```bash
# Generate JWT secret
openssl rand -hex 32

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test authenticated endpoint
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
```

---

**Document Version:** 1.0  
**Last Updated:** December 24, 2025  
**Related Docs:** [API Documentation](./API_DOCUMENTATION_GUIDE.md) | [Rate Limiting](./RATE_LIMITING_GUIDE.md)
