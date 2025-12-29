# LLM Gateway API

A Flask-based LLM gateway API with multiple vendor endpoints for testing. Features local language models (TinyLlama, DistilGPT-2) and OpenAI passthrough capabilities.

## Features

- 🤖 **Multiple LLM Vendors**: Test different response formats and models
- 🎨 **Interactive Web UI**: Chat interface and API documentation with "Try It" functionality
- 🔄 **Error Simulation**: Random failures and rate limiting for resilience testing
- 🔌 **OpenAI Passthrough**: Direct integration with OpenAI's API
- 📊 **Token Usage Tracking**: Monitor input/output tokens and latency

## Web Interfaces

- **Chat Interface**: http://localhost:8080 - Interactive chat with vendor selection
- **API Documentation**: http://localhost:8080/request-viewer - Stripe/Postman-style API docs with live testing

## API Endpoints

### Vendor A - TinyLlama (Local)

`POST /vendor-a/messages`

Uses TinyLlama-1.1B-Chat-v1.0 model for instruction-following responses.

**Request:**
```json
{
  "prompt": "What is the meaning of life?",
  "system_prompt": "You are a helpful assistant" // optional
}
```

**Response:**
```json
{
  "outputText": "Generated response from TinyLlama",
  "tokensIn": 15,
  "tokensOut": 25,
  "latencyMS": 1234
}
```

**Error Simulation:**
- 10% chance of HTTP 500 error
- 10% chance of slow response (2-5 seconds)

### Vendor B - DistilGPT-2 (Local)

`POST /vendor-b/messages`

Uses DistilGPT-2 model for faster, more creative responses.

**Request:**
```json
{
  "prompt": "Tell me a story",
  "system_prompt": "You are a creative writer" // optional
}
```

**Response:**
```json
{
  "choices": [{
    "message": {
      "content": "Generated response from DistilGPT-2"
    }
  }],
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20
  }
}
```

**Error Simulation:**
- 10% chance of HTTP 429 rate limit with `retryAfterMs` (5000-10000ms)

### Vendor E - Echo

`POST /vendor-e/messages`

Simple echo endpoint for testing.

**Request:**
```json
{
  "prompt": "Hello world"
}
```

**Response:**
```json
{
  "response": "You entered Hello world"
}
```

### Vendor O - OpenAI Passthrough

`POST /vendor-o/messages`

Direct passthrough to OpenAI's API. Requires `OPENAI_API_KEY` in `.env` file.

**Request:**
```json
{
  "prompt": "Explain quantum computing",
  "system_prompt": "You are a helpful assistant", // optional
  "model": "gpt-3.5-turbo" // optional, defaults to gpt-3.5-turbo
}
```

**Response:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-3.5-turbo",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Response from OpenAI"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 25,
    "total_tokens": 40
  }
}
```

## Local Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure OpenAI API key (optional, for Vendor O)
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Run

```bash
# Start the server
python app.py

# Server will run on http://localhost:8080
# First run will download models (~2GB for TinyLlama, ~400MB for DistilGPT-2)
```

### Test

```bash
# Run all tests
pytest test_api.py -v

# Test against custom URL
BASE_URL=http://localhost:8080 pytest test_api.py -v

# Test manually with curl
curl -X POST http://localhost:8080/vendor-a/messages \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'

curl -X POST http://localhost:8080/vendor-b/messages \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a joke"}'

curl -X POST http://localhost:8080/vendor-e/messages \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Echo test"}'

# Test Vendor O (requires API key in .env)
curl -X POST http://localhost:8080/vendor-o/messages \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?", "model": "gpt-3.5-turbo"}'
```

## Deploy to fly.io

```bash
# Install flyctl
brew install flyctl

# Login to fly.io
flyctl auth login

# Launch the app (first time)
flyctl launch

# Set OpenAI API key secret (optional, for Vendor O)
flyctl secrets set OPENAI_API_KEY=sk-your-api-key-here

# Deploy updates
flyctl deploy

# Check status
flyctl status

# View logs
flyctl logs
```

## Technology Stack

- **Backend**: Flask 3.0.0
- **LLM Inference**: Transformers 4.36.0, PyTorch 2.1.0
- **Models**: TinyLlama-1.1B-Chat-v1.0, DistilGPT-2
- **Testing**: Pytest 7.4.3
- **Deployment**: Fly.io (1GB RAM, auto-scaling)
- **Frontend**: Material Design UI with vanilla JavaScript

## Project Structure

```
sf-mock-vendor/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── test_api.py                 # Pytest test suite
├── Dockerfile                  # Container configuration
├── fly.toml                    # Fly.io deployment config
├── static/
│   ├── index.html             # Chat interface
│   └── request-viewer.html    # API documentation
└── README.md                   # This file
```

## Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for Vendor O endpoint (optional)

## Notes

- TinyLlama provides better instruction-following than DistilGPT-2 but is slower
- DistilGPT-2 is faster but produces more creative/unpredictable responses
- Error rates are simulated for testing resilience and retry logic
- Models are downloaded on first run and cached locally
- Vendor O requires a valid OpenAI API key to function
