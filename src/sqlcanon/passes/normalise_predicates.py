import re

from ..config.model import Config
from ..protocols import AstNode
from .base import BasePass


class NormalisePredicates(BasePass):
    name = "normalise_predicates"

    # Markers that typically end a WHERE clause
    _terminators = re.compile(
        r"\b(GROUP\s+BY|ORDER\s+BY|LIMIT|OFFSET|UNION|EXCEPT|INTERSECT)\b",
        flags=re.IGNORECASE,
    )

    def _contains_or_top_level(self, s: str) -> bool:
        # Detect ' OR ' not inside quotes/parentheses
        in_str = False
        depth = 0
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "'" and not in_str:
                in_str = True
            elif ch == "'" and in_str:
                if i + 1 < len(s) and s[i + 1] == "'":
                    i += 1  # skip escaped quote
                else:
                    in_str = False
            elif ch == "(" and not in_str:
                depth += 1
            elif ch == ")" and not in_str and depth > 0:
                depth -= 1
            # Check for OR at top level
            if depth == 0 and not in_str and s[i : i + 4].lower() == " or ":
                return True
            i += 1
        return False

    def _split_and_top_level(self, s: str) -> list[str]:
        parts: list[str] = []
        buf: list[str] = []
        in_str = False
        depth = 0
        i = 0
        lower = s.lower()
        while i < len(s):
            if not in_str and depth == 0 and lower[i : i + 5] == " and ":
                parts.append("".join(buf).strip())
                buf = []
                i += 5
                continue
            ch = s[i]
            if ch == "'" and not in_str:
                in_str = True
            elif ch == "'" and in_str:
                if i + 1 < len(s) and s[i + 1] == "'":
                    buf.append("''")
                    i += 1
                else:
                    in_str = False
            elif ch == "(" and not in_str:
                depth += 1
            elif ch == ")" and not in_str and depth > 0:
                depth -= 1
            buf.append(ch)
            i += 1
        if buf:
            parts.append("".join(buf).strip())
        return [p for p in parts if p != ""]

    def apply(self, ast: AstNode, cfg: Config) -> AstNode:
        text = ast.text
        # Find WHERE (first one only)
        m = re.search(r"\bWHERE\b", text, flags=re.IGNORECASE)
        if not m:
            return ast
        start = m.end()
        tail = text[start:]

        # Determine end of WHERE
        tmatch = self._terminators.search(tail)
        end = tmatch.start() if tmatch else len(tail)
        where_body = tail[:end]

        # Skip if OR appears at top level (to avoid changing semantics)
        if self._contains_or_top_level(" " + where_body + " "):
            return ast

        terms = self._split_and_top_level(" " + where_body + " ")
        if len(terms) <= 1:
            return ast

        terms_sorted = sorted(terms, key=lambda s: s.lower())
        new_where = " AND ".join(terms_sorted)

        new_text = text[:start] + " " + new_where + tail[end:]
        return AstNode(new_text)
