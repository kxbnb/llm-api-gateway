import random
import time
import uuid
import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import requests as http_requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')

# Simple token counter for canned responses
def count_tokens(text):
    """Simple word-based token approximation"""
    return len(text.split())

def generate_canned_response(prompt, system_prompt=None):
    """Generate a canned response based on prompt keywords"""
    prompt_lower = prompt.lower()
    
    # Simple keyword-based responses
    if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! How can I assist you today?"
    elif any(word in prompt_lower for word in ['weather', 'temperature']):
        return "I can help with weather information. Please specify a location."
    elif any(word in prompt_lower for word in ['meaning of life', 'life']):
        return "The meaning of life is a philosophical question that has been pondered throughout history."
    elif any(word in prompt_lower for word in ['help', 'assist']):
        return "I'm here to help! Please let me know what you need assistance with."
    elif any(word in prompt_lower for word in ['thank', 'thanks']):
        return "You're welcome! Feel free to ask if you need anything else."
    else:
        return "I understand your message. This is a simulated response for testing purposes."

def extract_invoice_id(prompt):
    """Extract invoice ID from prompt (looks for patterns like INV-123, invoice 123, #123)"""
    import re
    # Look for patterns like INV-123, invoice 123, #123, invoice #123
    patterns = [
        r'INV-\d+',
        r'invoice[\s#]+\d+',
        r'#\d+'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            # Extract just the number part
            number_match = re.search(r'\d+', match.group())
            if number_match:
                return f"INV-{number_match.group()}"
    return None

def get_invoice_data(invoice_id):
    """Return dummy invoice data"""
    import json
    # Parse invoice number from ID
    invoice_num = invoice_id.split('-')[1] if '-' in invoice_id else invoice_id
    
    # Generate deterministic dummy data based on invoice number
    seed = int(invoice_num) if invoice_num.isdigit() else 12345
    
    dummy_invoices = [
        {
            "invoice_id": invoice_id,
            "customer_name": "Acme Corporation",
            "amount": 1250.00 + (seed % 1000),
            "currency": "USD",
            "status": "paid",
            "issue_date": "2025-12-01",
            "due_date": "2025-12-31",
            "items": [
                {"description": "Consulting Services", "quantity": 10, "unit_price": 100.00},
                {"description": "Software License", "quantity": 1, "unit_price": 250.00}
            ]
        },
        {
            "invoice_id": invoice_id,
            "customer_name": "Tech Solutions Inc",
            "amount": 3500.00 + (seed % 500),
            "currency": "USD",
            "status": "pending",
            "issue_date": "2025-12-15",
            "due_date": "2026-01-15",
            "items": [
                {"description": "Development Work", "quantity": 40, "unit_price": 85.00}
            ]
        },
        {
            "invoice_id": invoice_id,
            "customer_name": "Global Enterprises",
            "amount": 5200.00 + (seed % 2000),
            "currency": "USD",
            "status": "overdue",
            "issue_date": "2025-11-01",
            "due_date": "2025-12-01",
            "items": [
                {"description": "Project Management", "quantity": 20, "unit_price": 150.00},
                {"description": "Infrastructure Setup", "quantity": 1, "unit_price": 2200.00}
            ]
        }
    ]
    
    # Select invoice based on seed
    invoice = dummy_invoices[seed % len(dummy_invoices)]
    return json.dumps(invoice)

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
    tools = data.get('tools')  # Optional tools parameter
    
    # Check if tools are provided and prompt mentions an invoice
    if tools:
        invoice_id = extract_invoice_id(prompt)
        if invoice_id:
            # Simulate tool call response
            tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
            invoice_data = get_invoice_data(invoice_id)
            
            # Generate natural language response incorporating invoice data
            import json
            invoice_info = json.loads(invoice_data)
            output_text = f"I found invoice {invoice_id} for {invoice_info['customer_name']}. The total amount is ${invoice_info['amount']:.2f} {invoice_info['currency']} and the status is '{invoice_info['status']}'. It was issued on {invoice_info['issue_date']} with a due date of {invoice_info['due_date']}."
            
            tokens_in = count_tokens(prompt)
            tokens_out = count_tokens(output_text)
            latency_ms = int((time.time() - start_time) * 1000)
            
            return jsonify({
                'outputText': output_text,
                'tokensIn': tokens_in,
                'tokensOut': tokens_out,
                'latencyMS': latency_ms,
                'tool_calls': [{
                    'id': tool_call_id,
                    'type': 'function',
                    'function': {
                        'name': 'get_invoice',
                        'arguments': json.dumps({'invoice_id': invoice_id})
                    }
                }],
                'invoice_data': invoice_info
            }), 200
    
    # Generate canned response
    output_text = generate_canned_response(prompt, system_prompt)
    
    # Calculate tokens
    tokens_in = count_tokens(prompt)
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
    
    # Generate canned response
    output_text = generate_canned_response(prompt, system_prompt)
    
    # Calculate tokens
    input_tokens = count_tokens(prompt)
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
