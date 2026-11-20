"""Ajusta referencias Big O, com baseline e objetivo logaritmico por padrao."""
import math

import numpy as np
from scipy.optimize import least_squares, minimize_scalar

from app.matching import ALGORITHM_TIME_COMPLEXITIES


def _problem(case, algorithm, direction):
    samples = case.get('execucoes', {}).get(algorithm)
    # Aceita tambem os JSONs antigos, anteriores ao suporte a repeticoes.
    if isinstance(samples, dict):
        samples = [samples]
    if not samples:
        raise ValueError(f"O fit exige os tamanhos e as arestas validas de {algorithm} em {case['entrada']}.")
    dimensions = []
    for sample in samples:
        devs, tasks, edges = (sample.get(key) for key in ('total_devs', 'total_tarefas', 'arestas_validas'))
        if (type(devs) is not int or type(tasks) is not int or type(edges) is not int
                or devs < 1 or tasks < 1 or not 0 <= edges <= devs * tasks):
            raise ValueError('O fit exige contagens validas de desenvolvedores, tarefas e arestas.')
        if case['entrada'] != f'{devs}x{tasks}':
            raise ValueError('O tamanho registrado nao corresponde ao rotulo da entrada do fit.')
        dimensions.append((devs, tasks, edges))
    if len(set(dimensions)) != 1:
        raise ValueError('As repeticoes do fit devem usar o mesmo problema.')
    devs, tasks, edges = dimensions[0]
    n, m = (tasks, devs) if direction == 'tarefas_para_devs' else (devs, tasks)
    return {'n': n, 'm': m, 'V': n + m, 'E': edges}


def _log_growth(algorithm, problem):
    n, m, vertices, edges = (problem[key] for key in ('n', 'm', 'V', 'E'))
    if algorithm == 'bfs':
        return math.log(n) + math.log(vertices + edges)
    if algorithm == 'scipy':
        return 2 * math.log(n) + math.log(m + n)
    if algorithm == 'greedy':
        # E log E e assintotico. Estende a forma aos casos E=0 e E=1,
        # mantendo uma unidade de trabalho para a chamada do solver.
        return math.log(max(1, edges)) + math.log(math.log2(max(2, edges)))
    if algorithm == 'brute_force':
        return math.log(n) + n * math.log1p(m)
    raise ValueError(f'Algoritmo sem modelo de complexidade: {algorithm}.')


def _fit_ms(log_basis, times):
    basis = [math.exp(value) for value in log_basis]
    if any(value == 0 for value in basis):
        raise ValueError('Amplitude do modelo Big O excede a precisao numerica; use um intervalo menor de entradas.')
    peak = max(times)
    coefficient = (math.fsum(x * (y / peak) for x, y in zip(basis, times))
                   / math.fsum(x * x for x in basis)) * peak if peak else 0.0
    return {
        'baseline_ms': 0.0, 'escala_ms': coefficient,
        'valores_ms': [coefficient * value for value in basis],
        'otimizacao': {'sucesso': True, 'solucao': 'escala_fechada', 'inicios_tentados': 0},
    }


def _fit_log_growth(log_basis, times):
    """Ajusta tempos e crescimento em log, com uma ancora no maior f."""
    if any(value <= 0 for value in times):
        raise ValueError('O fit log-growth exige tempos maiores que zero; use --metodo-fit ms para tempos zero.')
    log_x = np.asarray(log_basis, dtype=float)
    log_times = np.log(np.asarray(times, dtype=float))
    last_times = sorted(time for value, time in zip(log_basis, times) if value == 0)
    lower = last_times[(len(last_times) - 1) // 2]
    upper = last_times[len(last_times) // 2]
    anchor = lower + (upper - lower) / 2
    log_anchor = math.log(anchor)
    _, first, groups, counts = np.unique(log_x, return_index=True, return_inverse=True, return_counts=True)
    if len(first) == 1:
        return {
            'baseline_ms': anchor, 'escala_ms': 0.0, 'valores_ms': [anchor] * len(times),
            'ancora_ms': anchor,
            'otimizacao': {'sucesso': True, 'solucao': 'nivel_constante', 'avaliacoes': 0,
                           'parametros_identificaveis': 1},
        }

    # Para q = b / ancora, a previsao normalizada e ancora * ((1-q)*x + q).
    # Isso impoe a ancora em x=1 e deixa apenas q para ajustar.
    observed_growth = np.diff(np.bincount(groups, weights=log_times) / counts)

    def objective(log_fraction):
        scale_fraction = -math.expm1(log_fraction)
        log_scale = math.log(scale_fraction) if scale_fraction else -math.inf
        log_predictions = log_anchor + np.logaddexp(log_scale + log_x, log_fraction)
        errors = log_predictions - log_times
        growth_errors = np.diff(log_predictions[first]) - observed_growth
        return float(np.mean(np.where(errors > 0, 2., 1.) * errors ** 2)
                     + 2 * np.mean(growth_errors ** 2))

    # Busca em log para resolver baselines muito menores que a ancora.
    # Refina os minimos locais da malha e compara com a fronteira b=0.
    grid = np.linspace(float(log_times.min()) - log_anchor - 20, 0, 901)
    costs = np.array([objective(value) for value in grid])
    best = int(np.argmin(costs))
    candidates = [(costs[best], grid[best]), (objective(-math.inf), -math.inf)]
    evaluations = len(grid) + 1
    minima = np.flatnonzero(((costs[1:-1] < costs[:-2]) & (costs[1:-1] <= costs[2:]))
                           | ((costs[1:-1] <= costs[:-2]) & (costs[1:-1] < costs[2:]))) + 1
    bounds = [(grid[index - 1], grid[index + 1]) for index in minima]
    bounds.append((grid[-2], grid[-1]))
    for interval in bounds:
        result = minimize_scalar(objective, bounds=interval,
                                 method='bounded', options={'xatol': 1e-12})
        evaluations += result.nfev
        if result.success:
            candidates.append((result.fun, result.x))
    _, log_fraction = min(candidates)

    baseline = math.exp(log_anchor + log_fraction) if log_fraction < 0 else anchor
    coefficient = anchor * -math.expm1(log_fraction)
    log_scale = math.log(coefficient) if coefficient else -math.inf
    predictions = [anchor if value == 0 else baseline + math.exp(log_scale + value) for value in log_basis]
    if any(value == 0 for value in predictions):
        raise ValueError('As previsoes log-growth estao abaixo da precisao numerica.')
    return {
        'baseline_ms': baseline, 'escala_ms': coefficient, 'valores_ms': predictions,
        'ancora_ms': anchor,
        'otimizacao': {'sucesso': True, 'solucao': 'ancorado', 'avaliacoes': evaluations,
                       'parametros_identificaveis': 2},
    }


def _fit_log_baseline(log_basis, times):
    """Ajusta a*exp(log_basis) + b em log, com a,b >= 0.

    Procura o interior a,b>0 com seis inicializacoes deterministicas e compara
    tambem as duas fronteiras exatas a=0 e b=0. Nao adiciona epsilon aos tempos.
    """
    if any(value <= 0 for value in times):
        raise ValueError('O fit log-baseline exige tempos maiores que zero; use --metodo-fit ms para tempos zero.')
    x = np.asarray(log_basis, dtype=float)
    log_times = np.log(np.asarray(times, dtype=float))
    log_level = float(np.mean(log_times))
    if len(times) == 1 or np.all(x == x[0]):
        level = math.exp(log_level)
        return {
            'baseline_ms': level, 'escala_ms': 0.0, 'valores_ms': [level] * len(times),
            'otimizacao': {
                'sucesso': True, 'solucao': 'nivel_constante', 'inicios_tentados': 0,
                'parametros_identificaveis': 1,
                'mensagem': 'Uma entrada ou funcao constante: apenas um nivel pode ser identificado; escala definida como zero.',
            },
        }
    constant_predictions = np.full_like(log_times, log_level)
    candidates = [{
        'log_predictions': constant_predictions, 'log_baseline': log_level, 'log_scale': None,
        'cost': float(np.sum((constant_predictions - log_times) ** 2)), 'solucao': 'escala_zero', 'avaliacoes': 0,
    }]
    log_scale = float(np.mean(log_times - x))
    scale_predictions = log_scale + x
    candidates.append({
        'log_predictions': scale_predictions, 'log_baseline': None, 'log_scale': log_scale,
        'cost': float(np.sum((scale_predictions - log_times) ** 2)),
        'solucao': 'baseline_zero', 'avaliacoes': 0,
    })

    def residual(parameters):
        return np.logaddexp(parameters[0], parameters[1] + x) - log_times

    def jacobian(parameters):
        predicted = np.logaddexp(parameters[0], parameters[1] + x)
        return np.column_stack((np.exp(parameters[0] - predicted),
                                np.exp(parameters[1] + x - predicted)))

    lower = float(np.min(log_times) - 30)
    upper = float(min(np.max(log_times) + 30, math.log(np.finfo(float).max) - 1))
    converged = 0
    for fraction in (.01, .25, .75):
        for scale_start in (log_scale, float(log_times[np.argmax(x)] - np.max(x))):
            start = np.clip([float(np.min(log_times) + math.log(fraction)), scale_start],
                            np.nextafter(lower, upper), np.nextafter(upper, lower))
            result = least_squares(residual, start, jac=jacobian, bounds=(lower, upper),
                                   method='trf', loss='linear', max_nfev=2000,
                                   ftol=1e-11, xtol=1e-11, gtol=1e-11)
            if result.success and np.all(np.isfinite(result.fun)):
                converged += 1
                candidates.append({
                    'log_predictions': np.logaddexp(result.x[0], result.x[1] + x),
                    'log_baseline': float(result.x[0]), 'log_scale': float(result.x[1]),
                    'cost': float(np.sum(result.fun ** 2)), 'solucao': 'interior',
                    'avaliacoes': int(result.nfev),
                })
    if not converged:
        raise ValueError('O ajuste log-baseline nao convergiu; as medicoes devem ser preservadas para inspecao.')
    best = min(candidates, key=lambda candidate: candidate['cost'])
    try:
        baseline = math.exp(best['log_baseline']) if best['log_baseline'] is not None else 0.0
        coefficient = math.exp(best['log_scale']) if best['log_scale'] is not None else 0.0
        predictions = [math.exp(float(value)) for value in best['log_predictions']]
    except OverflowError:
        raise ValueError('O ajuste log-baseline excede a precisao numerica.') from None
    if any(value == 0 for value in predictions):
        raise ValueError('As previsoes log-baseline estao abaixo da precisao numerica.')
    return {
        'baseline_ms': baseline, 'escala_ms': coefficient, 'valores_ms': predictions,
        'otimizacao': {
            'sucesso': True, 'solucao': best['solucao'], 'inicios_tentados': 6,
            'inicios_convergentes': converged, 'avaliacoes': best['avaliacoes'],
            'parametros_identificaveis': 2,
        },
    }


_FIT_IMPLEMENTATIONS = {
    'log-baseline': (_fit_log_baseline, 'minimos_quadrados_log_com_baseline'),
    'ms': (_fit_ms, 'minimos_quadrados_em_ms_sem_intercepto'),
    'log-growth': (_fit_log_growth, 'minimos_quadrados_log_assimetricos_com_crescimento_ancorado'),
}
FIT_METHODS = tuple(_FIT_IMPLEMENTATIONS)


def fit_complexities(cases, algorithms, direction='devs_para_tarefas', method='log-baseline'):
    """Ajusta baseline/escala, mantendo a funcao Big O e seu expoente fixos.

    A normalizacao logaritmica evita potencias enormes. O objetivo e a escolha
    de parametros sao independentes da escala visual linear/log dos eixos.
    """
    if method not in FIT_METHODS:
        raise ValueError(f"Metodo de fit deve ser um de: {', '.join(FIT_METHODS)}.")
    if not cases or not algorithms:
        raise ValueError('O fit exige pelo menos uma entrada e um algoritmo.')
    if direction not in ('devs_para_tarefas', 'tarefas_para_devs'):
        raise ValueError('Direcao invalida para os fits Big O.')
    fit_model, objective = _FIT_IMPLEMENTATIONS[method]
    fits = {}
    for algorithm in algorithms:
        if algorithm not in ALGORITHM_TIME_COMPLEXITIES:
            raise ValueError(f'Algoritmo sem modelo de complexidade: {algorithm}.')
        problems = [_problem(case, algorithm, direction) for case in cases]
        times = [case['resultados'][algorithm] for case in cases]
        if any(not math.isfinite(value) or value < 0 for value in times):
            raise ValueError('O fit exige tempos finitos e nao negativos.')
        logs = [_log_growth(algorithm, problem) for problem in problems]
        normalization = max(logs)
        log_basis = [value - normalization for value in logs]
        parameters = fit_model(log_basis, times)
        predictions = parameters['valores_ms']
        if (not math.isfinite(parameters['escala_ms']) or not math.isfinite(parameters['baseline_ms'])
                or any(not math.isfinite(value) for value in predictions)):
            raise ValueError('O ajuste Big O excede a precisao numerica.')
        complexity = ALGORITHM_TIME_COMPLEXITIES[algorithm]
        fits[algorithm] = {
            'complexidade_tempo': complexity,
            'funcao': complexity[2:-1],
            'metodo_fit': method,
            'metodo': objective,
            'modelo_normalizado': 't_ms = baseline_ms + escala_ms * exp(log(f) - log_normalizador)',
            **parameters,
            'log_normalizador': normalization,
            'erro_rms_ms': math.hypot(*(y - predicted for y, predicted in zip(times, predictions))) / math.sqrt(len(times)),
            'entradas': [case['entrada'] for case in cases],
            'parametros_por_entrada': problems,
        }
        log_errors = ([math.log(predicted) - math.log(observed) for predicted, observed in zip(predictions, times)]
                      if all(value > 0 for value in predictions + times) else None)
        fits[algorithm]['erro_rms_log'] = (math.hypot(*log_errors) / math.sqrt(len(times))
                                          if log_errors is not None else None)
        fits[algorithm]['fator_erro_medio'] = (math.exp(math.fsum(abs(error) for error in log_errors) / len(times))
                                             if log_errors is not None else None)
        if algorithm == 'greedy':
            fits[algorithm]['extensao_casos_pequenos'] = 'max(1, E) * log2(max(2, E))'
    return fits
