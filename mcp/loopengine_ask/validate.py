"""Validate AskUserQuestion tool arguments."""

RECOMMENDED_MARKERS = ("(推荐)", "(Recommended)", "(recommended)")


class ValidationError(ValueError):
    """Raised when AskUserQuestion arguments fail schema validation."""


def _has_recommended_marker(label: str) -> bool:
    return any(marker in label for marker in RECOMMENDED_MARKERS)


def _normalize_option(raw: dict) -> dict:
    label = raw.get("label", "")
    if not label:
        raise ValidationError("validation_error: option label is required")

    recommended = bool(raw.get("recommended", False)) or _has_recommended_marker(label)

    return {
        "id": raw.get("id", label),
        "label": label,
        "description": raw.get("description", ""),
        "recommended": recommended,
    }


def validate_ask_args(args: dict) -> dict:
    """Validate and normalize AskUserQuestion arguments."""
    question = args.get("question", "")
    if not isinstance(question, str) or not question.strip():
        raise ValidationError("validation_error: question is required")

    raw_options = args.get("options")
    if not isinstance(raw_options, list):
        raise ValidationError("validation_error: options must be a list")

    if len(raw_options) < 2 or len(raw_options) > 4:
        raise ValidationError("validation_error: options must contain 2-4 items")

    options = [_normalize_option(opt) for opt in raw_options]

    if not any(o["recommended"] for o in options):
        raise ValidationError("validation_error: at least one option must be recommended")

    return {
        "question": question.strip(),
        "options": options,
        "multiSelect": bool(args.get("multiSelect", False)),
    }
