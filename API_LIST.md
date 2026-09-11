# API List

This project exposes the following Django REST API endpoints.

Base URL pattern:
- http://localhost:8000/api/...

## 1) Account APIs

### POST /api/accounts/register/
- Method: POST
- Authentication: Public
- Required data:
  - username: string
  - email: string
  - password: string (minimum 6 characters)
- Success response (201):
  ```json
  {
    "message": "User registered successfully",
    "user": {
      "id": 1,
      "username": "john",
      "email": "john@example.com",
      "is_staff": false,
      "is_superuser": false
    },
    "tokens": {
      "refresh": "<refresh-token>",
      "access": "<access-token>"
    }
  }
  ```

### POST /api/accounts/login/
- Method: POST
- Authentication: Public
- Required data:
  - username: string
  - password: string
- Success response (200):
  ```json
  {
    "message": "Login successful",
    "user": {
      "id": 1,
      "username": "john",
      "email": "john@example.com",
      "is_staff": false,
      "is_superuser": false
    },
    "tokens": {
      "refresh": "<refresh-token>",
      "access": "<access-token>"
    }
  }
  ```

### GET /api/accounts/profile/
- Method: GET
- Authentication: Required (Authenticated user)
- Success response (200):
  ```json
  {
    "user": {
      "id": 1,
      "username": "john",
      "email": "john@example.com",
      "is_staff": false,
      "is_superuser": false
    }
  }
  ```

### POST /api/accounts/logout/
- Method: POST
- Authentication: Required (Authenticated user)
- Required data:
  - refresh: string (refresh token)
- Success response (200):
  ```json
  {
    "message": "Logout successful"
  }
  ```
- Error response (400):
  ```json
  {
    "error": "Invalid refresh token"
  }
  ```

---

## 2) Notification Trigger APIs

### GET /api/notifications/triggers/
- Method: GET
- Authentication: Required (Authenticated + Admin)
- Success response (200):
  ```json
  [
    {
      "id": 1,
      "name": "Welcome Trigger",
      "key": "welcome",
      "description": "Sent when a user joins",
      "is_active": true,
      "templates": [
        {
          "id": 1,
          "trigger": 1,
          "channel": "email",
          "name": "Welcome Email",
          "subject": "Welcome!",
          "title": "Welcome",
          "body": "Hello {{name}}",
          "is_enabled": true,
          "variable_mapping": {},
          "created_by": 1,
          "created_at": "2026-09-11T12:00:00Z",
          "updated_at": "2026-09-11T12:00:00Z"
        }
      ],
      "created_at": "2026-09-11T12:00:00Z",
      "updated_at": "2026-09-11T12:00:00Z"
    }
  ]
  ```

### POST /api/notifications/triggers/
- Method: POST
- Authentication: Required (Authenticated + Admin)
- Required data:
  - name: string
  - key: string (unique slug)
  - description: string (optional)
  - is_active: boolean (optional, default true)
- Success response (201):
  ```json
  {
    "id": 1,
    "name": "Welcome Trigger",
    "key": "welcome",
    "description": "Sent when a user joins",
    "is_active": true,
    "templates": [],
    "created_at": "2026-09-11T12:00:00Z",
    "updated_at": "2026-09-11T12:00:00Z"
  }
  ```

### GET /api/notifications/triggers/{id}/
- Method: GET
- Authentication: Required (Authenticated + Admin)
- Success response (200): trigger object

### PUT /api/notifications/triggers/{id}/
- Method: PUT
- Authentication: Required (Authenticated + Admin)
- Required data:
  - name: string
  - key: string
  - description: string
  - is_active: boolean
- Success response (200): trigger object

### PATCH /api/notifications/triggers/{id}/
- Method: PATCH
- Authentication: Required (Authenticated + Admin)
- Optional data:
  - name: string
  - key: string
  - description: string
  - is_active: boolean
- Success response (200): updated trigger object

### DELETE /api/notifications/triggers/{id}/
- Method: DELETE
- Authentication: Required (Authenticated + Admin)
- Success response (200):
  ```json
  {
    "message": "Trigger deleted successfully"
  }
  ```

---

## 3) Notification Template APIs

### GET /api/notifications/templates/
- Method: GET
- Authentication: Required (Authenticated + Admin)
- Success response (200):
  ```json
  [
    {
      "id": 1,
      "trigger": 1,
      "channel": "email",
      "name": "Welcome Email",
      "subject": "Welcome!",
      "title": "Welcome",
      "body": "Hello {{name}}",
      "is_enabled": true,
      "variable_mapping": {},
      "created_by": 1,
      "created_at": "2026-09-11T12:00:00Z",
      "updated_at": "2026-09-11T12:00:00Z"
    }
  ]
  ```

### POST /api/notifications/templates/
- Method: POST
- Authentication: Required (Authenticated + Admin)
- Required data:
  - trigger: integer (trigger id)
  - channel: string
    - allowed values: whatsapp, email, web_push
  - name: string
  - subject: string (optional, blank allowed)
  - title: string (optional, blank allowed)
  - body: string
  - is_enabled: boolean (optional, default true)
  - variable_mapping: object (optional, default {})
- Success response (201): created template object

### GET /api/notifications/templates/{id}/
- Method: GET
- Authentication: Required (Authenticated + Admin)
- Success response (200): template object

### PUT /api/notifications/templates/{id}/
- Method: PUT
- Authentication: Required (Authenticated + Admin)
- Required data:
  - trigger: integer
  - channel: string
  - name: string
  - subject: string
  - title: string
  - body: string
  - is_enabled: boolean
  - variable_mapping: object
- Success response (200): updated template object

### PATCH /api/notifications/templates/{id}/
- Method: PATCH
- Authentication: Required (Authenticated + Admin)
- Optional data:
  - trigger: integer
  - channel: string
  - name: string
  - subject: string
  - title: string
  - body: string
  - is_enabled: boolean
  - variable_mapping: object
- Success response (200): updated template object

### DELETE /api/notifications/templates/{id}/
- Method: DELETE
- Authentication: Required (Authenticated + Admin)
- Success response (200):
  ```json
  {
    "message": "Template deleted successfully"
  }
  ```

### PATCH /api/notifications/templates/{id}/toggle/
- Method: PATCH
- Authentication: Required (Authenticated + Admin)
- No request body required
- Success response (200):
  ```json
  {
    "message": "Template status updated",
    "id": 1,
    "channel": "email",
    "is_enabled": false
  }
  ```

### POST /api/notifications/templates/{id}/test/
- Method: POST
- Authentication: Required (Authenticated + Admin)
- Optional data:
  - context: object
- Success response (200):
  ```json
  {
    "message": "Test notification sent",
    "template_id": 1,
    "channel": "email",
    "status": "success",
    "provider": "<provider>",
    "details": {
      "status": "success",
      "provider": "<provider>",
      "message": "sent"
    }
  }
  ```
- Error response (400):
  ```json
  {
    "error": "<validation error message>",
    "template_id": 1,
    "channel": "email",
    "status": "failed"
  }
  ```

---

## 4) Trigger Fire API

### POST /api/notifications/fire/
- Method: POST
- Authentication: Required (Authenticated user)
- Required data:
  - trigger: string (trigger key)
  - context: object (optional, default {})
- Success response (200):
  ```json
  {
    "trigger": "welcome",
    "message": "Trigger fired successfully",
    "notifications": [
      {
        "channel": "email",
        "template_id": 1,
        "status": "success",
        "context": {
          "name": "John"
        },
        "details": {
          "status": "success",
          "provider": "<provider>",
          "message": "sent"
        }
      }
    ]
  }
  ```
- Error response (400):
  ```json
  {
    "error": "trigger is required"
  }
  ```

---

## 5) Data Models Used by the APIs

### Trigger
```json
{
  "id": 1,
  "name": "Welcome Trigger",
  "key": "welcome",
  "description": "Sent when a user joins",
  "is_active": true,
  "created_at": "2026-09-11T12:00:00Z",
  "updated_at": "2026-09-11T12:00:00Z"
}
```

### NotificationTemplate
```json
{
  "id": 1,
  "trigger": 1,
  "channel": "email",
  "name": "Welcome Email",
  "subject": "Welcome!",
  "title": "Welcome",
  "body": "Hello {{name}}",
  "is_enabled": true,
  "variable_mapping": {},
  "created_by": 1,
  "created_at": "2026-09-11T12:00:00Z",
  "updated_at": "2026-09-11T12:00:00Z"
}
```

### User
```json
{
  "id": 1,
  "username": "john",
  "email": "john@example.com",
  "is_staff": false,
  "is_superuser": false
}
```

---

## 6) Permissions Summary
- Public endpoints: register, login
- Authenticated endpoints: profile, logout, fire trigger
- Admin-only endpoints: all trigger and template management, test template, toggle template
