"""
Insured Microservice
"""

from .service import InsuredService
from .models import (
    Insured,
    InsuredCreate,
    InsuredUpdate,
    InsuredLocation,
    InsuredContact,
    InsuredSearchCriteria,
    InsuredSearchResult
)

__all__ = [
    "InsuredService",
    "Insured",
    "InsuredCreate",
    "InsuredUpdate",
    "InsuredLocation",
    "InsuredContact",
    "InsuredSearchCriteria",
    "InsuredSearchResult"
]