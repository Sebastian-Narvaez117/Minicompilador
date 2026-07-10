import unittest

from services.syntax_service import SyntaxService as SyntaxValidator


class SyntaxValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = SyntaxValidator()

    def test_incomplete_instruction_reports_missing_preposition(self):
        tokens = [
            {"token": "CONVERTIR", "lexeme": "convertir", "position": 0, "length": 9, "source": "AFD"},
            {"token": "NUMERO", "lexeme": "100", "position": 10, "length": 3, "source": "AFD"},
            {"token": "UNIDAD_ORIGEN_C", "lexeme": "celsius", "position": 14, "length": 7, "source": "AFD"},
            {"token": "UNIDAD_DESTINO_F", "lexeme": "fahrenheit", "position": 23, "length": 10, "source": "AFD"},
        ]

        result = self.validator.validate(tokens)

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("preposición", result["message"].lower())
        self.assertIn("PREPOSICION_A", result["missing"])

    def test_correct_instruction_is_marked_valid(self):
        tokens = [
            {"token": "CONVERTIR", "lexeme": "convertir", "position": 0, "length": 9, "source": "AFD"},
            {"token": "NUMERO", "lexeme": "100", "position": 10, "length": 3, "source": "AFD"},
            {"token": "UNIDAD_ORIGEN_C", "lexeme": "celsius", "position": 14, "length": 7, "source": "AFD"},
            {"token": "PREPOSICION_A", "lexeme": "a", "position": 22, "length": 1, "source": "AFD"},
            {"token": "UNIDAD_DESTINO_F", "lexeme": "fahrenheit", "position": 24, "length": 10, "source": "AFD"},
        ]

        result = self.validator.validate(tokens)

        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "correct")
        self.assertEqual(result["missing"], [])

    def test_case_insensitive_tokens_are_accepted(self):
        tokens = [
            {"token": "convertir", "lexeme": "convertir", "position": 0, "length": 9, "source": "AFD"},
            {"token": "numero", "lexeme": "100", "position": 10, "length": 3, "source": "AFD"},
            {"token": "unidad_origen_f", "lexeme": "fahrenheit", "position": 14, "length": 10, "source": "AFD"},
            {"token": "preposicion_a", "lexeme": "A", "position": 25, "length": 1, "source": "AFD"},
            {"token": "unidad_destino_k", "lexeme": "kelvin", "position": 27, "length": 6, "source": "AFD"},
        ]

        result = self.validator.validate(tokens)

        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "correct")


if __name__ == "__main__":
    unittest.main()
