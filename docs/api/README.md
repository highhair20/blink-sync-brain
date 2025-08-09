# API Documentation

This document provides comprehensive API documentation for the Blink Sync Brain system, including all endpoints, request/response examples, and integration guides.

## 🔌 API Overview

The Blink Sync Brain API provides RESTful endpoints for brain signal processing, classification, and synchronization across multiple interfaces.

![API Overview](./images/api-overview.png)

*Figure 1: API architecture and endpoint structure overview*

### Base URL
```
Production: https://api.blinksyncbrain.com/v1
Development: http://localhost:3000/api/v1
```

### Authentication
All API requests require authentication using Bearer tokens in the Authorization header:
```
Authorization: Bearer <your-access-token>
```

## 📊 Signal Processing Endpoints

### POST /signals/process

Process raw brain signals and extract features.

![Signal Processing](./images/signal-processing-endpoint.png)

*Figure 2: Signal processing endpoint request/response flow*

**Request Body:**
```json
{
  "signals": {
    "channel_1": [0.1, 0.2, 0.3, ...],
    "channel_2": [0.15, 0.25, 0.35, ...],
    "channel_3": [0.12, 0.22, 0.32, ...],
    "channel_4": [0.18, 0.28, 0.38, ...]
  },
  "metadata": {
    "sample_rate": 1000,
    "timestamp": "2024-01-15T10:30:00Z",
    "device_id": "sensor_001",
    "session_id": "session_123"
  },
  "processing_options": {
    "filter_type": "bandpass",
    "frequency_range": [1, 40],
    "window_size": 1024,
    "overlap": 0.5
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "processed_signals": {
      "channel_1": [0.08, 0.18, 0.28, ...],
      "channel_2": [0.13, 0.23, 0.33, ...],
      "channel_3": [0.10, 0.20, 0.30, ...],
      "channel_4": [0.16, 0.26, 0.36, ...]
    },
    "features": {
      "frequency_domain": {
        "alpha_power": [0.45, 0.52, 0.38, ...],
        "beta_power": [0.23, 0.31, 0.28, ...],
        "theta_power": [0.12, 0.18, 0.15, ...],
        "delta_power": [0.08, 0.11, 0.09, ...]
      },
      "time_domain": {
        "mean": [0.15, 0.18, 0.16, ...],
        "variance": [0.023, 0.031, 0.028, ...],
        "skewness": [0.12, 0.08, 0.15, ...],
        "kurtosis": [2.8, 3.1, 2.9, ...]
      }
    },
    "quality_metrics": {
      "signal_to_noise_ratio": 15.6,
      "artifact_detection": false,
      "channel_connectivity": 0.95,
      "baseline_stability": 0.92
    }
  },
  "processing_time": 0.045,
  "timestamp": "2024-01-15T10:30:01Z"
}
```

### GET /signals/quality

Get real-time signal quality metrics.

![Signal Quality](./images/signal-quality-endpoint.png)

*Figure 3: Signal quality monitoring endpoint*

**Query Parameters:**
- `session_id` (required): Session identifier
- `time_window` (optional): Time window in seconds (default: 60)

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session_123",
    "quality_metrics": {
      "overall_quality": 0.87,
      "channel_quality": {
        "channel_1": 0.92,
        "channel_2": 0.85,
        "channel_3": 0.89,
        "channel_4": 0.82
      },
      "signal_to_noise_ratio": 14.2,
      "artifact_count": 3,
      "connection_stability": 0.94
    },
    "recommendations": [
      "Check channel 4 connection",
      "Reduce environmental noise",
      "Verify sensor placement"
    ],
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 🎯 Classification Endpoints

### POST /classify/brain-state

Classify current brain state based on processed signals.

![Brain State Classification](./images/brain-state-classification-endpoint.png)

*Figure 4: Brain state classification endpoint with confidence scores*

**Request Body:**
```json
{
  "features": {
    "frequency_domain": {
      "alpha_power": [0.45, 0.52, 0.38],
      "beta_power": [0.23, 0.31, 0.28],
      "theta_power": [0.12, 0.18, 0.15],
      "delta_power": [0.08, 0.11, 0.09]
    },
    "time_domain": {
      "mean": [0.15, 0.18, 0.16],
      "variance": [0.023, 0.031, 0.028],
      "skewness": [0.12, 0.08, 0.15],
      "kurtosis": [2.8, 3.1, 2.9]
    }
  },
  "model_version": "v2.1.0",
  "classification_options": {
    "confidence_threshold": 0.8,
    "include_probabilities": true,
    "temporal_smoothing": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "brain_state": "focused_attention",
    "confidence": 0.87,
    "probabilities": {
      "focused_attention": 0.87,
      "relaxed": 0.08,
      "drowsy": 0.03,
      "agitated": 0.02
    },
    "features_used": [
      "alpha_power_ratio",
      "beta_theta_ratio",
      "spectral_entropy",
      "coherence_measures"
    ],
    "classification_metadata": {
      "model_version": "v2.1.0",
      "processing_time": 0.023,
      "feature_count": 24,
      "temporal_window": 2.0
    },
    "timestamp": "2024-01-15T10:30:02Z"
  }
}
```

### GET /classify/history

Get historical brain state classifications.

![Classification History](./images/classification-history-endpoint.png)

*Figure 5: Historical classification data retrieval*

**Query Parameters:**
- `session_id` (required): Session identifier
- `start_time` (optional): Start timestamp (ISO 8601)
- `end_time` (optional): End timestamp (ISO 8601)
- `limit` (optional): Number of records (default: 100)

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session_123",
    "classifications": [
      {
        "timestamp": "2024-01-15T10:29:58Z",
        "brain_state": "focused_attention",
        "confidence": 0.85,
        "probabilities": {
          "focused_attention": 0.85,
          "relaxed": 0.10,
          "drowsy": 0.03,
          "agitated": 0.02
        }
      },
      {
        "timestamp": "2024-01-15T10:29:56Z",
        "brain_state": "focused_attention",
        "confidence": 0.82,
        "probabilities": {
          "focused_attention": 0.82,
          "relaxed": 0.12,
          "drowsy": 0.04,
          "agitated": 0.02
        }
      }
    ],
    "summary": {
      "total_classifications": 150,
      "most_common_state": "focused_attention",
      "average_confidence": 0.84,
      "state_distribution": {
        "focused_attention": 0.75,
        "relaxed": 0.15,
        "drowsy": 0.08,
        "agitated": 0.02
      }
    }
  }
}
```

## 🔄 Synchronization Endpoints

### POST /sync/interface

Synchronize brain state data across multiple interfaces.

![Interface Synchronization](./images/interface-sync-endpoint.png)

*Figure 6: Multi-interface synchronization endpoint*

**Request Body:**
```json
{
  "session_id": "session_123",
  "brain_state": {
    "state": "focused_attention",
    "confidence": 0.87,
    "timestamp": "2024-01-15T10:30:02Z"
  },
  "target_interfaces": [
    "visual_display",
    "audio_feedback",
    "haptic_device",
    "external_api"
  ],
  "sync_options": {
    "latency_compensation": true,
    "conflict_resolution": "highest_confidence",
    "retry_attempts": 3,
    "timeout": 5000
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "sync_id": "sync_456",
    "session_id": "session_123",
    "sync_status": {
      "visual_display": {
        "status": "synced",
        "latency": 45,
        "timestamp": "2024-01-15T10:30:02.045Z"
      },
      "audio_feedback": {
        "status": "synced",
        "latency": 52,
        "timestamp": "2024-01-15T10:30:02.052Z"
      },
      "haptic_device": {
        "status": "synced",
        "latency": 38,
        "timestamp": "2024-01-15T10:30:02.038Z"
      },
      "external_api": {
        "status": "synced",
        "latency": 67,
        "timestamp": "2024-01-15T10:30:02.067Z"
      }
    },
    "overall_status": "success",
    "average_latency": 50.5,
    "conflicts_resolved": 0,
    "timestamp": "2024-01-15T10:30:02Z"
  }
}
```

### GET /sync/status

Get synchronization status across all interfaces.

![Sync Status](./images/sync-status-endpoint.png)

*Figure 7: Real-time synchronization status monitoring*

**Query Parameters:**
- `session_id` (required): Session identifier
- `interface_id` (optional): Specific interface ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session_123",
    "interfaces": [
      {
        "interface_id": "visual_display",
        "status": "connected",
        "last_sync": "2024-01-15T10:30:02Z",
        "latency": 45,
        "error_count": 0,
        "sync_quality": 0.95
      },
      {
        "interface_id": "audio_feedback",
        "status": "connected",
        "last_sync": "2024-01-15T10:30:02Z",
        "latency": 52,
        "error_count": 1,
        "sync_quality": 0.92
      },
      {
        "interface_id": "haptic_device",
        "status": "disconnected",
        "last_sync": "2024-01-15T10:29:45Z",
        "latency": null,
        "error_count": 3,
        "sync_quality": 0.0
      }
    ],
    "overall_status": "partial",
    "connected_count": 2,
    "total_count": 3,
    "average_latency": 48.5,
    "timestamp": "2024-01-15T10:30:05Z"
  }
}
```

## 📊 Analytics Endpoints

### GET /analytics/performance

Get system performance analytics.

![Performance Analytics](./images/performance-analytics-endpoint.png)

*Figure 8: System performance analytics and metrics*

**Query Parameters:**
- `time_range` (optional): Time range in hours (default: 24)
- `metrics` (optional): Comma-separated metric names

**Response:**
```json
{
  "status": "success",
  "data": {
    "time_range": "24h",
    "performance_metrics": {
      "processing_latency": {
        "average": 0.045,
        "p95": 0.078,
        "p99": 0.123,
        "min": 0.023,
        "max": 0.156
      },
      "classification_accuracy": {
        "overall": 0.87,
        "by_state": {
          "focused_attention": 0.92,
          "relaxed": 0.85,
          "drowsy": 0.78,
          "agitated": 0.81
        }
      },
      "sync_performance": {
        "average_latency": 48.5,
        "success_rate": 0.94,
        "error_rate": 0.06,
        "conflict_rate": 0.02
      },
      "system_utilization": {
        "cpu_usage": 0.35,
        "memory_usage": 0.42,
        "network_throughput": 1.2,
        "disk_io": 0.15
      }
    },
    "trends": {
      "processing_latency_trend": [0.042, 0.045, 0.048, 0.044, 0.046],
      "accuracy_trend": [0.85, 0.87, 0.86, 0.88, 0.87],
      "sync_latency_trend": [45, 48, 52, 47, 49]
    },
    "alerts": [
      {
        "type": "high_latency",
        "message": "Processing latency above threshold",
        "severity": "warning",
        "timestamp": "2024-01-15T10:25:00Z"
      }
    ],
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 🔐 Authentication Endpoints

### POST /auth/login

Authenticate user and get access token.

![Authentication](./images/authentication-endpoint.png)

*Figure 9: User authentication and token generation*

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "secure_password",
  "device_id": "device_001"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "user_id": "user_123",
      "username": "user@example.com",
      "permissions": ["read", "write", "admin"],
      "session_limit": 10
    }
  }
}
```

### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

## 🚨 Error Handling

### Error Response Format

![Error Handling](./images/error-handling.png)

*Figure 10: Standard error response format and codes*

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "signals",
      "issue": "Missing required field"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_789"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## 📚 SDK and Libraries

### Available SDKs

![SDK Libraries](./images/sdk-libraries.png)

*Figure 11: Available SDK libraries and integration examples*

**Official SDKs:**
- **Python SDK**: `pip install blinksyncbrain-sdk`
- **JavaScript SDK**: `npm install @blinksyncbrain/sdk`
- **Java SDK**: Available via Maven Central
- **C# SDK**: Available via NuGet

### Python SDK Example

```python
from blinksyncbrain import BlinkSyncBrain

# Initialize client
client = BlinkSyncBrain(api_key="your-api-key")

# Process signals
response = client.signals.process(
    signals=signal_data,
    metadata=metadata,
    processing_options=options
)

# Classify brain state
classification = client.classify.brain_state(
    features=response.features,
    model_version="v2.1.0"
)

# Synchronize across interfaces
sync_result = client.sync.interface(
    session_id="session_123",
    brain_state=classification,
    target_interfaces=["visual_display", "audio_feedback"]
)
```

## 📈 Rate Limits

### Rate Limiting

![Rate Limits](./images/rate-limits.png)

*Figure 12: API rate limiting and quota management*

**Rate Limits:**
- **Free Tier**: 1,000 requests/hour
- **Pro Tier**: 10,000 requests/hour
- **Enterprise**: Custom limits

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 850
X-RateLimit-Reset: 1642248000
```

---

*For detailed setup instructions, see the [Setup Guide](../setup/README.md). For troubleshooting, see the [Troubleshooting Guide](../troubleshooting/README.md).* 