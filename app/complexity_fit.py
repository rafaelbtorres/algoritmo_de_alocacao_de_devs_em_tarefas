"""Ajusta referencias Big O, com baseline e objetivo logaritmico por padrao."""
import math

import numpy as np
from scipy.optimize import least_squares

from app.matching import ALGORITHM_TIME_COMPLEXITIES

FIT_METHODS = ('log-baseline', 'ms')


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


def _fit_log_baseline(log_basis, times):
    """Minimiza erros logaritmicos de a + b*exp(log_basis), com a,b >= 0.

    Procura o interior a,b>0 com seis inicializacoes deterministicas e compara
    tambem as duas fronteiras exatas a=0 e b=0. Nao adiciona epsilon aos tempos.
    """
    if any(value <= 0 for value in times):
        raise ValueError('O fit log-baseline exige tempos maiores que zero; use --metodo-fit ms para tempos zero.')
    x = np.asarray(log_basis, dtype=float)
    log_times = np.log(np.asarray(times, dtype=float))
    mean_log_time = float(np.mean(log_times))
    constant = {
        'log_predictions': np.full_like(log_times, mean_log_time),
        'log_baseline': mean_log_time, 'log_scale': None, 'solucao': 'escala_zero', 'avaliacoes': 0,
    }
    constant['cost'] = float(np.sum((constant['log_predictions'] - log_times) ** 2))
    if len(times) == 1 or np.all(x == x[0]):
        level = math.exp(mean_log_time)
        return {
            'baseline_ms': level, 'escala_ms': 0.0, 'valores_ms': [level] * len(times),
            'otimizacao': {
                'sucesso': True, 'solucao': 'nivel_constante', 'inicios_tentados': 0,
                'parametros_identificaveis': 1,
                'mensagem': 'Uma entrada ou funcao constante: apenas um nivel pode ser identificado; escala definida como zero.',
            },
        }
    candidates = [constant]
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


def fit_complexities(cases, algorithms, direction='devs_para_tarefas', method='log-baseline'):
    """Ajusta baseline/escala, mantendo a funcao Big O e seu expoente fixos.

    A normalizacao logaritmica evita potencias enormes. O objetivo e a escolha
    de parametros sao independentes da escala visual linear/log dos eixos.
    """
    if method not in FIT_METHODS:
        raise ValueError('Metodo de fit deve ser log-baseline ou ms.')
    if not cases or not algorithms:
        raise ValueError('O fit exige pelo menos uma entrada e um algoritmo.')
    if direction not in ('devs_para_tarefas', 'tarefas_para_devs'):
        raise ValueError('Direcao invalida para os fits Big O.')
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
        parameters = (_fit_log_baseline(log_basis, times) if method == 'log-baseline'
                      else _fit_ms(log_basis, times))
        predictions = parameters['valores_ms']
        if (not math.isfinite(parameters['escala_ms']) or not math.isfinite(parameters['baseline_ms'])
                or any(not math.isfinite(value) for value in predictions)):
            raise ValueError('O ajuste Big O excede a precisao numerica.')
        complexity = ALGORITHM_TIME_COMPLEXITIES[algorithm]
        fits[algorithm] = {
            'complexidade_tempo': complexity,
            'funcao': complexity[2:-1],
            'metodo_fit': method,
            'metodo': ('minimos_quadrados_log_com_baseline' if method == 'log-baseline'
                       else 'minimos_quadrados_em_ms_sem_intercepto'),
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
