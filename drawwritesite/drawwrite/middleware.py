"""Custom middleware for DrawWrite"""

import logging

LOG = logging.getLogger(__name__)

class LogExceptions:
    """Middleware for logging exceptions raised by views."""

    def __init__(self, get_response):
        """Set get_response appropriately."""
        self.get_response = get_response

    def __call__(self, request):
        """Just call the next middleware."""
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Log the exception."""
        LOG.exception(exception)
        return None
