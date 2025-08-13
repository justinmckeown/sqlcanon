import re

from ..config.model import Config
from ..protocols import AstNode
from .base import BasePass


class NormaliseLiterals(BasePass):
    name = "normalize_literals"

    # Single-quoted SQL strings, handling escaped '' inside.
    _string_re = re.compile(r"'(?:''|[^'])*'")
    # Integer/float numbers not inside identifiers
    _number_re = re.compile(r"\b\d+(?:\.\d+)?\b")

    def apply(self, ast: AstNode, cfg: Config) -> AstNode:
        text = ast.text

        # Replace strings first so numbers inside strings are untouched
        text = self._string_re.sub("'__STR__'", text)
        # Replace standalone numbers
        text = self._number_re.sub("__NUM__", text)

        return AstNode(text)
