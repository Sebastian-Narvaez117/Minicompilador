package semantic.exception;

/** Regla 1/4: La unidad de origen y destino son la misma (ej: celsius -> celsius). */
public class SameUnitException extends SemanticException {
    public SameUnitException() {
        super("La unidad origen y destino son iguales.", "Regla 1 / Regla 4");
    }
}
