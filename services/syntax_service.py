from models.parser import RecursiveDescentParser
from models.errors import ParserError


class SyntaxService:
    """Servicio de validación sintáctica.
    Usa el RecursiveDescentParser para validar tokens contra la gramática.
    Si hay error, clasifica si es 'incomplete' (falta un token) o 'invalid' (orden incorrecto).
    """

    def validate(self, tokens):
        """Valida la lista de tokens contra la gramática y retorna resultado con AST."""
        try:
            parser = RecursiveDescentParser(tokens)
            tree = parser.parse()

            return {
                "valid": True,
                "status": "correct",
                "message": "Instrucción sintácticamente correcta.",
                "missing": [],
                "tree": tree.to_dict()
            }

        except ParserError as e:
            status, message, missing = self._classify_error(tokens, e)

            return {
                "valid": False,
                "status": status,
                "message": message,
                "missing": missing,
                "tree": {}
            }

        except Exception as exc:
            return {
                "valid": False,
                "status": "error",
                "message": f"No se pudo validar la instrucción: {exc}",
                "missing": [],
                "tree": {}
            }

    def _classify_error(self, tokens, error):
        """Analiza qué token falta o está mal posicionado para dar un mensaje claro."""
        token_types = [str(token.get("token", "")).upper() for token in tokens if token.get("token")]

        if not token_types:
            return "incomplete", "No se reconocieron tokens en la instrucción.", ["CONVERTIR"]

        if "CONVERTIR" not in token_types:
            return "incomplete", "Falta la palabra 'convertir'.", ["CONVERTIR"]

        convert_index = token_types.index("CONVERTIR")
        number_index = next((i for i, token in enumerate(token_types) if token == "NUMERO"), None)
        origin_index = next((i for i, token in enumerate(token_types) if token.startswith("UNIDAD_ORIGEN_")), None)
        preposition_index = next((i for i, token in enumerate(token_types) if token == "PREPOSICION_A"), None)
        destination_index = next((i for i, token in enumerate(token_types) if token.startswith("UNIDAD_DESTINO_")), None)

        if convert_index != 0:
            return "invalid", "La instrucción debe comenzar con la palabra 'convertir'.", ["CONVERTIR"]

        if number_index is None:
            return "incomplete", "Falta el número a convertir.", ["NUMERO"]

        if origin_index is None:
            return "incomplete", "Falta la unidad de origen.", ["UNIDAD_ORIGEN"]

        if preposition_index is None:
            return "incomplete", "Falta la preposición 'a' entre la unidad de origen y la de destino.", ["PREPOSICION_A"]

        if destination_index is None:
            return "incomplete", "Falta la unidad de destino.", ["UNIDAD_DESTINO"]

        return "invalid", str(error), []
