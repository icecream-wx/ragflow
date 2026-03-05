"""
统一响应格式模块
"""
from typing import Any
from fastapi.responses import JSONResponse
from fastapi import status


class ResponseModel:
    """统一响应格式"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: int = 200
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": code,
                "data": data,
                "message": message
            }
        )

    @staticmethod
    def error(
        message: str = "操作失败",
        code: int = 500,
        data: Any = None
    ) -> JSONResponse:
        http_status = status.HTTP_200_OK
        if code == 401:
            http_status = status.HTTP_401_UNAUTHORIZED
        elif code == 403:
            http_status = status.HTTP_403_FORBIDDEN
        elif code == 404:
            http_status = status.HTTP_404_NOT_FOUND
        elif code == 400:
            http_status = status.HTTP_400_BAD_REQUEST

        return JSONResponse(
            status_code=http_status,
            content={
                "code": code,
                "data": data,
                "message": message
            }
        )
