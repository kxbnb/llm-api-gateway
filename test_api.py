#!/usr/bin/env python3
import requests
import json

print('Testing 30 requests to each vendor to verify error rates...\n')

# Test Vendor A
print('=== VENDOR A ===')
results_a = {'200': 0, '500': 0}
slow_count = 0

for i in range(30):
    try:
        r = requests.post(
            'http://localhost:8080/vendor-a/conversations/test/messages',
            json={'message': 'test'},
            timeout=10
        )
        results_a[str(r.status_code)] = results_a.get(str(r.status_code), 0) + 1
        
        if r.status_code == 200:
            data = r.json()
            if data.get('latencyMS', 0) > 1000:
                slow_count += 1
                print(f"  Request {i+1}: Slow response - {data['latencyMS']}ms")
        elif r.status_code == 500:
            print(f"  Request {i+1}: HTTP 500 Error")
    except Exception as e:
        print(f"  Request {i+1}: Error - {e}")

print(f'\nVendor A Results:')
print(f'  Success (200): {results_a.get("200", 0)}/30')
print(f'  Errors (500): {results_a.get("500", 0)}/30')
print(f'  Slow (>1s latency): {slow_count}/30')

# Test Vendor B
print('\n=== VENDOR B ===')
results_b = {'200': 0, '429': 0}

for i in range(30):
    try:
        r = requests.post(
            'http://localhost:8080/vendor-b/conversations/test/messages',
            json={'message': 'test'},
            timeout=10
        )
        results_b[str(r.status_code)] = results_b.get(str(r.status_code), 0) + 1
        
        if r.status_code == 429:
            data = r.json()
            print(f"  Request {i+1}: HTTP 429 Rate Limit - retryAfterMs: {data.get('retryAfterMs')}ms")
    except Exception as e:
        print(f"  Request {i+1}: Error - {e}")

print(f'\nVendor B Results:')
print(f'  Success (200): {results_b.get("200", 0)}/30')
print(f'  Rate Limited (429): {results_b.get("429", 0)}/30')
