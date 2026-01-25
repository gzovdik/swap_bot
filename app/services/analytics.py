# -*- coding: utf-8 -*-
"""Аналитика (заглушка)."""
from app.config import settings


def analytics_enabled() -> bool:
    return getattr(settings, "ANALYTICS_ENABLED", False)
