import time
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle
import logging
from ..utils import raise_validation


logger = logging.getLogger(__name__)


class TokenBucketThrottle(BaseThrottle):

    """
        Token bucket rate limiter with the same configuration for both anonymous and authenticated users.

    - Anonymous users: 1 token every 60 seconds, bucket size 7
    - Authenticated users: 1 token every 30 seconds, bucket size 20
    """

    def get_rate_and_capacity(self, request):

        # Get the current authenticated user
        user = request.user

        # Anonymous users
        if not user.is_authenticated:
            return 60, 7

        # Authenticated users
        return 30, 5
    
    def get_cache_key(self, request):

        # Get the current authenticated user
        user = request.user

        # If the user is authenticated 
        if user.is_authenticated:
            return f"rate_limit_user:{user.id}"
        else:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "anon")).split(",")[0].strip()
            return f"rate_limit_anon:{str(ip)}"

    def allow_request(self, request, view):

        now = time.time()
        refill_rate, capacity = self.get_rate_and_capacity(request)
        key = self.get_cache_key(request)

        bucket = cache.get(key)
        logger.debug(f"BUCKET FROM CACHE: {bucket}")

        # If no bucket found initialize full bucket
        if not bucket:
            last_refill_time = now
            current_tokens = capacity
        else:
            # Get the last refill time and current tokens inside the cache bucket
            last_refill_time, current_tokens = bucket

            # Calculate the elapsed time
            elapsed_time = now - last_refill_time
      

            # Only add tokens if elapsed has passed since the last refill time
            if elapsed_time > 0:
                # Calculate how many tokens to add based on the elapsed time and refill rate
                tokens_to_add = elapsed_time / refill_rate
                logger.debug(f"TOKENS TO ADD : {tokens_to_add}")    
                current_tokens = min(capacity, current_tokens + tokens_to_add)

        # Convert the tokens into integer
        current_tokens = int(current_tokens)

        if current_tokens >= 1:
            # Consume one token
            current_tokens -= 1
            # Update the last refill time to current time 
            last_refill_time = now
            # Update the current available tokens and last refill time from the cache
            self.save_cache(key, last_refill_time, current_tokens)
            return True
        else:
            self.save_cache(key, last_refill_time, current_tokens)
            return False

    # Helper function to save the cache
    def save_cache(self, key, last_refill_time, tokens):
        if not isinstance(key, str):
            raise_validation("Cache key must be a string")
        cache.set(key, (last_refill_time, tokens), timeout=3600)


    def wait(self):
        return None







