"""Le dados do TAWOS e gera uma proposta de alocacao sem alterar o banco."""
import argparse
import json
from pathlib import Path
import tempfile
import sys

from pymysql import MySQLError

from app.db import connect
from app.matching import allocate, validate_config

ROOT = Path(__file__).resolve().parents[1]


def load_data(config, limit=None):
    validate_config(config)

    def fetch_limit(key):
        requested = config.get(key)
        if limit is None:
            return requested
        return limit + 1 if requested is None else min(requested, limit + 1)

    with connect() as connection:
        with connection.cursor() as cursor:
            project = config.get('projeto_id')
            query = 'SELECT ID, Project_ID FROM `User`'
            params = []
            if project is not None:
                query += ' WHERE Project_ID=%s'
                params.append(project)
            query += ' ORDER BY ID'
            dev_limit = fetch_limit('quantidade_devs')
            if dev_limit is not None:
                query += ' LIMIT %s'
                params.append(dev_limit)
            cursor.execute(query, params)
            developers = cursor.fetchall()
            conditions, params = [], []
            for column, key in (('Project_ID', 'projeto_id'), ('Sprint_ID', 'sprint_id')):
                if config.get(key) is not None:
                    conditions.append(f'{column}=%s')
                    params.append(config[key])
            query = 'SELECT ID, Issue_Key, Title, Project_ID, Sprint_ID, Story_Point, Assignee_ID, Status, Priority FROM Issue'
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            query += ' ORDER BY ID'
            task_limit = fetch_limit('quantidade_tarefas')
            if task_limit is not None:
                query += ' LIMIT %s'
                params.append(task_limit)
            cursor.execute(query, params)
            tasks = cursor.fetchall()
    return developers, tasks


def save_result(result, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
        temporary.chmod(0o644)
        temporary.replace(output)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/critérios.json')
    parser.add_argument('--saida', type=Path, default=ROOT / 'resultados/alocacao.json')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('A configuracao deve ser um objeto JSON.')
    validate_config(config)
    developers, tasks = load_data(config)
    result = allocate(developers, tasks, config)
    result['projeto_id'] = config.get('projeto_id')
    result['sprint_id'] = config.get('sprint_id')
    save_result(result, args.saida)
    print('\n=== Alocacao de desenvolvedores ===')
    print(f'Desenvolvedores: {len(developers)} | Tarefas: {len(tasks)}')
    reverse = result['direcao'] == 'tarefas_para_devs'
    print('Direcao: ' + ('tarefas -> desenvolvedores' if reverse else 'desenvolvedores -> tarefas'))
    print('Limite: uma tarefa por desenvolvedor e um desenvolvedor por tarefa nesta execucao.')
    for row in result['alocacoes']:
        origin = f"Dev {row['dev_id']}"
        target = str(row['tarefa'] or row['tarefa_id'])
        if reverse:
            origin, target = target, origin
        print(f"{origin} -> {target} (sprint {row['sprint_id']})")
    print(f"Alocacoes: {len(result['alocacoes'])}")
    print(f"Devs sem tarefa: {len(result['devs_sem_tarefa'])} | Tarefas sem dev: {len(result['tarefas_sem_dev'])}")
    if not developers or not tasks:
        print('Nenhum par possivel. Confira a importacao do dataset e os filtros da configuracao.')
    print(f'Resultado salvo em: {args.saida}')
    print('Proposta gerada. As atribuicoes historicas no banco foram preservadas.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, MySQLError) as error:
        print(f'Erro na alocacao: {error}', file=sys.stderr)
        raise SystemExit(1)
