"""A module used to allow brace-formatted debugging messages."""

class BraceFormatter: #pylint: disable=too-few-public-methods
    """Allow brace-formatted debugging messages."""

    def __init__(self, fmt, *args, **kwargs):
        """Initialize the object"""
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        """Return the formatted message."""
        return self.fmt.format(*self.args, **self.kwargs)
