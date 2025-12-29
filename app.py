import random
import time
import uuid
import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import requests as http_requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')

# Load DistilGPT-2 for both Vendor A and Vendor B
print("Loading DistilGPT-2 model...")
distilgpt2_name = "distilgpt2"
distilgpt2_tokenizer = AutoTokenizer.from_pretrained(distilgpt2_name)
distilgpt2_model = AutoModelForCausalLM.from_pretrained(distilgpt2_name)
distilgpt2_tokenizer.pad_token = distilgpt2_tokenizer.eos_token
print("DistilGPT-2 loaded successfully!")

# Language model text generation
def generate_response_distilgpt2(prompt, system_prompt=None):
    """Generate response using DistilGPT-2"""
    try:
        # Prepare input
        if system_prompt:
            full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:"
        else:
            full_prompt = f"User: {prompt}\nAssistant:"
        
        inputs = distilgpt2_tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=100)
        
        # Generate response
        with torch.no_grad():
            outputs = distilgpt2_model.generate(
                inputs['input_ids'],
                max_new_tokens=50,
                temperature=0.8,
                do_sample=True,
                top_p=0.9,
                pad_token_id=distilgpt2_tokenizer.eos_token_id
            )
        
        # Decode response
        full_response = distilgpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract assistant's response
        if "Assistant:" in full_response:
            response = full_response.split("Assistant:")[1].strip()
            response = response.split('.')[0] + '.' if '.' in response else response[:100]
        else:
            response = full_response[len(full_prompt):].strip()[:100]
        
        return response if response else "I understand your message."
    except Exception as e:
        print(f"Error generating response with DistilGPT-2: {e}")
        return "I understand your message."

def count_tokens(text, vendor='a'):
    """Count tokens using the tokenizer"""
    return len(distilgpt2_tokenizer.encode(text))

# Vendor A endpoints
@app.route('/vendor-a/messages', methods=['POST'])
def vendor_a_send_message():
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
    prompt = data.get('prompt', data.get('message', 'Hello'))
    system_prompt = data.get('system_prompt')
    
    # Generate response using DistilGPT-2
    output_text = generate_response_distilgpt2(prompt, system_prompt)
    
    # Calculate tokens
    tokens_in = count_tokens(prompt, 'a')
    tokens_out = count_tokens(output_text, 'a')
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    return jsonify({
        'outputText': output_text,
        'tokensIn': tokens_in,
        'tokensOut': tokens_out,
        'latencyMS': latency_ms
    }), 200

# Vendor B endpoints
@app.route('/vendor-b/messages', methods=['POST'])
def vendor_b_send_message():
    # 10% chance of rate limit
    if random.random() < 0.1:
        retry_after_ms = random.randint(5000, 10000)
        return jsonify({
            'retryAfterMs': retry_after_ms,
            'error': 'Rate limit exceeded'
        }), 429
    
    data = request.get_json()
    prompt = data.get('prompt', data.get('message', 'Hello'))
    system_prompt = data.get('system_prompt')
    
    # Generate response using DistilGPT-2
    output_text = generate_response_distilgpt2(prompt, system_prompt)
    
    # Calculate tokens
    input_tokens = count_tokens(prompt, 'b')
    output_tokens = count_tokens(output_text, 'b')
    
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

# Vendor E endpoints
@app.route('/vendor-e/messages', methods=['POST'])
def vendor_e_send_message():
    data = request.get_json()
    prompt = data.get('prompt', data.get('message', 'Hello'))
    
    # Simply echo back with prefix
    echo_response = f"You entered {prompt}"
    
    return jsonify({
        'response': echo_response
    }), 200

def execute_function_call(function_name, arguments_str):
    """Execute a function call and return the result"""
    import json
    
    # Parse arguments
    try:
        arguments = json.loads(arguments_str)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON arguments"})
    
    # Real implementation for get_current_weather using wttr.in
    if function_name == "get_current_weather":
        location = arguments.get("location", "Unknown")
        unit = arguments.get("unit", "fahrenheit")
        
        try:
            # Call wttr.in weather API (free, no API key required)
            weather_response = http_requests.get(
                f"https://wttr.in/{location}?format=j1",
                timeout=10
            )
            
            if weather_response.status_code == 200:
                weather_json = weather_response.json()
                current = weather_json['current_condition'][0]
                
                # Convert temperature based on unit preference
                if unit == "celsius":
                    temp = current['temp_C']
                    temp_unit = "°C"
                else:
                    temp = current['temp_F']
                    temp_unit = "°F"
                
                weather_data = {
                    "location": location,
                    "temperature": f"{temp}{temp_unit}",
                    "condition": current['weatherDesc'][0]['value'],
                    "humidity": f"{current['humidity']}%",
                    "wind_speed": f"{current['windspeedMiles']} mph",
                    "feels_like": f"{current['FeelsLikeF']}°F" if unit == "fahrenheit" else f"{current['FeelsLikeC']}°C"
                }
                return json.dumps(weather_data)
            else:
                return json.dumps({
                    "error": f"Failed to fetch weather data for {location}",
                    "status_code": weather_response.status_code
                })
        except Exception as e:
            return json.dumps({
                "error": f"Weather API error: {str(e)}",
                "location": location
            })
    
    # Default response for unknown functions
    return json.dumps({"error": f"Function {function_name} not implemented"})

# Vendor O endpoints (OpenAI passthrough)
@app.route('/vendor-o/messages', methods=['POST'])
def vendor_o_send_message():
    data = request.get_json()
    prompt = data.get('prompt', data.get('message', 'Hello'))
    system_prompt = data.get('system_prompt', 'You are a helpful assistant')
    model = data.get('model', 'gpt-3.5-turbo')
    tools = data.get('tools')  # Optional tools parameter
    tool_choice = data.get('tool_choice')  # Optional tool_choice parameter
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-your-openai-api-key-here':
        return jsonify({
            'error': 'OPENAI_API_KEY not configured',
            'type': 'ConfigurationError'
        }), 500
    
    try:
        # Build OpenAI request payload
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        
        payload = {
            'model': model,
            'messages': messages
        }
        
        # Add tools if provided
        if tools:
            payload['tools'] = tools
        
        # Add tool_choice if provided
        if tool_choice:
            payload['tool_choice'] = tool_choice
        
        # First API call to OpenAI
        response = http_requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify(response.json()), response.status_code
        
        response_data = response.json()
        assistant_message = response_data['choices'][0]['message']
        
        # Check if the model wants to call a function
        if assistant_message.get('tool_calls'):
            # Add assistant's response to messages
            messages.append(assistant_message)
            
            # Execute each tool call
            for tool_call in assistant_message['tool_calls']:
                function_name = tool_call['function']['name']
                function_args = tool_call['function']['arguments']
                
                # Execute the function
                function_response = execute_function_call(function_name, function_args)
                
                # Add function result to messages
                messages.append({
                    'tool_call_id': tool_call['id'],
                    'role': 'tool',
                    'name': function_name,
                    'content': function_response
                })
            
            # Second API call with function results
            second_payload = {
                'model': model,
                'messages': messages
            }
            
            second_response = http_requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json=second_payload,
                timeout=30
            )
            
            if second_response.status_code == 200:
                return jsonify(second_response.json()), 200
            else:
                return jsonify(second_response.json()), second_response.status_code
        
        # No tool calls, return first response
        return jsonify(response_data), 200
            
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

# Health check endpoint for fly.io
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

# Serve frontend
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/request-viewer')
def request_viewer():
    return send_from_directory('static', 'request-viewer.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
