"""Objects injected into the routes by FastAPI.

The routes never build services themselves: they receive them here.
This makes it easy to swap the real model for a fake one in tests.
"""

from fastapi import Request

from config.settings import Settings
from inference.service import InferenceService


def get_inference_service(request: Request) -> InferenceService:
    """The service created at startup by backend/main.py."""
    return request.app.state.inference_service


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings
