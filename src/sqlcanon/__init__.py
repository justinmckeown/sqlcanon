from __future__ import annotations

from .config.model import Config
from .hashing.sha256_hash import Sha256Hash
from .parsing.sqlparse_adapter import SqlParseAdapter
from .passes.case_keywords import CaseFoldKeywords
from .passes.normalise_literals import NormaliseLiterals
from .passes.normalise_predicates import NormalisePredicates
from .passes.sort_in_list import SortInList
from .protocols import AstNode

_PASS_REGISTRY = {
    "case_keywords": CaseFoldKeywords,
    "normalize_literals": NormaliseLiterals,
    "sort_in_list": SortInList,
    "normalize_predicates": NormalisePredicates,
}


class Canonicalizer:
    """
    Facade that ties together: parser -> pass pipeline -> hash strategy.
    """

    def __init__(
        self,
        parser: str = "sqlparse",
        passes: list[str] | None = None,
        hash_strategy: str = "sha256",
    ):
        self.parser = SqlParseAdapter()  # simple factory for now
        self._default_pass_names = passes or [
            "case_keywords",
            "normalize_literals",
            "sort_in_list",
            "normalize_predicates",
        ]
        self.hasher = Sha256Hash()
        self.hash_strategy = hash_strategy

    def _build_pipeline(self, names: list[str]):
        return [_PASS_REGISTRY[name]() for name in names]

    def normalize(self, sql: str, cfg: Config | None = None) -> str:
        cfg = cfg or Config()
        pass_names = cfg.passes or self._default_pass_names
        pipeline = self._build_pipeline(pass_names)

        ast = self.parser.parse(sql)
        for p in pipeline:
            ast = p.apply(ast, cfg)
        return ast.text

    def hash(self, sql: str, cfg: Config | None = None) -> str:
        cfg = cfg or Config()
        normalized = self.normalize(sql, cfg)
        return self.hasher.digest(AstNode(normalized), cfg)
