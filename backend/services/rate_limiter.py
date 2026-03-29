"""
Rate limiting middleware for PlacetaID
"""

from datetime import datetime, timedelta
from flask import request, jsonify
import redis
import json


class RateLimiter:
    """Redis-based rate limiting implementation"""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379'):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}. Rate limiting will use in-memory storage.")
            self.redis_client = None
        
        # In-memory fallback for development
        self._memory_store = {}
    
    def is_rate_limited(self, key: str, max_requests: int, 
                       window_seconds: int) -> tuple[bool, dict]:
        """
        Check if request is rate limited
        
        Args:
            key: Rate limit key (e.g., 'ip:127.0.0.1', 'dip_hash:xyz', 'client:abc')
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            (is_limited, info_dict)
            info_dict contains: remaining, reset_at, limit
        """
        if self.redis_client:
            return self._check_redis(key, max_requests, window_seconds)
        else:
            return self._check_memory(key, max_requests, window_seconds)
    
    def _check_redis(self, key: str, max_requests: int, 
                    window_seconds: int) -> tuple[bool, dict]:
        """Check rate limit using Redis"""
        rate_key = f'ratelimit:{key}'
        
        try:
            # Increment counter
            current = self.redis_client.incr(rate_key)
            
            # Set expiry on first request
            if current == 1:
                self.redis_client.expire(rate_key, window_seconds)
            
            # Get TTL
            ttl = self.redis_client.ttl(rate_key)
            reset_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            remaining = max(0, max_requests - current)
            is_limited = current > max_requests
            
            return is_limited, {
                'limit': max_requests,
                'remaining': remaining,
                'reset_at': reset_at.isoformat(),
                'retry_after': ttl
            }
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            # Fall back to memory
            return self._check_memory(key, max_requests, window_seconds)
    
    def _check_memory(self, key: str, max_requests: int, 
                     window_seconds: int) -> tuple[bool, dict]:
        """Check rate limit using in-memory storage (development)"""
        now = datetime.utcnow()
        
        if key not in self._memory_store:
            self._memory_store[key] = {
                'requests': [],
                'window_seconds': window_seconds
            }
        
        store = self._memory_store[key]
        
        # Remove old requests outside window
        cutoff = now - timedelta(seconds=window_seconds)
        store['requests'] = [
            req_time for req_time in store['requests']
            if req_time > cutoff
        ]
        
        # Add new request
        store['requests'].append(now)
        
        remaining = max(0, max_requests - len(store['requests']))
        is_limited = len(store['requests']) > max_requests
        
        # Calculate reset time
        oldest_request = min(store['requests']) if store['requests'] else now
        reset_at = oldest_request + timedelta(seconds=window_seconds)
        retry_after = int((reset_at - now).total_seconds())
        
        return is_limited, {
            'limit': max_requests,
            'remaining': remaining,
            'reset_at': reset_at.isoformat(),
            'retry_after': max(0, retry_after)
        }
    
    def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a key"""
        if self.redis_client:
            rate_key = f'ratelimit:{key}'
            try:
                self.redis_client.delete(rate_key)
                return True
            except Exception:
                return False
        else:
            if key in self._memory_store:
                del self._memory_store[key]
            return True
    
    def get_current_count(self, key: str) -> int:
        """Get current request count for a key"""
        if self.redis_client:
            rate_key = f'ratelimit:{key}'
            try:
                count = self.redis_client.get(rate_key)
                return int(count) if count else 0
            except Exception:
                return 0
        else:
            if key in self._memory_store:
                return len(self._memory_store[key]['requests'])
            return 0


class RateLimitConfig:
    """Rate limiting configuration"""
    
    # IP-based rate limiting: 20 requests per minute
    IP_LIMIT = {
        'max_requests': 20,
        'window_seconds': 60
    }
    
    # DIP-based rate limiting: 3 attempts per 24 hours
    DIP_LIMIT = {
        'max_requests': 3,
        'window_seconds': 86400  # 24 hours
    }
    
    # OAuth endpoint rate limiting: 5 requests per minute per client
    OAUTH_LIMIT = {
        'max_requests': 5,
        'window_seconds': 60
    }
    
    # Token endpoint rate limiting: 10 requests per minute per IP
    TOKEN_LIMIT = {
        'max_requests': 10,
        'window_seconds': 60
    }
    
    # Session refresh rate limiting: 10 refreshes per 24 hours per citizen
    REFRESH_LIMIT = {
        'max_requests': 10,
        'window_seconds': 86400
    }


def rate_limit_by_ip(max_requests: int = 20, window_seconds: int = 60):
    """
    Decorator for IP-based rate limiting
    
    Usage:
        @rate_limit_by_ip()
        def my_route():
            pass
    """
    def decorator(f):
        def decorated_function(*args, **kwargs):
            limiter = RateLimiter()
            ip = request.remote_addr
            
            is_limited, info = limiter.is_rate_limited(
                f'ip:{ip}',
                max_requests,
                window_seconds
            )
            
            if is_limited:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': info['retry_after'],
                    'limit': info['limit'],
                    'remaining': info['remaining']
                }), 429
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


def rate_limit_by_dip(limiter: RateLimiter, dip_hash: str):
    """
    Rate limit by DIP hash
    
    Args:
        limiter: RateLimiter instance
        dip_hash: SHA256 hash of DIP
    
    Returns:
        (is_limited, info)
    """
    config = RateLimitConfig.DIP_LIMIT
    return limiter.is_rate_limited(
        f'dip:{dip_hash}',
        config['max_requests'],
        config['window_seconds']
    )


def rate_limit_by_client(limiter: RateLimiter, client_id: str):
    """
    Rate limit by OAuth client ID
    
    Args:
        limiter: RateLimiter instance
        client_id: OAuth client identifier
    
    Returns:
        (is_limited, info)
    """
    config = RateLimitConfig.OAUTH_LIMIT
    return limiter.is_rate_limited(
        f'client:{client_id}',
        config['max_requests'],
        config['window_seconds']
    )


# Create global rate limiter instance
rate_limiter = RateLimiter()
