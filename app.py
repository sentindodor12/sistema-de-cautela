import os
import json
import socket
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE, static_url_path='')

ARQUIVO_DADOS = os.path.join(BASE, 'cautelas.json')
LOCK = threading.Lock()


def carregar_cautelas():
    if not os.path.exists(ARQUIVO_DADOS):
        return []
    try:
        with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def salvar_cautelas(cautelas):
    temp = ARQUIVO_DADOS + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        json.dump(cautelas, f, ensure_ascii=False, indent=2)
    os.replace(temp, ARQUIVO_DADOS)


def ler_html(nome):
    caminho = os.path.join(BASE, nome)
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read()


# ============ ROTAS ============

@app.route('/')
def intro():
    return render_template_string(ler_html('index.html'))


@app.route('/dashboard')
def dashboard():
    return render_template_string(ler_html('dashboard.html'))


@app.route('/1cia.png')
def logo():
    return send_from_directory(BASE, '1cia.png')


@app.route('/api/cautelas', methods=['GET'])
def listar():
    with LOCK:
        return jsonify(carregar_cautelas())


@app.route('/api/cautelas', methods=['POST'])
def criar():
    nova = request.get_json()
    if not nova:
        return jsonify({'erro': 'Dados inválidos'}), 400
    with LOCK:
        cautelas = carregar_cautelas()
        nova['id'] = nova.get('id') or (
            str(int(datetime.now().timestamp() * 1000)) + '-' + os.urandom(3).hex()
        )
        nova['criadoEm'] = nova.get('criadoEm') or datetime.now().isoformat()
        cautelas.insert(0, nova)
        salvar_cautelas(cautelas)
    return jsonify(nova), 201


@app.route('/api/cautelas/<cautela_id>', methods=['DELETE'])
def deletar(cautela_id):
    with LOCK:
        cautelas = carregar_cautelas()
        novas = [c for c in cautelas if c.get('id') != cautela_id]
        if len(novas) == len(cautelas):
            return jsonify({'erro': 'Cautela não encontrada'}), 404
        salvar_cautelas(novas)
    return jsonify({'ok': True})


@app.route('/api/cautelas/<cautela_id>/devolucao', methods=['PUT'])
def devolver(cautela_id):
    dados = request.get_json()
    if not dados:
        return jsonify({'erro': 'Dados inválidos'}), 400
    with LOCK:
        cautelas = carregar_cautelas()
        for c in cautelas:
            if c.get('id') == cautela_id:
                c['status'] = 'devolvida'
                c['devolucao'] = dados
                salvar_cautelas(cautelas)
                return jsonify(c)
    return jsonify({'erro': 'Cautela não encontrada'}), 404


@app.route('/api/backup', methods=['GET'])
def backup():
    with LOCK:
        cautelas = carregar_cautelas()
    data_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
    return (
        json.dumps(cautelas, ensure_ascii=False, indent=2),
        200,
        {
            'Content-Type': 'application/json; charset=utf-8',
            'Content-Disposition': f'attachment; filename="backup_cautelas_{data_str}.json"'
        }
    )


@app.route('/api/backup', methods=['POST'])
def importar_backup():
    dados = request.get_json()
    if not isinstance(dados, list):
        return jsonify({'erro': 'Formato inválido'}), 400
    modo = request.args.get('modo', 'substituir')
    with LOCK:
        if modo == 'mesclar':
            atuais = carregar_cautelas()
            ids_atuais = {c.get('id') for c in atuais}
            novas = [c for c in dados if c.get('id') not in ids_atuais]
            todas = novas + atuais
        else:
            todas = dados
        salvar_cautelas(todas)
    return jsonify({'ok': True, 'total': len(todas)})


# ============ INICIAR ============

def pegar_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    ip = pegar_ip_local()
    print('\n' + '=' * 60)
    print('  SISTEMA DE CAUTELAS — ENC MAT 1ª CIA')
    print('=' * 60)
    print(f'  No seu PC:      http://localhost:5000')
    print(f'  Nos celulares:  http://{ip}:5000')
    print('  (todos na mesma rede Wi-Fi)')
    print('=' * 60 + '\n')
    app.run(host='0.0.0.0', port=5000, debug=False)