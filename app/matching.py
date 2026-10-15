"""Matching bipartido: no maximo uma tarefa por dev e um dev por tarefa."""
import math
from collections import deque
from time import perf_counter

import networkx as nx


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('A configuracao deve ser um objeto JSON.')
    if config.get('direcao', 'devs_para_tarefas') not in ('devs_para_tarefas', 'tarefas_para_devs'):
        raise ValueError('direcao deve ser devs_para_tarefas ou tarefas_para_devs.')
    for key in ('projeto_id', 'sprint_id', 'quantidade_devs', 'quantidade_tarefas'):
        value = config.get(key)
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f'{key} deve ser um inteiro positivo ou null.')
    criteria = config.get('criterios', {})
    if not isinstance(criteria, dict):
        raise ValueError('criterios deve ser um objeto JSON.')
    allowed = {'mesmo_projeto', 'max_story_points_por_tarefa', 'habilidades', 'disponibilidade'}
    if set(criteria) - allowed:
        raise ValueError(f'Criterios desconhecidos: {sorted(set(criteria) - allowed)}')
    for key in ('mesmo_projeto', 'habilidades', 'disponibilidade'):
        if type(criteria.get(key, False)) is not bool:
            raise ValueError(f'{key} deve ser true ou false.')
    limit = criteria.get('max_story_points_por_tarefa')
    if limit is not None and (type(limit) not in (int, float) or not math.isfinite(limit) or limit < 0):
        raise ValueError('max_story_points_por_tarefa deve ser um numero finito >= 0 ou null.')
    for key in ('dados_devs', 'habilidades_tarefas'):
        if not isinstance(config.get(key, {}), dict):
            raise ValueError(f'{key} deve ser um objeto JSON.')


def skill_set(value, label):
    if not isinstance(value, list) or any(not isinstance(skill, str) for skill in value):
        raise ValueError(f'{label} deve ser uma lista de habilidades.')
    return {skill.strip().casefold() for skill in value}


def matching_with_steps(graph, left, capture=False):
    """Busca caminhos aumentantes por BFS e registra as operacoes realmente feitas."""
    matches, events = {}, []
    checked = 0
    started = perf_counter()

    def emit(kind, **data):
        if capture:
            events.append({'tipo': kind, 'tempo_ms': (perf_counter() - started) * 1000, **data})

    def pair(first, second):
        dev, task = (first, second) if first[0] == 'dev' else (second, first)
        return {'dev_id': dev[1], 'tarefa_id': task[1]}

    for root in left:
        root_field = {'dev_id' if root[0] == 'dev' else 'tarefa_id': root[1]}
        root_label = f'dev {root[1]}' if root[0] == 'dev' else f'tarefa {root[1]}'
        target_label = 'uma tarefa' if root[0] == 'dev' else 'um dev'
        emit('buscar', **root_field, mensagem=f'Buscando {target_label} para {root_label}.')
        queue, visited, parent = deque([root]), set(), {}
        free = None
        while queue and free is None:
            node = queue.popleft()
            for target in graph[node]:
                if target in visited:
                    continue
                visited.add(target)
                parent[target] = node
                checked += 1
                current_pair = pair(node, target)
                emit('avaliar', **current_pair,
                     mensagem=f"Avaliando o par dev {current_pair['dev_id']} e tarefa {current_pair['tarefa_id']}.")
                if target not in matches:
                    free = target
                    break
                partner = matches[target]
                occupied = pair(partner, target)
                explanation = (f"Tarefa ocupada pelo dev {occupied['dev_id']}" if target[0] == 'tarefa'
                               else f"Dev ja alocado a tarefa {occupied['tarefa_id']}")
                emit('ocupada', **occupied, mensagem=explanation + '; procurando um caminho alternativo.')
                queue.append(partner)
        if free is None:
            emit('sem_par', **root_field, mensagem=f'Nenhum caminho disponivel para {root_label}.')
            continue
        path = []
        while free is not None:
            node = parent[free]
            previous = matches.get(node)
            matches[node] = free
            matches[free] = node
            path.append(pair(node, free))
            free = previous
        emit('alocar', **root_field, caminho=list(reversed(path)),
             pares=[pair(node, matches[node]) for node in left if node in matches],
             mensagem='Caminho aumentante aplicado: mais uma tarefa alocada.')
    emit('concluir', mensagem='Busca concluida. O matching tem a maior quantidade possivel de pares validos.')
    return matches, events, checked


def select_participants(developers, tasks, config):
    """Escolhe ate N registros por grupo, em ordem de ID, antes da compatibilidade."""
    validate_config(config)
    return (sorted(developers, key=lambda dev: dev['ID'])[:config.get('quantidade_devs')],
            sorted(tasks, key=lambda task: task['ID'])[:config.get('quantidade_tarefas')])


def allocate(developers, tasks, config, trace=False):
    started = perf_counter()
    validate_config(config)
    developers, tasks = select_participants(developers, tasks, config)
    criteria = config.get('criterios', {})
    devs = {dev['ID']: dev for dev in developers}
    issues = {task['ID']: task for task in tasks}
    if len(devs) != len(developers) or len(issues) != len(tasks):
        raise ValueError('IDs de desenvolvedores e tarefas devem ser unicos em cada grupo.')
    manual = config.get('dados_devs', {})
    available, skills, requirements = {}, {}, {}
    for uid in devs:
        data = manual.get(str(uid), {})
        if not isinstance(data, dict):
            raise ValueError(f'dados_devs.{uid} deve ser um objeto.')
        if criteria.get('disponibilidade'):
            if type(data.get('disponivel')) is not bool:
                raise ValueError(f'Informe dados_devs.{uid}.disponivel como true ou false.')
            available[uid] = data['disponivel']
        if criteria.get('habilidades'):
            skills[uid] = skill_set(data.get('habilidades'), f'dados_devs.{uid}.habilidades')
    if criteria.get('habilidades'):
        for tid in issues:
            requirements[tid] = skill_set(config.get('habilidades_tarefas', {}).get(str(tid)), f'habilidades_tarefas.{tid}')
    graph = nx.Graph()
    left = [('dev', uid) for uid in sorted(devs)]
    graph.add_nodes_from(left, bipartite=0)
    graph.add_nodes_from((('tarefa', tid) for tid in sorted(issues)), bipartite=1)
    limit = criteria.get('max_story_points_por_tarefa')
    for uid in sorted(devs):
        for tid in sorted(issues):
            dev, task = devs[uid], issues[tid]
            if criteria.get('mesmo_projeto') and (
                dev.get('Project_ID') is None or dev.get('Project_ID') != task.get('Project_ID')
            ):
                continue
            if limit is not None and (task.get('Story_Point') is None or task['Story_Point'] > limit):
                continue
            if criteria.get('disponibilidade') and not available[uid]:
                continue
            if criteria.get('habilidades') and not requirements[tid].issubset(skills[uid]):
                continue
            graph.add_edge(('dev', uid), ('tarefa', tid))
    direction = config.get('direcao', 'devs_para_tarefas')
    origins = left if direction == 'devs_para_tarefas' else [('tarefa', tid) for tid in sorted(issues)]
    graph_finished = perf_counter()
    matches, events, checked = matching_with_steps(graph, origins, capture=trace)
    matching_finished = perf_counter()
    allocations = []
    for node in left:
        if node in matches:
            tid = matches[node][1]
            task = issues[tid]
            allocations.append({
                'dev_id': node[1], 'tarefa_id': tid,
                'tarefa': task.get('Issue_Key'), 'titulo': task.get('Title'),
                'sprint_id': task.get('Sprint_ID'), 'story_points': task.get('Story_Point'),
            })
    used_tasks = {row['tarefa_id'] for row in allocations}
    used_devs = {row['dev_id'] for row in allocations}
    return {
        'alocacoes': allocations,
        'devs_sem_tarefa': sorted(set(devs) - used_devs),
        'tarefas_sem_dev': sorted(set(issues) - used_tasks),
        'total_devs': len(devs), 'total_tarefas': len(issues),
        'quantidade_devs': config.get('quantidade_devs'),
        'quantidade_tarefas': config.get('quantidade_tarefas'),
        'direcao': direction,
        'criterios': criteria,
        'passos': events,
        'metricas': {
            'preparacao_ms': (graph_finished - started) * 1000,
            'matching_ms': (matching_finished - graph_finished) * 1000,
            'total_ms': (matching_finished - started) * 1000,
            'arestas_possiveis': len(devs) * len(issues),
            'arestas_validas': graph.number_of_edges(),
            'arestas_avaliadas': checked,
        },
    }
