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
    "normalise_literals": NormaliseLiterals,
    "sort_in_list": SortInList,
    "normalise_predicates": NormalisePredicates,
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
            "normalise_literals",
            "sort_in_list",
            "normalise_predicates",
        ]
        self.hasher = Sha256Hash()
        self.hash_strategy = hash_strategy

    def _resolve_pass_name(self, name: str) -> str:
        """Resolve UK/US spellings to whatever exists in the registry."""
        key = name.strip().lower()
        if key in _PASS_REGISTRY:
            return key
        # flip normalise/normalize if needed
        if "normalise" in key:
            alt = key.replace("normalise", "normalize")
            if alt in _PASS_REGISTRY:
                return alt
        if "normalize" in key:
            alt = key.replace("normalize", "normalise")
            if alt in _PASS_REGISTRY:
                return alt
        # not found; let caller raise a clear error
        return key

    def _build_pipeline(self, names: list[str]):
        pipeline = []
        for name in names:
            resolved = self._resolve_pass_name(name)
            if resolved not in _PASS_REGISTRY:
                raise KeyError(f"Unknown normalisation pass: {name!r} (resolved: {resolved!r})")
            pipeline.append(_PASS_REGISTRY[resolved]())
        return pipeline

    def normalise(self, sql: str, cfg: Config | None = None) -> str:
        cfg = cfg or Config()
        pass_names = cfg.passes or self._default_pass_names
        pipeline = self._build_pipeline(pass_names)

        ast = self.parser.parse(sql)
        for p in pipeline:
            ast = p.apply(ast, cfg)

        result = ast.text

        ## NOTE: Ensure a single trailing newline so gold files match exactly in tests
        # if not result.endswith("\n"):
        #    result += "\n"
        return result

    def hash(self, sql: str, cfg: Config | None = None) -> str:
        cfg = cfg or Config()
        normalised = self.normalise(sql, cfg)
        return self.hasher.digest(AstNode(normalised), cfg)
