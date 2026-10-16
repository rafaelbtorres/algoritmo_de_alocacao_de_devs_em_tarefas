"""Le dados do TAWOS e gera uma proposta de alocacao sem alterar o banco."""
import argparse
import json
from pathlib import Path
import tempfile
import sys
from time import perf_counter

# Quando executado como `python app/main.py`, o Python coloca `app/` no
# caminho de importacao. Inclui a raiz do projeto para localizar o pacote `app`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pymysql import MySQLError

from app.db import connect
from app.matching import allocate, select_participants, validate_config

def load_data(config, limit=None):
    validate_config(config)
    for key in ('quantidade_projetos', 'quantidade_sprints'):
        value = config.get(key)
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f'{key} deve ser um inteiro positivo ou null.')

    def fetch_limit(key):
        requested = config.get(key)
        if limit is None:
            return requested
        return limit + 1 if requested is None else min(requested, limit + 1)

    with connect() as connection:
        with connection.cursor() as cursor:
            project = config.get('projeto_id')
            project_ids = None
            if config.get('quantidade_projetos') is not None:
                query = 'SELECT ID FROM Project'
                params = []
                if project is not None:
                    query += ' WHERE ID=%s'
                    params.append(project)
                query += ' ORDER BY ID LIMIT %s'
                params.append(config['quantidade_projetos'])
                cursor.execute(query, params)
                project_ids = [row['ID'] for row in cursor.fetchall()]

            def project_filter():
                if project_ids is not None:
                    if not project_ids:
                        return '1=0', []
                    placeholders = ', '.join(['%s'] * len(project_ids))
                    return f'Project_ID IN ({placeholders})', list(project_ids)
                if project is not None:
                    return 'Project_ID=%s', [project]
                return '', []

            sprint_ids = None
            if config.get('quantidade_sprints') is not None:
                condition, params = project_filter()
                conditions = [condition] if condition else []
                if config.get('sprint_id') is not None:
                    conditions.append('ID=%s')
                    params.append(config['sprint_id'])
                query = 'SELECT ID FROM Sprint'
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                query += ' ORDER BY ID LIMIT %s'
                params.append(config['quantidade_sprints'])
                cursor.execute(query, params)
                sprint_ids = [row['ID'] for row in cursor.fetchall()]

            query = 'SELECT ID, Project_ID FROM `User`'
            condition, params = project_filter()
            if condition:
                query += ' WHERE ' + condition
            query += ' ORDER BY ID'
            dev_limit = fetch_limit('quantidade_devs')
            if dev_limit is not None:
                query += ' LIMIT %s'
                params.append(dev_limit)
            cursor.execute(query, params)
            developers = cursor.fetchall()
            condition, params = project_filter()
            conditions = [condition] if condition else []
            if sprint_ids is not None:
                if sprint_ids:
                    placeholders = ', '.join(['%s'] * len(sprint_ids))
                    conditions.append(f'Sprint_ID IN ({placeholders})')
                    params.extend(sprint_ids)
                else:
                    conditions.append('1=0')
            elif config.get('sprint_id') is not None:
                conditions.append('Sprint_ID=%s')
                params.append(config['sprint_id'])
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
    return select_participants(developers, tasks, config)


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


def positive_integer(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Informe um inteiro positivo.') from None
    if number < 1:
        raise argparse.ArgumentTypeError('Informe um inteiro positivo.')
    return number


def main():
    execution_started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/critérios.json')
    parser.add_argument('--saida', type=Path, default=ROOT / 'resultados/alocacao.json')
    for short, long, key, help_text in (
        ('-d', '--devs', 'quantidade_devs', 'Quantidade maxima de desenvolvedores'),
        ('-t', '--tarefas', 'quantidade_tarefas', 'Quantidade maxima de tarefas'),
        ('-s', '--sprints', 'quantidade_sprints', 'Quantidade maxima de sprints, por ID crescente'),
        ('-p', '--projetos', 'quantidade_projetos', 'Quantidade maxima de projetos, por ID crescente'),
    ):
        parser.add_argument(short, long, dest=key, type=positive_integer, help=help_text)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('A configuracao deve ser um objeto JSON.')
    for key in ('quantidade_devs', 'quantidade_tarefas', 'quantidade_sprints', 'quantidade_projetos'):
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    validate_config(config)
    developers, tasks = load_data(config)
    result = allocate(developers, tasks, config)
    result['projeto_id'] = config.get('projeto_id')
    result['sprint_id'] = config.get('sprint_id')
    for key in ('quantidade_sprints', 'quantidade_projetos'):
        if config.get(key) is not None:
            result[key] = config[key]
    save_result(result, args.saida)
    print('\n=== Alocacao de desenvolvedores ===')
    print(f"Algoritmo: {result['algoritmo']}")
    print(f"Objetivo: {result['objetivo']}")
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
    print(f"Alocacoes: {len(result['alocacoes'])} | Pontuacao total: {result['pontuacao_total']:.2f}")
    print(f"Devs sem tarefa: {len(result['devs_sem_tarefa'])} | Tarefas sem dev: {len(result['tarefas_sem_dev'])}")
    print(f'Tempo total da execucao: {perf_counter() - execution_started:.2f} segundos')
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
