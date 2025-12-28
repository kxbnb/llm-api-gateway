import random
import time
import uuid
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Simple mock text generation
def generate_mock_response(message):
    """Simple mock response generator"""
    responses = [
        f"I understand your message about: {message[:50]}...",
        f"That's an interesting point. Let me elaborate on {message[:30]}...",
        f"Thank you for sharing. Regarding {message[:40]}...",
        "I appreciate your input. Here's my perspective on that topic.",
        "That's a great question. Let me provide some insights.",
    ]
    return random.choice(responses)

def count_tokens(text):
    """Simple token counter - roughly words/0.75"""
    return max(1, len(text.split()) * 4 // 3)

# Vendor A endpoints
@app.route('/vendor-a/conversations', methods=['POST'])
def vendor_a_create_conversation():
    conversation_id = str(uuid.uuid4())
    return jsonify({
        'conversation_id': conversation_id
    }), 201

@app.route('/vendor-a/conversations/<conversation_id>/messages', methods=['POST'])
def vendor_a_send_message(conversation_id):
    start_time = time.time()
    
    # 10% chance of failure
    if random.random() < 0.1:
        return jsonify({
            'error': 'Internal server error'
        }), 500
    
    # 10% chance of slow response (2-5 seconds delay)
    if random.random() < 0.1:
        time.sleep(random.uniform(2, 5))
    
    data = request.get_json()
    input_message = data.get('message', 'Hello')
    
    # Generate response
    output_text = generate_mock_response(input_message)
    
    # Calculate tokens
    tokens_in = count_tokens(input_message)
    tokens_out = count_tokens(output_text)
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    return jsonify({
        'outputText': output_text,
        'tokensIn': tokens_in,
        'tokensOut': tokens_out,
        'latencyMS': latency_ms
    }), 200

# Vendor B endpoints
@app.route('/vendor-b/conversations', methods=['POST'])
def vendor_b_create_conversation():
    conversation_id = str(uuid.uuid4())
    return jsonify({
        'conversation_id': conversation_id
    }), 201

@app.route('/vendor-b/conversations/<conversation_id>/messages', methods=['POST'])
def vendor_b_send_message(conversation_id):
    # 10% chance of rate limit
    if random.random() < 0.1:
        retry_after_ms = random.randint(5000, 10000)
        return jsonify({
            'retryAfterMs': retry_after_ms,
            'error': 'Rate limit exceeded'
        }), 429
    
    data = request.get_json()
    input_message = data.get('message', 'Hello')
    
    # Generate response
    output_text = generate_mock_response(input_message)
    
    # Calculate tokens
    input_tokens = count_tokens(input_message)
    output_tokens = count_tokens(output_text)
    
    return jsonify({
        'choices': [{
            'message': {
                'content': output_text
            }
        }],
        'usage': {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        }
    }), 200

# Health check endpoint for fly.io
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
