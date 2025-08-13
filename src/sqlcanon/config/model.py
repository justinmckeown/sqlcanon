from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Config:
    keyword_case: Literal["upper", "lower"] = "upper"
    identifier_case: Literal["as_is", "upper", "lower"] = "as_is"
    passes: list[str] | None = None
    hash_strategy: str = "sha256"
