# API Documentation

The Azure Firewall Manager provides a RESTful API accessible at:

```
https://<your-domain>/api/v1/
```

## Authentication

All API endpoints require authentication via JWT Bearer token:

```
Authorization: Bearer <token>
```

### Token Refresh

To refresh an expired access token:

```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

## Request/Response Format

### Content Types

- Requests: `application/json`
- Responses: `application/json`

### Pagination

List endpoints support pagination:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

### Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "status": 400
}
```

## Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/login | Authenticate user |
| POST | /auth/refresh | Refresh access token |
| POST | /auth/logout | Logout user |

#### Login Request

```json
{
  "email": "admin@example.com",
  "password": "your-password"
}
```

#### Login Response

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Firewall Rules

| Method | Path | Description |
|--------|------|-------------|
| GET | /firewalls/rules | List all rules |
| GET | /firewalls/rules/{id} | Get rule details |
| POST | /firewalls/rules | Create rule |
| PUT | /firewalls/rules/{id} | Update rule |
| DELETE | /firewalls/rules/{id} | Delete rule |

#### List Rules Request/Response

```
GET /api/v1/firewalls/rules?page=1&per_page=20&status=draft&landing_zone=dev
```

```json
{
  "items": [
    {
      "id": "rule-123",
      "name": "Allow HTTP Traffic",
      "status": "approved",
      "action": "allow",
      "priority": 100,
      "landing_zone": "dev",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

#### Create Rule Request

```json
{
  "name": "Allow HTTP Traffic",
  "rule_collection_name": "WebTraffic",
  "action": "allow",
  "priority": 100,
  "landing_zone": "dev",
  "destination_addresses": ["*"],
  "destination_ports": [80, 443],
  "destination_fqdns": ["*.example.com"]
}
```

#### Update Rule Request

```json
{
  "name": "Allow HTTP and HTTPS Traffic",
  "rule_collection_name": "WebTraffic",
  "action": "allow",
  "priority": 100,
  "destination_addresses": ["*"],
  "destination_ports": [80, 443],
  "destination_fqdns": ["*.example.com"],
  "notes": "Updated to include HTTPS"
}
```

### Approvals

| Method | Path | Description |
|--------|------|-------------|
| GET | /approvals | List approvals |
| POST | /approvals/{id}/action | Approve/reject |

#### List Approvals

```
GET /api/v1/approvals?status=pending&type=rule_creation
```

#### Approve/Reject Request

```json
{
  "action": "approve",
  "notes": "Looks good, ready for deployment"
}
```

### Statistics

| Method | Path | Description |
|--------|------|-------------|
| GET | /stats/dashboard | Get dashboard stats |
| GET | /stats/health | Health check with dependencies |

#### Dashboard Stats Response

```json
{
  "total_rules": 42,
  "pending_approvals": 5,
  "approved_rules": 12,
  "deployed_rules": 30,
  "by_status": {
    "draft": 3,
    "pending_approval": 5,
    "approved": 12,
    "deployed": 22,
    "rejected": 4,
    "deleted": 0
  },
  "by_landing_zone": {
    "dev": 15,
    "staging": 12,
    "prod": 15
  }
}
```

### Export

| Method | Path | Description |
|--------|------|-------------|
| GET | /export/rules.csv | Export rules as CSV |

#### CSV Export

Returns a CSV file with all firewall rules. Include headers:

```
ID,Name,Rule Collection,Action,Priority,Status,Landing Zone,Destinations,Dest Ports,FQDNs,Created By,Created At
```

## Interactive Documentation

OpenAPI/Swagger UI is available at:
- Development: http://localhost:8000/api/docs
- Staging: https://staging.example.com/api/docs
- Production: https://api.example.com/api/docs