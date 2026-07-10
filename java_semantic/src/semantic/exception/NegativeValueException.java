package semantic.exception;

/** Regla 2: El número de la conversión debe ser mayor que cero. */
public class NegativeValueException extends SemanticException {
    public NegativeValueException() {
        super("La cantidad debe ser mayor que cero.", "Regla 2");
    }
}
