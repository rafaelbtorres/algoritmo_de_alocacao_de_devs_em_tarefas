"""Alocacao 1:1 com BFS, SciPy, SSP, Kwok (2025) ou guloso classico."""
import math
import random
from collections import deque
from heapq import heappop, heappush
from time import perf_counter

import numpy as np
from kwok import kwok as kwok_matching
from scipy.optimize import linear_sum_assignment


ALGORITHMS = {
    'bfs': 'BFS por caminhos aumentantes',
    'scipy': 'scipy.optimize.linear_sum_assignment (Jonker-Volgenant modificado)',
    'ssp': 'SSP (guloso por caminhos aumentantes de menor custo)',
    'kwok': 'kwok.kwok (Kwok, 2025)',
    'greedy': 'Greedy Weighted Matching (guloso classico por pontuacao decrescente)',
}


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('A configuracao deve ser um objeto JSON.')
    if config.get('direcao', 'devs_para_tarefas') not in ('devs_para_tarefas', 'tarefas_para_devs'):
        raise ValueError('direcao deve ser devs_para_tarefas ou tarefas_para_devs.')
    if not isinstance(config.get('algoritmo', 'scipy'), str) or config.get('algoritmo', 'scipy') not in ALGORITHMS:
        raise ValueError('algoritmo deve ser scipy, bfs, ssp, kwok ou greedy.')
    for key in ('projeto_id', 'sprint_id', 'quantidade_devs', 'quantidade_tarefas'):
        value = config.get(key)
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f'{key} deve ser um inteiro positivo ou null.')
    seed = config.get('semente_embaralhamento')
    if seed is not None and (type(seed) is not int or not 0 <= seed <= 4294967295):
        raise ValueError('semente_embaralhamento deve ser um inteiro entre 0 e 4294967295 ou null.')
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
    weights = config.get('pesos', {})
    if not isinstance(weights, dict) or set(weights) - {'mesmo_projeto', 'disponibilidade', 'habilidades'}:
        raise ValueError('pesos deve conter apenas mesmo_projeto, disponibilidade e habilidades.')
    for key, value in weights.items():
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f'pesos.{key} deve ser um numero entre 0 e 100.')
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
        if capture:
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
                if capture:
                    current_pair = pair(node, target)
                    emit('avaliar', **current_pair,
                         mensagem=f"Avaliando o par dev {current_pair['dev_id']} e tarefa {current_pair['tarefa_id']}.")
                if target not in matches:
                    free = target
                    break
                partner = matches[target]
                if capture:
                    occupied = pair(partner, target)
                    explanation = (f"Tarefa ocupada pelo dev {occupied['dev_id']}" if target[0] == 'tarefa'
                                   else f"Dev ja alocado a tarefa {occupied['tarefa_id']}")
                    emit('ocupada', **occupied, mensagem=explanation + '; procurando um caminho alternativo.')
                queue.append(partner)
        if free is None:
            if capture:
                emit('sem_par', **root_field, mensagem=f'Nenhum caminho disponivel para {root_label}.')
            continue
        path = []
        while free is not None:
            node = parent[free]
            previous = matches.get(node)
            matches[node] = free
            matches[free] = node
            if capture:
                path.append(pair(node, free))
            free = previous
        if capture:
            emit('alocar', **root_field, caminho=list(reversed(path)),
                 pares=[pair(node, matches[node]) for node in left if node in matches],
                 mensagem='Caminho aumentante aplicado: mais uma tarefa alocada.')
    if capture:
        emit('concluir', mensagem='Busca concluida. O matching tem a maior quantidade possivel de pares validos.')
    return matches, events, checked


def greedy_with_steps(candidates, left, right, capture=False):
    """Aceita pares por nota decrescente sem revisar escolhas; empata pela ordem dos grupos."""
    selected, events = [], []
    used_left, used_right = set(), set()
    started = perf_counter()

    def emit(kind, **data):
        if capture:
            events.append({'tipo': kind, 'tempo_ms': (perf_counter() - started) * 1000, **data})

    def pair(row, column):
        first, second = left[row], right[column]
        dev, task = (first, second) if first[0] == 'dev' else (second, first)
        return {'dev_id': dev[1], 'tarefa_id': task[1]}

    candidates = sorted(candidates, key=lambda edge: (-edge[0], edge[1], edge[2]))
    emit('ordenar', mensagem='Greedy Weighted Matching: pares permitidos ordenados por nota decrescente; empates seguem a ordem do grupo a esquerda e depois do grupo a direita.')
    for score, row, column in candidates:
        current = pair(row, column) if capture else None
        if row in used_left or column in used_right:
            if capture:
                emit('descartar', **current, pontuacao=score,
                     mensagem='Greedy Weighted Matching: par descartado porque o dev ou a tarefa ja foi alocado; escolhas anteriores nao sao revistas.')
            continue
        used_left.add(row)
        used_right.add(column)
        selected.append((row, column))
        if capture:
            emit('alocar', **current, pontuacao=score,
                 pares=[pair(i, j) for i, j in selected],
                 mensagem=f"Greedy Weighted Matching: aceita dev {current['dev_id']} e tarefa {current['tarefa_id']}, nota {score:.2f}/100, sem reatribuicoes.")
    emit('concluir', mensagem='Greedy Weighted Matching concluido: nenhum par pode ser acrescentado sem alterar escolhas anteriores. A quantidade de pares e a pontuacao total podem ser menores que as otimas.')
    return selected, events


def prepare_ssp(values):
    """Cria a rede residual com capacidade 1 e custo 100 - nota por par."""
    rows, columns = values.shape
    source, sink = rows + columns, rows + columns + 1
    graph = [[] for _ in range(sink + 1)]

    def add(first, second, cost):
        # Aresta: destino, indice da reversa, capacidade residual e custo.
        forward = [second, len(graph[second]), 1, cost]
        backward = [first, len(graph[first]), 0, -cost]
        graph[first].append(forward)
        graph[second].append(backward)

    for row in range(rows):
        add(source, row, 0.0)
    for column in range(columns):
        add(rows + column, sink, 0.0)
    valid_rows, valid_columns = np.nonzero(np.isfinite(values))
    for row, column in zip(valid_rows, valid_columns):
        add(int(row), rows + int(column), 100.0 - float(values[row, column]))
    return graph


def ssp_with_steps(graph, left, right, capture=False):
    """Escolhe o caminho de menor custo; reversas permitem refazer pares anteriores."""
    rows, columns = len(left), len(right)
    source, sink = rows + columns, rows + columns + 1
    potentials = [0.0] * len(graph)
    matches, events = {}, []
    started = perf_counter()

    def emit(kind, **data):
        if capture:
            events.append({'tipo': kind, 'tempo_ms': (perf_counter() - started) * 1000, **data})

    def pair(row, column):
        first, second = left[row], right[column]
        dev, task = (first, second) if first[0] == 'dev' else (second, first)
        return {'dev_id': dev[1], 'tarefa_id': task[1]}

    while True:
        emit('buscar', mensagem='SSP: buscando o caminho de menor custo para acrescentar uma alocacao; pares anteriores podem ser reorganizados.')
        distances, parents = [math.inf] * len(graph), [None] * len(graph)
        distances[source] = 0.0
        queue = [(0.0, source)]
        while queue:
            distance, node = heappop(queue)
            if distance > distances[node]:
                continue
            for index, (target, _, capacity, cost) in enumerate(graph[node]):
                if not capacity:
                    continue
                # Os potenciais tornam os custos reduzidos nao negativos.
                # O max protege contra pequenos erros de arredondamento em floats.
                reduced = max(0.0, cost + potentials[node] - potentials[target])
                candidate = distance + reduced
                if candidate < distances[target]:
                    distances[target], parents[target] = candidate, (node, index)
                    heappush(queue, (candidate, target))
        if parents[sink] is None:
            break
        for node, distance in enumerate(distances):
            if math.isfinite(distance):
                potentials[node] += distance
        added, removed = [], []
        node = sink
        while node != source:
            previous, index = parents[node]
            edge = graph[previous][index]
            edge[2] -= 1
            graph[node][edge[1]][2] += 1
            if previous < rows and rows <= node < rows + columns:
                added.append((previous, node - rows))
            elif rows <= previous < rows + columns and node < rows:
                removed.append((node, previous - rows))
            node = previous
        for row, _ in removed:
            del matches[row]
        for row, column in added:
            matches[row] = column
        if capture:
            path = [pair(row, column) for row, column in reversed(added)]
            emit('alocar', **path[0], caminho=path,
                 removidos=[pair(row, column) for row, column in removed],
                 pares=[pair(row, column) for row, column in sorted(matches.items())],
                 mensagem=f'SSP: caminho de menor custo aplicado; {len(removed)} par(es) anterior(es) reorganizado(s). A solucao tem {len(matches)} pares e a melhor pontuacao para essa quantidade.')
    emit('concluir', mensagem='SSP concluido: nenhum caminho aumentante restante. Quantidade maxima de pares e maior pontuacao total entre essas solucoes.')
    return sorted(matches.items()), events


def prepare_kwok(values):
    """Compacta vertices ativos e coloca o menor grupo a esquerda do Kwok."""
    valid = np.isfinite(values)
    left = np.flatnonzero(valid.any(axis=1))
    right = np.flatnonzero(valid.any(axis=0))
    transposed = len(left) > len(right)
    if transposed:
        values, valid = values.T, valid.T
        left, right = right, left
    left_map, right_map = np.full(values.shape[0], -1), np.full(values.shape[1], -1)
    left_map[left], right_map[right] = np.arange(len(left)), np.arange(len(right))
    rows, columns = np.nonzero(valid)
    # O bonus prioriza a quantidade e mantem notas zero como arestas reais positivas.
    bonus = min(values.shape) + 1
    weights = bonus + values[rows, columns] / 100
    graph = [[] for _ in left]
    for row, column, weight in zip(left_map[rows], right_map[columns], weights):
        graph[int(row)].append((int(column), float(weight)))
    # Kwok 1.1.7 escolhe o tipo numerico olhando somente a primeira linha.
    # Mover uma linha fracionaria para o inicio evita truncar notas das demais.
    fractional = next((row for row, edges in enumerate(graph)
                       if any(not weight.is_integer() for _, weight in edges)), 0)
    if fractional:
        graph[0], graph[fractional] = graph[fractional], graph[0]
        left[0], left[fractional] = left[fractional], left[0]
    return graph, left, right, transposed


def select_participants(developers, tasks, config):
    """Seleciona os primeiros IDs e, opcionalmente, embaralha a ordem desse recorte."""
    validate_config(config)
    developers = sorted(developers, key=lambda dev: dev['ID'])[:config.get('quantidade_devs')]
    tasks = sorted(tasks, key=lambda task: task['ID'])[:config.get('quantidade_tarefas')]
    seed = config.get('semente_embaralhamento')
    if seed is not None:
        generator = random.Random(seed)
        generator.shuffle(developers)
        generator.shuffle(tasks)
    return developers, tasks


def prepare_problem(developers, tasks, config):
    developers, tasks = select_participants(developers, tasks, config)
    if len({d['ID'] for d in developers}) != len(developers) or len({t['ID'] for t in tasks}) != len(tasks):
        raise ValueError('IDs de desenvolvedores e tarefas devem ser unicos em cada grupo.')
    criteria, weights = config.get('criterios', {}), config.get('pesos', {})
    manual = config.get('dados_devs', {})
    available, skills, requirements = {}, {}, {}
    for dev in developers:
        uid = dev['ID']
        data = manual.get(str(uid), {})
        if not isinstance(data, dict):
            raise ValueError(f'dados_devs.{uid} deve ser um objeto.')
        if criteria.get('disponibilidade') or weights.get('disponibilidade', 0) > 0:
            if type(data.get('disponivel')) is not bool:
                raise ValueError(f'Informe a disponibilidade do dev {uid} na tabela de desenvolvedores.')
            available[uid] = data['disponivel']
        if criteria.get('habilidades') or weights.get('habilidades', 0) > 0:
            dev_skills = data.get('habilidades')
            if dev_skills is None:
                if criteria.get('habilidades'):
                    raise ValueError(f'Informe as áreas de atuação do dev {uid}; para a restrição obrigatória, classifique todos os devs e tarefas.')
            else:
                skills[uid] = skill_set(dev_skills, f'dados_devs.{uid}.habilidades')
    if criteria.get('habilidades') or weights.get('habilidades', 0) > 0:
        for task in tasks:
            task_id = task['ID']
            task_skills = config.get('habilidades_tarefas', {}).get(str(task_id))
            if task_skills is None:
                if criteria.get('habilidades'):
                    raise ValueError(f'Informe as áreas exigidas pela tarefa {task_id}; para a restrição obrigatória, classifique todos os devs e tarefas.')
            else:
                requirements[task_id] = skill_set(task_skills, f'habilidades_tarefas.{task_id}')
    return developers, tasks, available, skills, requirements


def evaluate_pair(dev, task, config, available, skills, requirements):
    criteria, weights = config.get('criterios', {}), config.get('pesos', {})
    uid, tid = dev['ID'], task['ID']
    same_project = dev.get('Project_ID') is not None and dev.get('Project_ID') == task.get('Project_ID')
    skills_informed = uid in skills and tid in requirements
    required = requirements.get(tid, set())
    developer_skills = skills.get(uid, set())
    covered = required & developer_skills
    factors = {'mesmo_projeto': float(same_project), 'disponibilidade': float(available.get(uid, False)),
               'habilidades': (len(covered) / len(required) if required else 1.0) if skills_informed else None}
    reasons = []
    if criteria.get('mesmo_projeto') and not same_project:
        reasons.append('Projetos diferentes ou projeto do dev nao informado.')
    if criteria.get('disponibilidade') and not available[uid]:
        reasons.append('Desenvolvedor indisponivel.')
    if criteria.get('habilidades') and not required.issubset(skills[uid]):
        reasons.append('O dev nao possui todas as habilidades exigidas.')
    limit = criteria.get('max_story_points_por_tarefa')
    if limit is not None and (task.get('Story_Point') is None or task['Story_Point'] > limit):
        reasons.append('Story points ausentes ou acima do limite.')
    known_weight = sum(weights.get(key, 0) for key, value in factors.items() if value is not None)
    components = [{'criterio': key, 'peso': weights.get(key, 0), 'fator': factors[key],
                   'contribuicao': 100 * weights.get(key, 0) * factors[key] / known_weight
                   if factors[key] is not None and known_weight else 0}
                  for key in factors]
    score = sum(c['contribuicao'] for c in components) if known_weight else 0.0
    return {'permitido': not reasons, 'pontuacao': score if not reasons else None,
            'motivos': reasons, 'componentes': components,
            'habilidades_atendidas': sorted(covered) if skills_informed else None,
            'habilidades_exigidas': sorted(required) if tid in requirements else None,
            'habilidades_dev_informadas': uid in skills,
            'habilidades_tarefa_informadas': tid in requirements,
            'fatores_ignorados': [key for key, value in factors.items()
                                  if weights.get(key, 0) > 0 and value is None],
            'sem_pontuacao': bool(weights) and any(weights.values()) and known_weight == 0}


def score_matrix(developers, tasks, config):
    prepared = prepare_problem(developers, tasks, config)
    developers, tasks, *context = prepared
    evaluations = [[evaluate_pair(dev, task, config, *context) for task in tasks] for dev in developers]
    values = [[cell['pontuacao'] for cell in row] for row in evaluations]
    skills_partial = config.get('pesos', {}).get('habilidades', 0) > 0
    return developers, tasks, {'dev_ids': [d['ID'] for d in developers], 'tarefa_ids': [t['ID'] for t in tasks],
                              'valores': values, 'pesos': config.get('pesos', {}), 'escala': 100,
                              'sem_dados': [[skills_partial and not (cell['habilidades_dev_informadas'] and cell['habilidades_tarefa_informadas'])
                                             for cell in row] for row in evaluations],
                              'sem_pontuacao': [[cell['sem_pontuacao'] for cell in row] for row in evaluations]}


def allocate(developers, tasks, config, trace=False):
    started = perf_counter()
    developers, tasks, matrix = score_matrix(developers, tasks, config)
    direction = config.get('direcao', 'devs_para_tarefas')
    reverse = direction == 'tarefas_para_devs'
    n, m = len(developers), len(tasks)
    values = np.array([[np.nan if value is None else value for value in row] for row in matrix['valores']], dtype=float).reshape(n, m)
    valid = np.isfinite(values)
    algorithm = config.get('algoritmo', 'scipy')
    events = []
    if algorithm == 'bfs':
        left = [('dev', d['ID']) for d in developers]
        right = [('tarefa', t['ID']) for t in tasks]
        graph = {node: {} for node in left + right}
        for i, dev in enumerate(left):
            for j, task in enumerate(right):
                if valid[i, j]:
                    graph[dev][task] = None
                    graph[task][dev] = None
        origins = right if reverse else left
        prepared_at = perf_counter()
        matches, events, checked = matching_with_steps(graph, origins, capture=trace)
        solved_at = perf_counter()
        task_indices = {t['ID']: j for j, t in enumerate(tasks)}
        selected = [(i, task_indices[matches[node][1]]) for i, node in enumerate(left) if node in matches]
        if reverse:
            selected.sort(key=lambda pair: pair[1])
    elif algorithm == 'greedy':
        left = [('dev', d['ID']) for d in developers]
        right = [('tarefa', t['ID']) for t in tasks]
        origins, targets = (right, left) if reverse else (left, right)
        oriented = values.T if reverse else values
        candidate_rows, candidate_columns = np.nonzero(np.isfinite(oriented))
        candidates = [(float(oriented[row, column]), int(row), int(column))
                      for row, column in zip(candidate_rows, candidate_columns)]
        prepared_at = perf_counter()
        oriented_selected, events = greedy_with_steps(candidates, origins, targets, capture=trace)
        solved_at = perf_counter()
        selected = [(column, row) if reverse else (row, column) for row, column in oriented_selected]
    elif algorithm == 'ssp':
        left = [('dev', d['ID']) for d in developers]
        right = [('tarefa', t['ID']) for t in tasks]
        origins, targets = (right, left) if reverse else (left, right)
        graph = prepare_ssp(values.T if reverse else values)
        prepared_at = perf_counter()
        oriented_selected, events = ssp_with_steps(graph, origins, targets, capture=trace)
        solved_at = perf_counter()
        selected = [(column, row) if reverse else (row, column) for row, column in oriented_selected]
    elif algorithm == 'kwok':
        graph, left, right, transposed = prepare_kwok(values.T if reverse else values)
        prepared_at = perf_counter()
        # Pares virtuais de peso zero representam a ausencia de uma alocacao.
        result = kwok_matching(graph, keeps_virtual_matching=False) if graph else None
        solved_at = perf_counter()
        if graph and result is None:
            raise RuntimeError('Kwok nao retornou uma solucao para o grafo preparado.')
        selected = []
        if result is not None:
            for row, column in enumerate(result.left_pairs):
                if column < 0:
                    continue
                i, j = (int(right[column]), int(left[row])) if transposed else (int(left[row]), int(right[column]))
                selected.append((j, i) if reverse else (i, j))
        selected.sort(key=lambda pair: pair[1] if reverse else pair[0])
    else:
        oriented = values.T if reverse else values
        # O bonus preserva a prioridade: quantidade de pares, depois pontuacao.
        bonus = min(n, m) + 1
        utility = np.concatenate((np.where(np.isfinite(oriented), bonus + oriented / 100, -np.inf),
                                  np.zeros((oriented.shape[0], oriented.shape[0]))), axis=1)
        prepared_at = perf_counter()
        rows, columns = [], []
        if n and m:
            rows, columns = linear_sum_assignment(utility, maximize=True)
        solved_at = perf_counter()
        selected = []
        for row, column in zip(rows, columns):
            if column >= oriented.shape[1]:
                continue
            i, j = (int(column), int(row)) if reverse else (int(row), int(column))
            selected.append((i, j))
    allocations = []
    for i, j in selected:
        task = tasks[j]
        allocations.append({'dev_id': developers[i]['ID'], 'tarefa_id': task['ID'],
                            'tarefa': task.get('Issue_Key'), 'titulo': task.get('Title'),
                            'sprint_id': task.get('Sprint_ID'), 'story_points': task.get('Story_Point'),
                            'pontuacao': matrix['valores'][i][j]})
    used_devs = {p['dev_id'] for p in allocations}
    used_tasks = {p['tarefa_id'] for p in allocations}
    if trace and algorithm in ('scipy', 'kwok'):
        label = 'Kwok' if algorithm == 'kwok' else 'SciPy'
        events = [
            {'tipo': 'matriz', 'mensagem': 'Matriz preparada: cada celula representa a pontuacao de um par permitido; bloqueios nao participam da alocacao.'},
            {'tipo': 'resolver', 'mensagem': f'O {label} ja calculou a solucao global. A seguir, apresentamos os pares do resultado; esta sequencia nao mostra operacoes internas do solver.'},
        ]
        for index, pair in enumerate(allocations):
            events.append({'tipo': 'alocar', 'dev_id': pair['dev_id'], 'tarefa_id': pair['tarefa_id'],
                           'pares': [{'dev_id': p['dev_id'], 'tarefa_id': p['tarefa_id']} for p in allocations[:index + 1]],
                           'pontuacao': pair['pontuacao'],
                           'mensagem': f"Par da solucao: dev {pair['dev_id']} e tarefa {pair['tarefa_id']}, nota {pair['pontuacao']:.2f}/100. A escolha considera a soma global, nao apenas a maior nota individual."})
        events.append({'tipo': 'concluir', 'mensagem': 'Apresentacao concluida: maior quantidade de pares validos e melhor pontuacao total entre essas solucoes.'})
    return {
        'codigo_algoritmo': algorithm,
        'algoritmo': ALGORITHMS[algorithm],
        'objetivo': ('Aceitar pares validos por pontuacao decrescente, sem reatribuicoes; sem garantia de quantidade ou pontuacao otimas.' if algorithm == 'greedy'
                     else 'Maximizar quantidade de pares validos; pesos somente para avaliar o resultado.' if algorithm == 'bfs'
                     else 'Maximizar quantidade de pares validos; depois maximizar pontuacao total.'),
        'tipo_passos': 'execucao_real' if algorithm in ('bfs', 'ssp', 'greedy') else 'apresentacao_da_solucao',
        'alocacoes': allocations,
        'pontuacao_total': sum(p['pontuacao'] for p in allocations),
        'devs_sem_tarefa': sorted({d['ID'] for d in developers} - used_devs),
        'tarefas_sem_dev': sorted({t['ID'] for t in tasks} - used_tasks),
        'total_devs': n, 'total_tarefas': m,
        'quantidade_devs': config.get('quantidade_devs'), 'quantidade_tarefas': config.get('quantidade_tarefas'),
        'semente_embaralhamento': config.get('semente_embaralhamento'),
        'ordem_devs': matrix['dev_ids'], 'ordem_tarefas': matrix['tarefa_ids'],
        'direcao': direction, 'criterios': config.get('criterios', {}), 'pesos': config.get('pesos', {}),
        'matriz': matrix, 'passos': events,
        'metricas': {'preparacao_ms': (prepared_at - started) * 1000,
                     'matching_ms': (solved_at - prepared_at) * 1000,
                     'total_ms': (solved_at - started) * 1000,
                     'arestas_possiveis': n * m, 'arestas_validas': int(valid.sum()),
                     'registro_passos': trace},
    }
