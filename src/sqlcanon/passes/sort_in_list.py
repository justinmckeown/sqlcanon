import re

from ..config.model import Config
from ..protocols import AstNode
from .base import BasePass


class SortInList(BasePass):
    name = "sort_in_list"
    _in_clause_re = re.compile(r"\bIN\s*\(([^()]*)\)", flags=re.IGNORECASE)

    def _split_args(self, s: str) -> list[str]:
        # Split on commas not inside single quotes
        args = []
        buf = []
        in_str = False
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "'" and not in_str:
                in_str = True
                buf.append(ch)
            elif ch == "'" and in_str:
                # Handle escaped '' inside strings
                if i + 1 < len(s) and s[i + 1] == "'":
                    buf.append("''")
                    i += 1
                else:
                    in_str = False
                    buf.append(ch)
            elif ch == "," and not in_str:
                args.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
            i += 1
        if buf:
            args.append("".join(buf).strip())
        return [a for a in args if a != ""]

    def _sort_key(self, token: str):
        # Normalise quotes for sorting, but keep original in output
        t = token.strip()
        if t.startswith("'") and t.endswith("'"):
            inner = t[1:-1].replace("''", "'").lower()
            return (1, inner)  # strings after numbers for determinism
        try:
            # numeric key
            return (0, float(t))
        except ValueError:
            return (2, t.lower())

    def apply(self, ast: AstNode, cfg: Config) -> AstNode:
        def repl(m: re.Match) -> str:
            inside = m.group(1)
            items = self._split_args(inside)
            if len(items) <= 1:
                return m.group(0)
            items_sorted = sorted(items, key=self._sort_key)
            return f"IN ({', '.join(items_sorted)})"

        return AstNode(self._in_clause_re.sub(repl, ast.text))
