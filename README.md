# SF Mock Vendor API

A Flask-based mock vendor API for testing with two different vendor response formats.

## Endpoints

### Vendor A

- `POST /vendor-a/conversations` - Create a new conversation
  - Returns: `{ "conversation_id": "uuid" }`

- `POST /vendor-a/conversations/{id}/messages` - Send a message
  - Request: `{ "message": "your message" }`
  - Response: `{ "outputText": "...", "tokensIn": 10, "tokensOut": 15, "latencyMS": 123 }`
  - 10% chance of HTTP 500 error
  - 10% chance of slow response (2-5 seconds)

### Vendor B

- `POST /vendor-b/conversations` - Create a new conversation
  - Returns: `{ "conversation_id": "uuid" }`

- `POST /vendor-b/conversations/{id}/messages` - Send a message
  - Request: `{ "message": "your message" }`
  - Response: `{ "choices": [{ "message": { "content": "..." }}], "usage": { "input_tokens": 10, "output_tokens": 15 }}`
  - 10% chance of HTTP 429 rate limit with `retryAfterMs` (5000-10000ms)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test the API
curl -X POST http://localhost:8080/vendor-a/conversations
curl -X POST http://localhost:8080/vendor-a/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Deploy to fly.io

```bash
# Install flyctl
brew install flyctl

# Login to fly.io
flyctl auth login

# Launch the app (first time)
flyctl launch

# Or deploy updates
flyctl deploy

# Check status
flyctl status

# View logs
flyctl logs
```

## Testing

```bash
# Get app URL
flyctl status

# Test vendor-a
curl -X POST https://your-app.fly.dev/vendor-a/conversations

# Test vendor-b
curl -X POST https://your-app.fly.dev/vendor-b/conversations
```
