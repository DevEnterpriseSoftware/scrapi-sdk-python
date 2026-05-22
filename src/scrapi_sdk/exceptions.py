from __future__ import annotations

from typing import Optional


class ScrapiException(Exception):
    def __init__(
        self,
        status_code: Optional[int] = 500,
        message: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = 500 if status_code is None else int(status_code)
        self.inner_exception = inner_exception
