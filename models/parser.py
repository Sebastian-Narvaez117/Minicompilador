from typing import List, Dict, Any, Optional

from models.ast import ASTNode
from models.errors import ParserError, UnexpectedTokenError, MissingTokenError


class RecursiveDescentParser:
    """Analizador sintáctico descendente recursivo.
    Verifica que los tokens cumplan la gramática y construye el AST.

    Gramática:
      Programa       ::= Instruccion
      Instruccion    ::= CONVERTIR NUMERO UnidadOrigen PREPOSICION_A UnidadDestino
      UnidadOrigen   ::= UNIDAD_ORIGEN_C | UNIDAD_ORIGEN_F | UNIDAD_ORIGEN_K
      UnidadDestino  ::= UNIDAD_DESTINO_C | UNIDAD_DESTINO_F | UNIDAD_DESTINO_K
    """

    def __init__(self, tokens: List[Dict[str, Any]]):
        self.tokens = tokens
        self.position = 0
        self.current_token: Optional[Dict[str, Any]] = None
        self._advance()

    def _advance(self) -> None:
        """Avanza al siguiente token en la lista."""
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
            self.position += 1
        else:
            self.current_token = None

    def _expect(self, token_type: str) -> Dict[str, Any]:
        """Verifica que el token actual sea del tipo esperado y avanza."""
        if self.current_token is None:
            raise MissingTokenError(
                f"Se esperaba token '{token_type}' pero no hay más tokens.",
                token=None
            )

        if self.current_token["token"] == token_type:
            token = self.current_token
            self._advance()
            return token
        else:
            raise UnexpectedTokenError(
                f"Se esperaba token '{token_type}' pero se encontró '{self.current_token['token']}'.",
                token=self.current_token
            )

    def _peek(self) -> Optional[str]:
        """Observa el tipo del token actual sin consumirlo."""
        if self.current_token:
            return self.current_token["token"]
        return None

    def parse(self) -> ASTNode:
        """Punto de entrada: inicia el análisis desde <Programa>."""
        return self._parse_programa()

    def _parse_programa(self) -> ASTNode:
        programa = ASTNode("Programa")
        programa.add_child(self._parse_instruccion())
        return programa

    def _parse_instruccion(self) -> ASTNode:
        instruccion = ASTNode("Instruccion")

        convertir_token = self._expect("CONVERTIR")
        instruccion.add_child(ASTNode("CONVERTIR", value=convertir_token["lexeme"]))

        numero_token = self._expect("NUMERO")
        instruccion.add_child(ASTNode("NUMERO", value=numero_token["lexeme"]))

        instruccion.add_child(self._parse_unidad_origen())

        prep_token = self._expect("PREPOSICION_A")
        instruccion.add_child(ASTNode("PREPOSICION_A", value=prep_token["lexeme"]))

        instruccion.add_child(self._parse_unidad_destino())

        if self.current_token and self.current_token["token"] != "UNKNOWN":
            raise UnexpectedTokenError(
                f"Token inesperado después de la instrucción: '{self.current_token['token']}'.",
                token=self.current_token
            )

        return instruccion

    def _parse_unidad_origen(self) -> ASTNode:
        if self._peek() in ("UNIDAD_ORIGEN_C", "UNIDAD_ORIGEN_F", "UNIDAD_ORIGEN_K"):
            token = self._expect(self._peek())
            return ASTNode("UnidadOrigen", value=token["token"])
        else:
            raise UnexpectedTokenError(
                "Se esperaba una unidad de origen (UNIDAD_ORIGEN_C, UNIDAD_ORIGEN_F o UNIDAD_ORIGEN_K).",
                token=self.current_token
            )

    def _parse_unidad_destino(self) -> ASTNode:
        if self._peek() in ("UNIDAD_DESTINO_C", "UNIDAD_DESTINO_F", "UNIDAD_DESTINO_K"):
            token = self._expect(self._peek())
            return ASTNode("UnidadDestino", value=token["token"])
        else:
            raise UnexpectedTokenError(
                "Se esperaba una unidad de destino (UNIDAD_DESTINO_C, UNIDAD_DESTINO_F o UNIDAD_DESTINO_K).",
                token=self.current_token
            )
