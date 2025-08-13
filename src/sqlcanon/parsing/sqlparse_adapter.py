from ..protocols import AstNode, QueryParser


class SqlParseAdapter(QueryParser):
    def parse(self, sql: str) -> AstNode:
        # placeholder: real impl would build/attach AST
        return AstNode(sql)
