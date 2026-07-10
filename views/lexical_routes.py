from flask import Blueprint, request, jsonify

from controllers.compiler_controller import CompilerController


def create_lexical_blueprint():
    """Crea el blueprint Flask con el endpoint de análisis."""
    bp = Blueprint("lexical", __name__, url_prefix="/api")
    controller = CompilerController()

    @bp.route("/analyze", methods=["POST"])
    def analyze():
        if not request.is_json:
            return jsonify({"error": "El body debe ser JSON válido."}), 400

        data = request.get_json()

        if "source" not in data or not isinstance(data["source"], str):
            return jsonify({"error": "El campo 'source' es requerido y debe ser string."}), 401

        source = data["source"].strip()

        if not source:
            return jsonify({"error": "El campo 'source' no puede estar vacío."}), 401

        result = controller.analyze(source)

        semantic = result.get("semantic", {})

        if semantic.get("status") == "unavailable":
            return jsonify(result), 503

        if semantic.get("status") == "error":
            return jsonify(result), 502

        return jsonify(result), 200

    return bp
