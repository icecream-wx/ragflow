"""
中间件（拦截器）模块
"""
import time
import json
from typing import Callable, Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logger import app_logger
from app.core.response import ResponseModel


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""

    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()
        method, path = request.method, request.url.path
        client_ip = request.client.host if request.client else "unknown"
        app_logger.info(f"请求开始 - {method} {path} | IP: {client_ip}")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            app_logger.info(f"请求完成 - {method} {path} | Status: {response.status_code} | Time: {process_time:.3f}s")
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            process_time = time.time() - start_time
            app_logger.error(f"请求异常 - {method} {path} | Error: {str(e)}", exc_info=True)
            return ResponseModel.error(message=f"服务器内部错误: {str(e)}", code=500)


class ResponseMiddleware(BaseHTTPMiddleware):
    """响应格式化中间件"""

    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        response = await call_next(request)
        if isinstance(response, JSONResponse):
            try:
                body = json.loads(response.body.decode())
                if isinstance(body, dict) and "code" in body and "data" in body and "message" in body:
                    return response
                if response.status_code == status.HTTP_200_OK:
                    return ResponseModel.success(data=body)
                return ResponseModel.error(
                    message=body.get("detail", "请求失败") if isinstance(body, dict) else str(body),
                    code=response.status_code
                )
            except (json.JSONDecodeError, AttributeError):
                pass
        return response
