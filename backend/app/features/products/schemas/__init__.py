"""Pydantic contracts for the Product feature."""

from .requests import CreateProductRequest, UpdateProductRequest
from .responses import ProductResponse

__all__ = ["CreateProductRequest", "ProductResponse", "UpdateProductRequest"]