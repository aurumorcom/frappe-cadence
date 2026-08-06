# Callback Data Models & Webhook Payload Specifications

This document defines the data models and payload contracts for outbound webhook requests sent to AI engines (Sift / n8n) and inbound callback responses received by `frappe_cadence`.

---

## Standard Webhook Envelope Rule

All outbound task dispatches to external AI services (Sift / n8n) follow the unified webhook envelope specification:
- **`background`**: Boolean (`true`) indicating asynchronous execution.
- **`webhook`**: Object containing callback instructions:
  - **`url`**: The callback endpoint URL hosted on Frappe.
  - **`events`**: List of subscribed completion events (`["completed", "failed"]`).
  - **`metadata`**: Contextual dictionary passed to the AI engine and echoed back verbatim in the callback payload.
- **`response_format`**: JSON schema detailing the required output structure.
- **`input`**: Conversation history messages and prompt context.
- **`model`**: AI model identifier string.

> **CRITICAL**: Metadata MUST exist ONLY inside `webhook.metadata` (`body.webhook.metadata`). Top-level `metadata` (`body.metadata`) is NOT present in outbound generation requests.

---

## Template Channel Callback Specifications

### 1. Email Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.email_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:97)

#### Outbound Dispatch Payload (`POST` to n8n / Sift)
```json
{
  "background": true,
  "model": "gemini/gemini-3.5-flash-lite",
  "webhook": {
    "url": "https://<your-site>/api/method/frappe_cadence.email_template.callback",
    "events": [
      "completed",
      "failed"
    ],
    "metadata": {
      "name": "COMM-00001"
    }
  },
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "communication_generation",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "subject": {
            "type": "string",
            "description": "The subject line of the email"
          },
          "content": {
            "type": "string",
            "description": "The main body content of the email"
          }
        },
        "required": [
          "subject",
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "input": [
    {
      "role": "user",
      "content": "Sender Name: Alex Smith\nSender Bio:\nAccount Executive..."
    }
  ]
}
```

#### Inbound Callback Response (`POST` from n8n / Sift)
```json
{
  "type": "response.completed",
  "metadata": {
    "name": "COMM-00001"
  },
  "data": [
    {
      "content": [
        {
          "type": "text",
          "text": "{\"subject\": \"Quick question regarding your growth strategy\", \"content\": \"Hi John,\\n\\nI noticed...\"}"
        }
      ]
    }
  ]
}
```

---

### 2. SMS Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.sms_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:97)

#### Outbound Dispatch Payload
```json
{
  "background": true,
  "model": "gemini/gemini-3.5-flash-lite",
  "webhook": {
    "url": "https://<your-site>/api/method/frappe_cadence.sms_template.callback",
    "events": [
      "completed",
      "failed"
    ],
    "metadata": {
      "name": "COMM-00002"
    }
  },
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "communication_generation",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "content": {
            "type": "string",
            "description": "The main body content of the message"
          }
        },
        "required": [
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "input": [...]
}
```

#### Inbound Callback Response
```json
{
  "type": "response.completed",
  "metadata": {
    "name": "COMM-00002"
  },
  "data": [
    {
      "content": [
        {
          "type": "text",
          "text": "{\"content\": \"Hi John, following up on our email yesterday. Are you available for a brief call?\"}"
        }
      ]
    }
  ]
}
```

---

### 3. WhatsApp Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.whatsapp_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:97)

#### Outbound Dispatch Payload
```json
{
  "background": true,
  "model": "gemini/gemini-3.5-flash-lite",
  "webhook": {
    "url": "https://<your-site>/api/method/frappe_cadence.whatsapp_template.callback",
    "events": [
      "completed",
      "failed"
    ],
    "metadata": {
      "name": "COMM-00003"
    }
  },
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "communication_generation",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "content": {
            "type": "string",
            "description": "The main body content of the message"
          }
        },
        "required": [
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "input": [...]
}
```

---

### 4. LinkedIn Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.linkedin_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:97)

#### Outbound Dispatch Payload
```json
{
  "background": true,
  "model": "gemini/gemini-3.5-flash-lite",
  "webhook": {
    "url": "https://<your-site>/api/method/frappe_cadence.linkedin_template.callback",
    "events": [
      "completed",
      "failed"
    ],
    "metadata": {
      "name": "COMM-00004"
    }
  },
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "communication_generation",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "content": {
            "type": "string",
            "description": "The main body content of the message"
          }
        },
        "required": [
          "content"
        ],
        "additionalProperties": false
      }
    }
  },
  "input": [...]
}
```

---

## Optimization and Prediction Callbacks

### Template Optimization Callback (`optimize_callback`)

- **Endpoints**:
  - n8n: `/api/method/frappe_cadence.integrations.n8n.optimize_callback`
  - Sift: `/api/method/frappe_cadence.integrations.sift.optimize_callback`
- **Webhook Metadata Model**:
  ```json
  "metadata": {
    "doctype": "Email Template",
    "name": "ET-00001"
  }
  ```

### Annotation Prediction Callback (`predict_callback`)

- **Endpoints**:
  - n8n: `/api/method/frappe_cadence.integrations.n8n.predict_callback`
  - Sift: `/api/method/frappe_cadence.integrations.sift.predict_callback`
- **Webhook Metadata Model**:
  ```json
  "metadata": {
    "doctype": "Email Template Annotation",
    "name": "ETA-00001"
  }
  ```
