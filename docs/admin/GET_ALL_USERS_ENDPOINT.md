# Get All Users Endpoint

## Overview
A new endpoint has been added to fetch all users from the database with pagination and filtering capabilities.

## Endpoint Details

### URL
```
GET /auth/users
```

### Authentication
**Required**: Yes (Bearer token)

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip for pagination |
| `limit` | integer | 100 | Maximum number of records to return (max: 100) |
| `is_active` | boolean | null | Filter by active status (optional) |

### Response Schema

```json
{
  "users": [
    {
      "email": "string",
      "username": "string",
      "full_name": "string",
      "id": 0,
      "role": "string",
      "is_active": true,
      "is_verified": true,
      "created_at": "2025-10-31T00:00:00Z",
      "updated_at": "2025-10-31T00:00:00Z"
    }
  ],
  "total": 0,
  "skip": 0,
  "limit": 100
}
```

## Usage Examples

### 1. Get all users (first 100)
```bash
curl -X GET "http://localhost:8000/auth/users" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. Get users with pagination
```bash
# Get second page (skip 100, get next 50)
curl -X GET "http://localhost:8000/auth/users?skip=100&limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Get only active users
```bash
curl -X GET "http://localhost:8000/auth/users?is_active=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Get only inactive users
```bash
curl -X GET "http://localhost:8000/auth/users?is_active=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Get active users with pagination
```bash
curl -X GET "http://localhost:8000/auth/users?is_active=true&skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing in Swagger UI

1. Navigate to http://localhost:8000/docs
2. Click on the **Authentication** section
3. Find the **GET /auth/users** endpoint
4. Click **Try it out**
5. Enter your access token by clicking **Authorize** at the top
6. Optionally adjust the query parameters:
   - `skip`: Set to 0 for first page
   - `limit`: Set how many users to fetch (max 100)
   - `is_active`: Leave empty for all users, or set to true/false
7. Click **Execute**

## Response Details

### Success Response (200 OK)
Returns a `UserListResponse` object containing:
- **users**: Array of user objects (without sensitive data like passwords)
- **total**: Total number of users matching the filter
- **skip**: The skip value used in the request
- **limit**: The limit value used in the request

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```
**Cause**: Missing or invalid access token

#### 403 Forbidden
```json
{
  "detail": "Account is inactive"
}
```
**Cause**: User account is deactivated

## Implementation Details

### Repository Method
Uses `UserRepository.list_users()` and `UserRepository.count_users()` methods for efficient database queries.

### Security
- Requires authentication (Bearer token)
- No special permissions required (any authenticated user can view user list)
- Sensitive data (passwords) is excluded from response

### Performance
- **Pagination**: Prevents loading entire user table into memory
- **Limit cap**: Maximum 100 users per request to prevent abuse
- **Filtering**: Optional `is_active` filter reduces result set
- **Efficient queries**: Uses SQLAlchemy's `offset()` and `limit()` for database-level pagination

## Related Endpoints

- **POST /auth/register** - Register new user
- **GET /auth/me** - Get current user profile
- **PUT /auth/me** - Update current user profile
- **DELETE /auth/me** - Delete current user account

## Future Enhancements

Potential improvements for this endpoint:

1. **Role-based access**: Restrict to admin users only
2. **Search functionality**: Add query parameter to search by username/email
3. **Sorting**: Add parameter to sort by created_at, username, etc.
4. **More filters**: Filter by role, is_verified, etc.
5. **Partial response**: Allow selecting specific fields to return
6. **Caching**: Implement Redis caching for frequently accessed pages

## Database Schema

The endpoint queries the `users` table with the following relevant fields:
- `id`: Primary key
- `email`: User email (unique, indexed)
- `username`: Username (unique, indexed)
- `full_name`: User's full name
- `role`: User role (user, admin)
- `is_active`: Account active status
- `is_verified`: Email verification status
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp (optional/nullable)

## Notes

- The `updated_at` field may be `null` for newly created users (only populated after first update)
- User passwords are never included in the response
- The endpoint respects the application's authentication and session management
