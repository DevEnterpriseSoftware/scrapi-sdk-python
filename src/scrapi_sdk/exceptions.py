from __future__ import annotations

from typing import Optional


class ScrapiException(Exception):
    """Represents errors that may occur when making calls to the ScrAPI API.

    Attributes:
        status_code: The HTTP status code associated with the error. Defaults to 500.
        inner_exception: The original exception that caused this error, if any.
    """

    def __init__(
        self,
        status_code: Optional[int] = 500,
        message: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """Initialize a new :class:`ScrapiException`.

        Args:
            status_code: The HTTP status code returned by the API. Defaults to 500.
            message: A message describing the error.
            inner_exception: The exception that is the cause of the current exception, if any.
        """
        super().__init__(message)
        self.status_code = 500 if status_code is None else int(status_code)
        self.inner_exception = inner_exception
