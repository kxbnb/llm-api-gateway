import random
import time
import uuid
from flask import Flask, request, jsonify
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = Flask(__name__)

# Load tiny language model (DistilGPT-2 - smallest available)
print("Loading DistilGPT-2 model...")
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token
print("Model loaded successfully!")

# Language model text generation
def generate_mock_response(message):
    """Generate response using DistilGPT-2"""
    try:
        # Prepare input
        prompt = f"User: {message}\nAssistant:"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=100)
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs['input_ids'],
                max_new_tokens=50,
                temperature=0.8,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode and extract assistant response
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant's response
        if "Assistant:" in full_response:
            response = full_response.split("Assistant:")[1].strip()
            # Take first sentence or up to 100 chars
            response = response.split('.')[0] + '.' if '.' in response else response[:100]
        else:
            response = full_response[len(prompt):].strip()[:100]
        
        return response if response else "I understand your message."
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I understand your message."

def count_tokens(text):
    """Count tokens using the actual tokenizer"""
    return len(tokenizer.encode(text))

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
