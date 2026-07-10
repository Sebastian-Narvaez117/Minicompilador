class ParserError(Exception):
    """Excepción base para errores del analizador sintáctico."""

    def __init__(self, message: str, token: dict = None):
        self.message = message
        self.token = token
        super().__init__(self.message)

    def to_dict(self) -> dict:
        result = {"message": self.message}
        if self.token:
            result["token"] = self.token
        return result


class UnexpectedTokenError(ParserError):
    """Se encontró un token que no coincide con lo esperado por la gramática.
    Ejemplo: se esperaba PREPOSICION_A pero se encontró UNIDAD_DESTINO_F.
    """


class MissingTokenError(ParserError):
    """Falta un token requerido por la gramática.
    Ejemplo: se esperaba NUMERO después de CONVERTIR pero no hay más tokens.
    """
