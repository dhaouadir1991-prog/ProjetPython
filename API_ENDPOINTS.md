# API Endpoints Documentation

## Base URL
```
http://127.0.0.1:8000
```

## 🛡️ Content Moderation Endpoint

### POST `/moderate`
Analyze content for inappropriate material and save alert if detected.

**Request Body:**
```json
{
  "text": "The content to analyze",
  "url": "https://example.com",
  "deviceInfo": {
    "publicIP": "203.0.113.25",
    "userAgent": "Mozilla/5.0...",
    "platform": "MacIntel",
    "screenWidth": 1920,
    "screenHeight": 1080,
    "timezone": "Europe/Paris",
    "language": "fr",
    "timestamp": "2025-12-16T10:30:00Z"
  }
}
```

**Response (Alert Not Triggered):**
```json
{
  "non_adequate": false,
  "scores": [
    {
      "label": "toxicity",
      "score": 0.05
    }
  ]
}
```

**Response (Alert Triggered):**
```json
{
  "non_adequate": true,
  "scores": [
    {
      "label": "toxicity",
      "score": 0.92
    }
  ]
}
```

---

## 📊 Data Retrieval Endpoints

### GET `/alerts`
Retrieve all alerts with pagination.

**Query Parameters:**
- `limit` (int, default: 50): Number of results to return
- `offset` (int, default: 0): Number of results to skip

**Example:**
```
GET /alerts?limit=20&offset=0
```

**Response:**
```json
{
  "status": "success",
  "total": 150,
  "limit": 20,
  "offset": 0,
  "alerts": [
    {
      "id": 1,
      "url": "https://reddit.com/r/example",
      "detected_text": "inappropriate content...",
      "ip_address": "203.0.113.25",
      "browser_info": "Mozilla/5.0...",
      "platform": "MacIntel",
      "screen_resolution": "1920x1080",
      "timezone": "Europe/Paris",
      "language": "fr",
      "timestamp": "2025-12-16 10:30:00",
      "created_at": "2025-12-16 10:30:05",
      "device_info_json": {...},
      "scores_json": {...}
    }
  ]
}
```

---

### GET `/alerts/ip/{ip_address}`
Get alerts filtered by IP address.

**Parameters:**
- `ip_address` (string): The IP address to filter by
- `limit` (int, default: 50): Number of results to return

**Example:**
```
GET /alerts/ip/203.0.113.25?limit=50
```

**Response:**
```json
{
  "status": "success",
  "ip_address": "203.0.113.25",
  "count": 5,
  "alerts": [...]
}
```

---

### GET `/alerts/date/{date}`
Get alerts for a specific date.

**Parameters:**
- `date` (string, format: YYYY-MM-DD): The date to filter by
- `limit` (int, default: 50): Number of results to return

**Example:**
```
GET /alerts/date/2025-12-16?limit=50
```

**Response:**
```json
{
  "status": "success",
  "date": "2025-12-16",
  "count": 8,
  "alerts": [...]
}
```

---

### GET `/alerts/url`
Search alerts by URL (partial matching).

**Query Parameters:**
- `url` (string): Part of URL to search for
- `limit` (int, default: 50): Number of results to return

**Example:**
```
GET /alerts/url?url=reddit.com&limit=50
```

**Response:**
```json
{
  "status": "success",
  "search_url": "reddit.com",
  "count": 12,
  "alerts": [...]
}
```

---

### GET `/alerts/{alert_id}`
Get detailed information about a specific alert.

**Parameters:**
- `alert_id` (int): The ID of the alert

**Example:**
```
GET /alerts/42
```

**Response:**
```json
{
  "status": "success",
  "alert": {
    "id": 42,
    "url": "https://example.com",
    "detected_text": "inappropriate content text...",
    "ip_address": "203.0.113.25",
    "browser_info": "Mozilla/5.0...",
    "platform": "MacIntel",
    "screen_resolution": "1920x1080",
    "timezone": "Europe/Paris",
    "language": "fr",
    "timestamp": "2025-12-16 10:30:00",
    "created_at": "2025-12-16 10:30:05",
    "device_info_json": {
      "publicIP": "203.0.113.25",
      "userAgent": "Mozilla/5.0...",
      "screenWidth": 1920,
      "screenHeight": 1080,
      "timezone": "Europe/Paris",
      "language": "fr",
      "timestamp": "2025-12-16T10:30:00Z"
    },
    "scores_json": [
      {
        "label": "toxicity",
        "score": 0.92
      }
    ]
  }
}
```

---

### GET `/alerts/stats`
Get comprehensive statistics about all alerts.

**Example:**
```
GET /alerts/stats
```

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_alerts": 150,
    "top_ips": [
      {
        "ip_address": "203.0.113.25",
        "count": 23
      },
      {
        "ip_address": "198.51.100.50",
        "count": 18
      }
    ],
    "top_problematic_sites": [
      {
        "url": "https://reddit.com/r/inappropriate",
        "count": 12
      },
      {
        "url": "https://example.com/adult",
        "count": 8
      }
    ],
    "alerts_by_platform": [
      {
        "platform": "MacIntel",
        "count": 85
      },
      {
        "platform": "Win32",
        "count": 65
      }
    ],
    "last_7_days": [
      {
        "date": "2025-12-16",
        "count": 15
      },
      {
        "date": "2025-12-15",
        "count": 12
      }
    ]
  }
}
```

---

## 🗑️ Delete Endpoint

### DELETE `/alerts/{alert_id}`
Delete an alert from the database.

**Parameters:**
- `alert_id` (int): The ID of the alert to delete

**Example:**
```
DELETE /alerts/42
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Alert 42 deleted successfully"
}
```

**Response (Not Found):**
```json
{
  "error": "Alert not found",
  "status": "not_found"
}
```

---

## 📱 Example Requests Using cURL

### Check all alerts
```bash
curl http://127.0.0.1:8000/alerts
```

### Get alerts from specific IP
```bash
curl http://127.0.0.1:8000/alerts/ip/203.0.113.25
```

### Get alerts for today
```bash
curl "http://127.0.0.1:8000/alerts/date/2025-12-16"
```

### Search by URL
```bash
curl "http://127.0.0.1:8000/alerts/url?url=reddit"
```

### Get statistics
```bash
curl http://127.0.0.1:8000/alerts/stats
```

### Get specific alert
```bash
curl http://127.0.0.1:8000/alerts/42
```

### Delete an alert
```bash
curl -X DELETE http://127.0.0.1:8000/alerts/42
```

---

## 📝 Python Client Examples

### Get all alerts
```python
import requests

response = requests.get('http://127.0.0.1:8000/alerts')
alerts = response.json()
print(alerts)
```

### Get alerts from IP
```python
ip = "203.0.113.25"
response = requests.get(f'http://127.0.0.1:8000/alerts/ip/{ip}')
alerts = response.json()
print(f"Alerts from {ip}: {alerts['count']}")
```

### Get statistics
```python
response = requests.get('http://127.0.0.1:8000/alerts/stats')
stats = response.json()
print(f"Total alerts: {stats['statistics']['total_alerts']}")
```

---

## 🌐 FastAPI Auto-Documentation

Access interactive API documentation at:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Description of error",
  "status": "error"
}
```

Common errors:
- `Database connection failed` - MySQL server not running
- `Alert not found` - Alert ID doesn't exist
- Invalid date format - Use YYYY-MM-DD
