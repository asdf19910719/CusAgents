from decimal import Decimal

from app.schemas.common import StrictSchema


class ReviewDecision(StrictSchema):
    result: str
    score: Decimal
    notes: str
