from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .config.model import Config


class AstNode:  # simple placeholder
    def __init__(self, text: str):
        self.text = text


class QueryParser(Protocol):
    def parse(self, sql: str) -> AstNode: ...


class NormalizationPass(Protocol):
    def apply(self, ast: AstNode, cfg: "Config") -> AstNode: ...


class HashComputer(Protocol):
    def digest(self, ast: AstNode, cfg: "Config") -> str: ...
