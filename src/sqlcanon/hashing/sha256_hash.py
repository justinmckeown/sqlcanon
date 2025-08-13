import hashlib

from ..protocols import AstNode, HashComputer


class Sha256Hash(HashComputer):
    def digest(self, ast: AstNode, cfg) -> str:
        data = ast.text.encode("utf-8")  # replace with stable AST serialization later
        return hashlib.sha256(data).hexdigest()
