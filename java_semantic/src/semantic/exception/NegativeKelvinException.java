package semantic.exception;

/** Regla 3: Kelvin es una escala absoluta, no puede ser negativo (0K = cero absoluto). */
public class NegativeKelvinException extends SemanticException {
    public NegativeKelvinException() {
        super("Kelvin no admite valores negativos.", "Regla 3");
    }
}
