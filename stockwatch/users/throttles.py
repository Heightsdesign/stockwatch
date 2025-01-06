# users/throttles.py

from rest_framework.throttling import SimpleRateThrottle

class VerificationThrottle(SimpleRateThrottle):
    scope = 'verification'

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return None  # Only throttle authenticated users

        # Use user ID for unique throttling
        return self.cache_format % {
            'scope': self.scope,
            'ident': request.user.pk
        }
