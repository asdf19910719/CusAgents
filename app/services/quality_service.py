from decimal import Decimal


class QualityResult:
    def __init__(self, result, notes, score):
        self.result = result
        self.notes = notes
        self.score = score


class ManualReview:
    def __init__(self, result, notes, reviewed_by, score=Decimal("1.00")):
        self.result = result
        self.notes = notes
        self.reviewed_by = reviewed_by
        self.score = score


class QualityService:
    def validate_generation(self, storyboard, prompts, assets):
        if len(storyboard.shots) != len(prompts):
            return QualityResult("failed", "prompt count mismatch", Decimal("0.00"))
        if len(storyboard.shots) != len(assets):
            return QualityResult("failed", "asset count mismatch", Decimal("0.00"))
        for asset in assets:
            status = asset.get("status") if isinstance(asset, dict) else getattr(asset, "status", None)
            if status != "completed":
                return QualityResult("failed", "asset generation failed", Decimal("0.00"))
        for prompt in prompts:
            if not prompt.positive_prompt or not prompt.negative_prompt:
                return QualityResult("failed", "empty prompt detected", Decimal("0.00"))
        return QualityResult("passed", "ok", Decimal("1.00"))

    def build_manual_review(self, result, notes, reviewed_by):
        return ManualReview(result=result, notes=notes, reviewed_by=reviewed_by)
