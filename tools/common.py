"""Common types used across tools"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
