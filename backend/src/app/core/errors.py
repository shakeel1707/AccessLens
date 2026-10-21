"""
Error handling middleware and utilities for graceful failure handling.
"""

import uuid
import logging
from typing import Callable, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException


logger = logging.getLogger("accesslens.middleware")


class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(self, code: str, message: str, status_code: int, request_id: str | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id or str(uuid.uuid4())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
                "request_id": self.request_id,
            }
        }


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling and request tracking."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.logger = logger
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except HTTPException as e:
            # FastAPI HTTPException; pass through
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    code="HTTP_ERROR",
                    message=e.detail,
                    status_code=e.status_code,
                    request_id=request_id,
                ).to_dict(),
            )
        except ValueError as e:
            # Validation errors
            logger.warning(f"[{request_id}] Validation error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    code="VALIDATION_ERROR",
                    message=str(e),
                    status_code=status.HTTP_400_BAD_REQUEST,
                    request_id=request_id,
                ).to_dict(),
            )
        except Exception as e:
            # Unexpected errors
            logger.error(f"[{request_id}] Unhandled exception: {type(e).__name__}: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred. Please contact support if the issue persists.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    request_id=request_id,
                ).to_dict(),
            )


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Helper to create standardized error response."""
    return ErrorResponse(code, message, status_code, request_id).to_dict()