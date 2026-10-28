import json
import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, render_template

BASE = Path(__file__).resolve().parent
app = Flask(__name__, template_folder="templates", static_folder="static")
ARQUIVO_DADOS = BASE / "cautelas.json"
LOCK = threading.Lock()


def carregar_cautelas():
    if not ARQUIVO_DADOS.exists():
        return []
    try:
        with ARQUIVO_DADOS.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return dados if isinstance(dados, list) else []
    except (OSError, json.JSONDecodeError):
        app.logger.exception("Não foi possível ler cautelas.json")
        return []


def salvar_cautelas(cautelas):
    temporario = ARQUIVO_DADOS.with_suffix(".json.tmp")
    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(cautelas, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, ARQUIVO_DADOS)


@app.get("/")
def intro():
    return render_template("index.html")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/1cia.png")
def logo():
    # Mantém compatibilidade com os caminhos usados nos HTMLs originais.
    return send_from_directory(app.static_folder, "1cia.png")


@app.get("/api/cautelas")
def listar():
    with LOCK:
        return jsonify(carregar_cautelas())


@app.post("/api/cautelas")
def criar():
    nova = request.get_json(silent=True)
    if not isinstance(nova, dict) or not nova:
        return jsonify({"erro": "Dados inválidos"}), 400

    with LOCK:
        cautelas = carregar_cautelas()
        nova["id"] = nova.get("id") or (
            str(int(datetime.now().timestamp() * 1000)) + "-" + os.urandom(3).hex()
        )
        nova["criadoEm"] = nova.get("criadoEm") or datetime.now().isoformat()
        cautelas.insert(0, nova)
        salvar_cautelas(cautelas)
    return jsonify(nova), 201


@app.delete("/api/cautelas/<cautela_id>")
def deletar(cautela_id):
    with LOCK:
        cautelas = carregar_cautelas()
        novas = [c for c in cautelas if c.get("id") != cautela_id]
        if len(novas) == len(cautelas):
            return jsonify({"erro": "Cautela não encontrada"}), 404
        salvar_cautelas(novas)
    return jsonify({"ok": True})


@app.put("/api/cautelas/<cautela_id>/devolucao")
def devolver(cautela_id):
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    with LOCK:
        cautelas = carregar_cautelas()
        for cautela in cautelas:
            if cautela.get("id") == cautela_id:
                cautela["status"] = "devolvida"
                cautela["devolucao"] = dados
                salvar_cautelas(cautelas)
                return jsonify(cautela)
    return jsonify({"erro": "Cautela não encontrada"}), 404


@app.get("/api/backup")
def backup():
    with LOCK:
        cautelas = carregar_cautelas()
    data_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    resposta = app.response_class(
        response=json.dumps(cautelas, ensure_ascii=False, indent=2),
        status=200,
        mimetype="application/json",
    )
    resposta.headers["Content-Disposition"] = (
        f'attachment; filename="backup_cautelas_{data_str}.json"'
    )
    return resposta


@app.post("/api/backup")
def importar_backup():
    dados = request.get_json(silent=True)
    if not isinstance(dados, list):
        return jsonify({"erro": "Formato inválido"}), 400
    modo = request.args.get("modo", "substituir")
    with LOCK:
        if modo == "mesclar":
            atuais = carregar_cautelas()
            ids_atuais = {c.get("id") for c in atuais}
            novas = [c for c in dados if isinstance(c, dict) and c.get("id") not in ids_atuais]
            todas = novas + atuais
        else:
            todas = dados
        salvar_cautelas(todas)
    return jsonify({"ok": True, "total": len(todas)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
