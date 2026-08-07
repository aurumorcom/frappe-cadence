# Callback Data Models & Webhook Payload Specifications

This document defines the data models and payload contracts for outbound webhook requests sent to AI engines (Sift / n8n) and inbound callback responses received by `frappe_cadence`.

---

## WebhookResponse Schema

All inbound callbacks delivered to `frappe_cadence` follow the unified `WebhookResponse` model parsed by [`_template.WebhookResponse`](apps/frappe_cadence/frappe_cadence/_template.py:6):

```json
{
  "success": true,
  "type": "email_template.complete",
  "id": "wm-job-12345",
  "webhookId": "wh-delivery-67890",
  "data": [
    {
      "content": [
        {
          "type": "text",
          "text": "{\"subject\": \"Quick question\", \"content\": \"Hi John...\"}"
        }
      ]
    }
  ],
  "error": null,
  "metadata": {
    "name": "COMM-00001",
    "doctype": "Communication"
  }
}
```

### Schema Attributes

| Field | Type | Description |
|---|---|---|
| **`success`** | `boolean` | **Primary Decision Flag.** `true` for successful completion, `false` for execution failure. |
| **`type`** | `string` | Event type identifier (e.g. `email_template.complete`, `completed`, `response.completed`, `agent.started`). Used to filter out in-between status events such as `started`. |
| **`id`** | `string` | Execution or Job ID (e.g., Windmill Job ID `WM_JOB_ID` or UUID). |
| **`webhookId`** | `string` | Unique UUID for the delivery attempt. |
| **`data`** | `Any` | Output payload. Contains empty array `[]` for `started` events, or raw output array/object for completed tasks. |
| **`error`** | `string \| null` | Optional error message string when `success` is `false`. |
| **`metadata`** | `object \| string` | Contextual dictionary passed in the outbound dispatch and echoed back in callback. Can be a dictionary or a stringified JSON object. |

---

## Callback Endpoint Return Values

To ensure transparency, all whitelisted callback endpoints return the **actual updated domain document** as a dictionary rather than generic `{"status": "success"}` payloads:

1. **Generation Callbacks** ([`_template.handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:198)): Returns the updated `Communication` document (`comm.as_dict()`).
2. **Template Optimization Callbacks** ([`sift.optimize_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:102), [`n8n.optimize_callback`](apps/frappe_cadence/frappe_cadence/integrations/n8n.py:284)): Returns the updated Template document (`template.as_dict()`).
3. **Annotation Prediction Callbacks** ([`sift.predict_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:228), [`n8n.predict_callback`](apps/frappe_cadence/frappe_cadence/integrations/n8n.py:417)): Returns the updated `Annotation` child document (`ann.as_dict()`).

---

## Standard Webhook Envelope Rule (Outbound)

All outbound dispatches to external AI services (Sift / n8n) follow the unified webhook envelope specification:
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
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:198)

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

#### Inbound Callback Request (`POST` from n8n / Sift)
```json
{
  "success": true,
  "type": "email_template.complete",
  "id": "wm-job-00001",
  "webhookId": "wh-delivery-00001",
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

#### Inbound Callback Endpoint Return Value
```json
{
  "name": "COMM-00001",
  "doctype": "Communication",
  "subject": "Quick question regarding your growth strategy",
  "content": "<p>Hi John,<br><br>I noticed...</p>",
  "delivery_status": "Scheduled"
}
```

#### Inbound Callback cURL Example
```bash
curl -X POST "https://<your-site>/api/method/frappe_cadence.email_template.callback" \
  -H "Content-Type: application/json" \
  -d '{
    "success": true,
    "type": "email_template.complete",
    "id": "wm-job-00001",
    "webhookId": "wh-delivery-00001",
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
  }'
```

---

### 2. SMS Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.sms_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:198)

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

#### Inbound Callback Request
```json
{
  "success": true,
  "type": "sms_template.complete",
  "id": "wm-job-00002",
  "webhookId": "wh-delivery-00002",
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

#### Inbound Callback Endpoint Return Value
```json
{
  "name": "COMM-00002",
  "doctype": "Communication",
  "subject": "SMS Message",
  "content": "<p>Hi John, following up on our email yesterday. Are you available for a brief call?</p>",
  "delivery_status": "Scheduled"
}
```

---

### 3. WhatsApp Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.whatsapp_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:198)

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

#### Inbound Callback Request
```json
{
  "success": true,
  "type": "whatsapp_template.complete",
  "id": "wm-job-00003",
  "webhookId": "wh-delivery-00003",
  "metadata": {
    "name": "COMM-00003"
  },
  "data": [
    {
      "content": [
        {
          "type": "text",
          "text": "{\"content\": \"Hi John, reaching out on WhatsApp regarding our recent conversation.\"}"
        }
      ]
    }
  ]
}
```

#### Inbound Callback Endpoint Return Value
```json
{
  "name": "COMM-00003",
  "doctype": "Communication",
  "subject": "WhatsApp Message",
  "content": "<p>Hi John, reaching out on WhatsApp regarding our recent conversation.</p>",
  "delivery_status": "Scheduled"
}
```

---

### 4. LinkedIn Template Callback Data Model

- **Channel Endpoint**: `/api/method/frappe_cadence.linkedin_template.callback`
- **Handler Method**: [`handle_callback`](apps/frappe_cadence/frappe_cadence/_template.py:198)

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

#### Inbound Callback Request
```json
{
  "success": true,
  "type": "linkedin_template.complete",
  "id": "wm-job-00004",
  "webhookId": "wh-delivery-00004",
  "metadata": {
    "name": "COMM-00004"
  },
  "data": [
    {
      "content": [
        {
          "type": "text",
          "text": "{\"content\": \"Hi John, enjoyed reading your post on AI workflows. Would love to connect!\"}"
        }
      ]
    }
  ]
}
```

#### Inbound Callback Endpoint Return Value
```json
{
  "name": "COMM-00004",
  "doctype": "Communication",
  "subject": "LinkedIn Message",
  "content": "<p>Hi John, enjoyed reading your post on AI workflows. Would love to connect!</p>",
  "delivery_status": "Scheduled"
}
```

---

## Optimization and Prediction Callbacks

### Template Optimization Callback (`optimize_callback`)

- **Endpoints**:
  - n8n: `/api/method/frappe_cadence.integrations.n8n.optimize_callback` (Handler: [`n8n.optimize_callback`](apps/frappe_cadence/frappe_cadence/integrations/n8n.py:284))
  - Sift: `/api/method/frappe_cadence.integrations.sift.optimize_callback` (Handler: [`sift.optimize_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:102))

#### Inbound Optimization Callback Request
```json
{
  "success": true,
  "type": "completed",
  "id": "wm-job-00005",
  "webhookId": "wh-delivery-00005",
  "metadata": {
    "doctype": "Email Template",
    "name": "ET-00001"
  },
  "data": [
    {
      "agent_name": "Sift AI Optimization Agent"
    }
  ]
}
```

#### Inbound Optimization Endpoint Return Value
```json
{
  "name": "ET-00001",
  "doctype": "Email Template",
  "sift_id": "Sift AI Optimization Agent",
  "status": "Disabled",
  "enabled": 0
}
```

---

### Annotation Prediction Callback (`predict_callback`)

- **Endpoints**:
  - n8n: `/api/method/frappe_cadence.integrations.n8n.predict_callback` (Handler: [`n8n.predict_callback`](apps/frappe_cadence/frappe_cadence/integrations/n8n.py:417))
  - Sift: `/api/method/frappe_cadence.integrations.sift.predict_callback` (Handler: [`sift.predict_callback`](apps/frappe_cadence/frappe_cadence/integrations/sift.py:228))

#### Inbound Prediction Callback Request
```json
{
  "success": true,
  "type": "response.completed",
  "id": "wm-job-00006",
  "webhookId": "wh-delivery-00006",
  "metadata": {
    "doctype": "Email Template Annotation",
    "name": "ETA-00001"
  },
  "data": [
    {
      "content": [
        {
          "type": "text",
          "text": "{\"subject\": \"Predicted Subject\", \"body\": \"Predicted Body\"}"
        }
      ]
    }
  ]
}
```

#### Inbound Prediction Endpoint Return Value
```json
{
  "name": "ETA-00001",
  "doctype": "Email Template Annotation",
  "parent": "ET-00001",
  "subject": "Predicted Subject",
  "body": "Predicted Body"
}
```
