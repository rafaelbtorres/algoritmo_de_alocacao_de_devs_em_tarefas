"""API e interface do laboratorio. Execute com gunicorn web.app:app."""
import json
import os
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit

from flask import Flask, jsonify, render_template, request
from pymysql import MySQLError
from werkzeug.exceptions import HTTPException

from app.db import connect
from app.main import load_data, save_result
from app.matching import allocate, validate_config, score_matrix, prepare_problem, evaluate_pair

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / 'config/critérios.json'
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024


def read_config():
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def payload_config():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError('Envie a configuracao como objeto JSON.')
    validate_config(data)
    return data


def dataset(config):
    started = perf_counter()
    developers, tasks = load_data(config, limit=500)
    if len(developers) > 200 or len(tasks) > 500:
        raise ValueError('Selecione um projeto ou sprint menor: o laboratorio visual aceita ate 200 devs e 500 tarefas.')
    return developers, tasks, (perf_counter() - started) * 1000


@app.get('/')
def index():
    host = urlsplit(request.host_url).hostname
    if ':' in host:
        host = f'[{host}]'
    port = int(os.environ.get('PHPMYADMIN_PORT', '8081'))
    return render_template('index.html', phpmyadmin_url=f'http://{host}:{port}/')


@app.get('/api/health')
def health():
    return jsonify(status='ok')


@app.get('/api/inicio')
def bootstrap():
    config = read_config()
    validate_config(config)
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT ID, Name FROM Project ORDER BY ID')
            projects = cursor.fetchall()
            cursor.execute('SELECT ID, Name, Project_ID FROM Sprint ORDER BY Start_Date, ID')
            sprints = cursor.fetchall()
    areas = json.loads((ROOT / 'config/areas.json').read_text(encoding='utf-8'))
    return jsonify(config=config, projetos=projects, sprints=sprints, areas=areas)


@app.post('/api/dados')
def data():
    config = payload_config()
    developers, tasks, elapsed = dataset(config)
    return jsonify(devs=developers, tarefas=tasks, leitura_ms=elapsed)


@app.post('/api/alocar')
def run():
    config = payload_config()
    developers, tasks, elapsed = dataset(config)
    result = allocate(developers, tasks, config, trace=True)
    result['metricas']['leitura_ms'] = elapsed
    result['projeto_id'] = config.get('projeto_id')
    result['sprint_id'] = config.get('sprint_id')
    # A execucao usa exatamente esta configuracao; nao sobrescreve a configuracao salva.
    return jsonify(resultado=result, devs=developers, tarefas=tasks, config=config)


@app.post('/api/matriz')
def matrix():
    config = payload_config()
    developers, tasks, _ = dataset(config)
    developers, tasks, scores = score_matrix(developers, tasks, config)
    return jsonify(matriz=scores, devs=developers, tarefas=tasks)


@app.post('/api/comparar')
def compare():
    config = payload_config()
    # Uma unica leitura fornece o mesmo recorte e a mesma ordem aos dois metodos.
    developers, tasks, elapsed = dataset(config)
    results = {}
    for algorithm in ('bfs', 'scipy'):
        result = allocate(developers, tasks, {**config, 'algoritmo': algorithm}, trace=False)
        result['metricas']['leitura_ms'] = elapsed
        results[algorithm] = result
    return jsonify(resultados=results, config=config,
                   observacao='Mesmos dados e criterios; tempos sem registro de passos e sem animacao. Uma execucao por metodo; os tempos podem variar.')


@app.post('/api/par')
def pair_details():
    payload = request.get_json()
    if not isinstance(payload, dict):
        raise ValueError('Envie configuracao e IDs do par.')
    config = payload.get('config')
    validate_config(config)
    developers, tasks, _ = dataset(config)
    developers, tasks, *context = prepare_problem(developers, tasks, config)
    dev = next((d for d in developers if d['ID'] == payload.get('dev_id')), None)
    task = next((t for t in tasks if t['ID'] == payload.get('tarefa_id')), None)
    if dev is None or task is None:
        raise ValueError('Par fora do recorte selecionado.')
    return jsonify(dev_id=dev['ID'], tarefa_id=task['ID'], **evaluate_pair(dev, task, config, *context))


@app.put('/api/criterios')
def save_config():
    config = payload_config()
    # Verifica os dados manuais quando os criterios que os exigem estiverem ativos.
    developers, tasks, _ = dataset(config)
    allocate(developers, tasks, config)
    save_result(config, CONFIG_PATH)
    return jsonify(mensagem='Criterios salvos em config/critérios.json.')


@app.before_request
def same_origin():
    # O painel local nao precisa aceitar requisicoes de outras paginas.
    if request.method in ('POST', 'PUT', 'DELETE'):
        from urllib.parse import urlsplit
        origin = request.headers.get('Origin')
        if origin and urlsplit(origin).netloc != request.host:
            return jsonify(erro='Origem da requisicao nao permitida.'), 403


@app.errorhandler(ValueError)
def invalid(error):
    return jsonify(erro=str(error)), 400


@app.errorhandler(MySQLError)
def database_error(error):
    app.logger.warning('Falha de acesso ao banco: %s', type(error).__name__)
    return jsonify(erro='Nao foi possivel ler o dataset. Confira o MySQL e importe o SQL pelo menu 3 → 1.'), 503


@app.errorhandler(OSError)
def file_error(error):
    app.logger.warning('Falha de arquivo: %s', type(error).__name__)
    return jsonify(erro='Nao foi possivel ler ou salvar a configuracao. Confira os arquivos e as permissoes do projeto.'), 500


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(erro=error.description), error.code
