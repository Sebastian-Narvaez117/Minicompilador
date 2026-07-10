class ASTNode:
    """Nodo del Árbol de Sintaxis Abstracta (AST).
    El parser construye un árbol con esta estructura:
      Programa → Instruccion → [CONVERTIR, NUMERO, UnidadOrigen, PREPOSICION_A, UnidadDestino]
    """

    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def to_dict(self):
        """Convierte el nodo y sus hijos a un diccionario JSON serializable."""
        node = {
            "type": self.name,
            "name": self.name,
            "children": [child.to_dict() for child in self.children]
        }

        if self.value is not None:
            node["value"] = self.value

        return node
