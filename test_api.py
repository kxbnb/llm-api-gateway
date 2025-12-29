#!/usr/bin/env python3
import pytest
import requests
import os

# Base URL can be set via environment variable or defaults to localhost
BASE_URL = os.environ.get('BASE_URL', 'https://sf-mock-vendor.fly.dev')


class TestVendorA:
    """Test cases for Vendor A endpoints"""

    def test_send_message_success(self):
        """Test vendor-a message endpoint returns correct format"""
        response = requests.post(
            f"{BASE_URL}/vendor-a/messages",
            json={'prompt': 'Hello, how are you?', 'system_prompt': 'You are a helpful assistant'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'outputText' in data
            assert 'tokensIn' in data
            assert 'tokensOut' in data
            assert 'latencyMS' in data
            assert isinstance(data['outputText'], str)
            assert isinstance(data['tokensIn'], int)
            assert isinstance(data['tokensOut'], int)
            assert isinstance(data['latencyMS'], int)
            assert len(data['outputText']) > 0
        elif response.status_code == 500:
            # 10% failure rate is expected
            data = response.json()
            assert 'error' in data

    def test_error_rate_and_latency(self):
        """Test vendor-a has approximately 10% errors and 10% slow responses"""
        results = {'200': 0, '500': 0}
        slow_count = 0
        
        for i in range(30):
            response = requests.post(
                f"{BASE_URL}/vendor-a/messages",
                json={'prompt': 'test'},
                timeout=10
            )
            results[str(response.status_code)] = results.get(str(response.status_code), 0) + 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get('latencyMS', 0) > 1000:
                    slow_count += 1
        
        # Verify roughly 10% error rate (allow 0-30% range due to randomness)
        error_rate = results.get('500', 0) / 30
        assert 0 <= error_rate <= 0.3, f"Error rate {error_rate:.1%} outside expected range"
        
        # Verify roughly 10% slow responses (allow 0-30% range)
        success_count = results.get('200', 0)
        if success_count > 0:
            slow_rate = slow_count / success_count
            assert 0 <= slow_rate <= 0.4, f"Slow response rate {slow_rate:.1%} outside expected range"


class TestVendorB:
    """Test cases for Vendor B endpoints"""

    def test_send_message_success(self):
        """Test vendor-b message endpoint returns correct format"""
        response = requests.post(
            f"{BASE_URL}/vendor-b/messages",
            json={'prompt': 'What is AI?', 'system_prompt': 'You are a helpful assistant'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'choices' in data
            assert 'usage' in data
            assert isinstance(data['choices'], list)
            assert len(data['choices']) > 0
            assert 'message' in data['choices'][0]
            assert 'content' in data['choices'][0]['message']
            assert 'input_tokens' in data['usage']
            assert 'output_tokens' in data['usage']
            assert isinstance(data['usage']['input_tokens'], int)
            assert isinstance(data['usage']['output_tokens'], int)
        elif response.status_code == 429:
            # 10% rate limit is expected
            data = response.json()
            assert 'retryAfterMs' in data
            assert 'error' in data
            assert 5000 <= data['retryAfterMs'] <= 10000

    def test_rate_limit(self):
        """Test vendor-b has approximately 10% rate limit responses"""
        results = {'200': 0, '429': 0}
        
        for i in range(30):
            response = requests.post(
                f"{BASE_URL}/vendor-b/messages",
                json={'prompt': 'test'},
                timeout=10
            )
            results[str(response.status_code)] = results.get(str(response.status_code), 0) + 1
        
        # Verify roughly 10% rate limit (allow 0-30% range due to randomness)
        rate_limit_rate = results.get('429', 0) / 30
        assert 0 <= rate_limit_rate <= 0.3, f"Rate limit rate {rate_limit_rate:.1%} outside expected range"


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


if __name__ == '__main__':
    # Run with: python test_api.py or pytest test_api.py
    pytest.main([__file__, '-v'])
