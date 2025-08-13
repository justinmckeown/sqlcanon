import re

from ..config.model import Config
from ..protocols import AstNode
from .base import BasePass


class CaseFoldKeywords(BasePass):
    name = "case_keywords"
    SQL_KEYWORDS = {
        "select",
        "from",
        "where",
        "and",
        "or",
        "in",
        "join",
        "on",
        "as",
        "group",
        "by",
        "order",
        "limit",
    }

    def apply(self, ast: AstNode, cfg: Config) -> AstNode:
        def repl(m):
            kw = m.group(0)
            return kw.upper() if cfg.keyword_case == "upper" else kw.lower()

        pattern = r"\b(" + "|".join(self.SQL_KEYWORDS) + r")\b"
        return AstNode(re.sub(pattern, repl, ast.text, flags=re.IGNORECASE))
