from ..config.model import Config
from ..protocols import AstNode


class BasePass:
    name = "base"

    def apply(self, ast: AstNode, cfg: Config) -> AstNode:
        return ast
