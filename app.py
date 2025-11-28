from __future__ import annotations

import ast
import operator
import re
import secrets
from typing import Callable, Dict, Optional

from flask import Flask, jsonify, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)


# --- Calculator core ---------------------------------------------------------

ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

ALLOWED_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

# Simple in-memory user store for demo auth
USER_STORE: Dict[str, str] = {}


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BIN_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY_OPS:
        return ALLOWED_UNARY_OPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("Unsupported expression")


def safe_eval_expression(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Constant,
                ast.Load,
                ast.Pow,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.Mod,
                ast.UAdd,
                ast.USub,
            ),
        ):
            continue
        raise ValueError("Unsupported token")
    return _eval_ast(tree)


def ai_guess_operation(text: str) -> Optional[Callable[[float, float], float]]:
    cleaned = text.lower()
    if any(word in cleaned for word in ["sum", "suma", "add", "mas"]):
        return operator.add
    if any(word in cleaned for word in ["resta", "sub", "menos"]):
        return operator.sub
    if any(word in cleaned for word in ["multiplica", "multiplicacion", "por", "producto", "x"]):
        return operator.mul
    if any(word in cleaned for word in ["divide", "division", "entre", "sobre", "dividir"]):
        return operator.truediv
    return None


def ai_resolve(text: str) -> float:
    numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
    operation = ai_guess_operation(text)
    if operation and len(numbers) >= 2:
        return operation(numbers[0], numbers[1])

    return safe_eval_expression(text)


# --- Auth helpers -----------------------------------------------------------


def _validate_credentials(payload: dict) -> tuple[str, str]:
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if len(username) < 3 or len(password) < 6:
        raise ValueError("Usuario (>=3) y clave (>=6) son requeridos")
    return username, password


def register_user(username: str, password: str) -> None:
    if username in USER_STORE:
        raise ValueError("El usuario ya existe")
    USER_STORE[username] = generate_password_hash(password)


def login_user(username: str, password: str) -> str:
    hashed = USER_STORE.get(username)
    if not hashed or not check_password_hash(hashed, password):
        raise ValueError("Credenciales invalidas")
    return secrets.token_hex(16)


# --- HTTP interface ----------------------------------------------------------

@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/calc", methods=["POST"])
def calculate():
    payload = request.get_json(silent=True) or {}
    user_input = payload.get("input")
    if not user_input or not isinstance(user_input, str):
        return (
            jsonify({"error": "Se requiere el campo 'input' con una expresion o pregunta."}),
            400,
        )

    try:
        result = ai_resolve(user_input)
    except Exception:
        return (
            jsonify({"error": "No pude interpretar la operacion. Intenta con otra frase o expresion."}),
            400,
        )

    mode = "nlp" if ai_guess_operation(user_input) else "expression"
    return jsonify({"input": user_input, "mode": mode, "result": result})


@app.route("/api/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    try:
        username, password = _validate_credentials(payload)
        register_user(username, password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": "Usuario creado", "username": username}), 201


@app.route("/api/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    try:
        username, password = _validate_credentials(payload)
        token = login_user(username, password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401

    return jsonify({"message": "Login exitoso", "token": token, "username": username})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
