from fastapi import Query
from dataclasses import dataclass


@dataclass
class PageParams:
    """分页参数"""
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def get_page_params(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> PageParams:
    """FastAPI依赖注入分页参数"""
    return PageParams(page=page, page_size=page_size)