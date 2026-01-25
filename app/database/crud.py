# -*- coding: utf-8 -*-
"""
CRUD-операции. Сейчас — обёртка над models (aiosqlite).
"""
from app.database.models import UserModel, AdModel, SwapModel, RatingModel, FavoriteModel

__all__ = ["UserModel", "AdModel", "SwapModel", "RatingModel", "FavoriteModel"]
