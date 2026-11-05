"""Compara o tempo dos solvers em varios tamanhos e exporta um grafico Matplotlib."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import platform
import re
from statistics import median
import sys
import tempfile
from time import get_clock_info

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pymysql import MySQLError

from app.main import load_data, positive_integer, save_result
from app.matching import ALGORITHMS, allocate, prepare_problem, validate_config


# Cores fixas: a mesma cor identifica o algoritmo em qualquer selecao/ordem.
STYLES = {
    'bfs': ('BFS', '#2563EB', 'o'),
    'scipy': ('SciPy', '#D97706', 's'),
    'greedy': ('Greedy bweight', '#0D9488', '^'),
    'brute_force': ('Força bruta', '#A855F7', 'D'),
}
FORMATS = ('.png', '.svg', '.pdf')


def input_size(value):
    match = re.fullmatch(r'([0-9]+)[xX]([0-9]+)', value)
    if not match or any(int(part) < 1 for part in match.groups()):
        raise argparse.ArgumentTypeError('Use DEVSxTAREFAS com inteiros positivos, por exemplo 2x3.')
    return tuple(int(part) for part in match.groups())


def synthetic_data(dev_count, task_count):
    """Caso completo, deterministico, sem restricoes ou diferencas de pontuacao."""
    return ([{'ID': i + 1} for i in range(dev_count)],
            [{'ID': i + 1} for i in range(task_count)])


def benchmark(developers, tasks, config, sizes, algorithms, repetitions=1):
    """Executa as repeticoes solicitadas, guarda amostras e retorna suas medianas."""
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError('O numero de repeticoes deve ser um inteiro positivo.')
    max_devs = max(size[0] for size in sizes)
    max_tasks = max(size[1] for size in sizes)
    if len(developers) < max_devs or len(tasks) < max_tasks:
        raise ValueError(
            f'Entradas exigem ate {max_devs} devs e {max_tasks} tarefas, mas o recorte '
            f'possui {len(developers)} devs e {len(tasks)} tarefas. '
            'Reduza as entradas ou ajuste o dataset/filtros.')
    # Valida dados manuais e IDs antes de iniciar qualquer solver.
    prepare_problem(developers, tasks, {
        **config, 'quantidade_devs': max_devs, 'quantidade_tarefas': max_tasks,
    })
    cases = []
    for dev_count, task_count in sizes:
        case = {'entrada': f'{dev_count}x{task_count}', 'resultados': {}, 'execucoes': {}}
        for algorithm in algorithms:
            label = STYLES[algorithm][0]
            run_config = {
                **config, 'algoritmo': algorithm,
                'quantidade_devs': dev_count, 'quantidade_tarefas': task_count,
            }
            samples = []
            for repetition in range(1, repetitions + 1):
                progress = f' (execucao {repetition}/{repetitions})' if repetitions > 1 else ''
                print(f"Executando {label}: {case['entrada']}{progress}...", flush=True)
                result = allocate(developers, tasks, run_config, trace=False)
                if (result['total_devs'], result['total_tarefas']) != (dev_count, task_count):
                    raise ValueError(f"O solver retornou um tamanho diferente da entrada {case['entrada']}.")
                elapsed = result['metricas']['matching_ms']
                if not math.isfinite(elapsed) or elapsed < 0:
                    raise ValueError(f"Tempo invalido para {label} na entrada {case['entrada']}.")
                samples.append({
                    'total_devs': result['total_devs'], 'total_tarefas': result['total_tarefas'],
                    'ordem_devs': result['ordem_devs'], 'ordem_tarefas': result['ordem_tarefas'],
                    'pares': len(result['alocacoes']), 'pontuacao_total': result['pontuacao_total'],
                    **result['metricas'],
                })
                work = (f" | {result['metricas']['estados_explorados']} estados, "
                        f"{result['metricas']['solucoes_avaliadas']} solucoes"
                        if algorithm == 'brute_force' else '')
                if algorithm == 'bfs':
                    work = f" | {result['metricas']['arestas_examinadas']} arestas examinadas"
                print(f'  {elapsed:.6f} ms{work}', flush=True)
                # Guarda somente os diagnosticos, liberando a matriz antes da proxima chamada.
                del result
            case['resultados'][algorithm] = median(sample['matching_ms'] for sample in samples)
            case['execucoes'][algorithm] = samples
            if repetitions > 1:
                print(f"  Mediana de {repetitions} execucoes: {case['resultados'][algorithm]:.6f} ms", flush=True)
        cases.append(case)
    return cases


def resolve_y_scale(cases, algorithms, scale):
    if scale not in ('auto', 'linear', 'log'):
        raise ValueError('A escala Y deve ser auto, linear ou log.')
    values = [case['resultados'][algorithm] for case in cases for algorithm in algorithms]
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError('O grafico exige tempos finitos e nao negativos.')
    if scale == 'log' and min(values) == 0:
        raise ValueError('A escala logaritmica exige tempos maiores que zero; use --escala-y auto ou linear.')
    if scale == 'auto':
        # Mantem zeros reais visiveis; nunca os substitui por um tempo inventado.
        return ('log' if min(values) > 0 and math.log10(max(values)) - math.log10(min(values)) >= 2
                else 'linear')
    return scale


def plot_benchmark(cases, algorithms, source, output, scale='auto', repetitions=1):
    """Exporta sem display, inclusive no container, com legenda abaixo dos eixos."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator, NullFormatter, ScalarFormatter

    effective_scale = resolve_y_scale(cases, algorithms, scale)
    ink, muted, border = '#17243B', '#617089', '#E3EAF3'
    figure = Figure(figsize=(max(11.5, min(18, len(cases) * .7)), 7.5),
                    dpi=180, facecolor='#F5F7FB')
    FigureCanvasAgg(figure)
    figure.add_artist(FancyBboxPatch(
        (.055, .205), .9, .565, boxstyle='round,pad=0.012,rounding_size=0.018',
        transform=figure.transFigure, facecolor='white', edgecolor=border,
        linewidth=.8, zorder=0))
    axis = figure.subplots()
    axis.set_facecolor('white')
    axis.set_yscale(effective_scale)
    positions = list(range(len(cases)))
    for algorithm in algorithms:
        label, color, marker = STYLES[algorithm]
        axis.plot(positions, [case['resultados'][algorithm] for case in cases],
                  label=label, color=color, marker=marker, linewidth=2.6,
                  markersize=7.5, markeredgecolor='white', markeredgewidth=1.6,
                  solid_capstyle='round', solid_joinstyle='round', zorder=3)
    axis.set_xticks(positions, [case['entrada'] for case in cases],
                    rotation=45 if len(cases) > 10 else 0)
    axis.set_xlabel('Entrada (desenvolvedores x tarefas)',
                    fontsize=10, color=muted, labelpad=14, fontfamily='DejaVu Sans')
    time_label = 'Tempo mediano do solver (ms)' if repetitions > 1 else 'Tempo do solver (ms)'
    axis.set_ylabel(time_label, fontsize=10, color=muted,
                    labelpad=14, fontfamily='DejaVu Sans')
    axis.margins(x=.045, y=.14)
    if effective_scale == 'linear':
        axis.set_ylim(bottom=0)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5, min_n_ticks=3))
        formatter = ScalarFormatter(useOffset=False)
        formatter.set_scientific(False)
        axis.yaxis.set_major_formatter(formatter)
    else:
        axis.yaxis.set_major_locator(LogLocator(base=10, numticks=8))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f'{value:g}'))
        axis.yaxis.set_minor_locator(LogLocator(base=10, subs=(2, 5), numticks=40))
        axis.yaxis.set_minor_formatter(NullFormatter())
        axis.grid(axis='y', which='minor', color=border, linewidth=.6, linestyle=':', alpha=.7)
    axis.set_axisbelow(True)
    axis.grid(axis='y', color=border, linewidth=.8)
    axis.tick_params(axis='both', which='both', length=0, labelsize=10,
                     labelcolor=muted, pad=10)
    for side in ('top', 'right', 'left'):
        axis.spines[side].set_visible(False)
    axis.spines['bottom'].set_color(border)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_fontfamily('DejaVu Sans')

    text_style = {'fontfamily': 'DejaVu Sans', 'color': ink}
    figure.text(.065, .94, 'MATCHING LAB  /  BENCHMARK', fontsize=9,
                fontweight='bold', **text_style)
    figure.text(.065, .875, 'Tempo de execução por algoritmo', fontsize=23,
                fontweight='bold', **text_style)
    source_label = 'MYSQL' if source == 'banco' else 'DADOS SINTÉTICOS'
    figure.text(.945, .94, source_label, ha='right', fontsize=8, fontweight='bold',
                bbox={'boxstyle': 'round,pad=.65', 'facecolor': '#E8EEF8', 'edgecolor': 'none'},
                **text_style)
    description = ('Critérios e filtros da configuração aplicados.' if source == 'banco'
                   else 'Todos os pares permitidos, com pontuações iguais.')
    execution_label = ('Uma execução por entrada.' if repetitions == 1
                       else f'Mediana de {repetitions} execuções por entrada.')
    figure.text(.065, .825, f'{description}  {execution_label}',
                fontsize=10, color=muted, fontfamily='DejaVu Sans')
    note = ('Amostra única: pausas do sistema podem afetar os tempos.' if repetitions == 1
            else 'Cada ponto representa a mediana, sem execuções de aquecimento.')
    figure.text(.065, .79, note,
                fontsize=8, color=muted, fontfamily='DejaVu Sans')
    figure.legend(*axis.get_legend_handles_labels(), loc='lower center',
                  bbox_to_anchor=(.5, .115), ncol=len(algorithms), frameon=False,
                  prop={'family': 'DejaVu Sans', 'size': 10}, labelcolor=ink,
                  handlelength=2.6, handletextpad=.8, columnspacing=2.5)
    figure.add_artist(Line2D([.065, .945], [.085, .085],
                            transform=figure.transFigure, color=border, linewidth=.8))
    scale_label = 'LOGARÍTMICA' if effective_scale == 'log' else 'LINEAR'
    figure.text(.065, .045, f'MILISSEGUNDOS (ms)  ·  ESCALA {scale_label}',
                fontsize=8, color=muted, fontfamily='DejaVu Sans')
    figure.text(.945, .045, 'Exclui leitura do banco, preparação e exportação.',
                ha='right', fontsize=8, color=muted, fontfamily='DejaVu Sans')
    figure.subplots_adjust(left=.12, right=.93, top=.735,
                           bottom=.34 if len(cases) > 10 else .30)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=output.suffix, delete=False) as stream:
            temporary = Path(stream.name)
        figure.savefig(temporary, format=output.suffix[1:].lower())
        temporary.chmod(0o644)
        temporary.replace(output)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
        figure.clear()
    return effective_scale


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonte', choices=('banco', 'sintetico'), default='banco',
                        help='banco: MySQL e criterios atuais (padrao); sintetico: todos os pares, notas iguais')
    parser.add_argument('--algoritmos', nargs='+', choices=(*ALGORITHMS, 'brute'),
                        default=['bfs', 'scipy', 'greedy'],
                        help='Solvers a comparar; brute e um alias de brute_force (padrao: bfs scipy greedy)')
    parser.add_argument('--entradas', nargs='+', type=input_size, required=True,
                        metavar='DEVSxTAREFAS', help='Tamanhos exatos na ordem do grafico, ex.: 1x1 2x2 3x5')
    parser.add_argument('--config', type=Path, default=ROOT / 'config/critérios.json')
    parser.add_argument('--saida', type=Path, default=ROOT / 'resultados/comparacao.png',
                        help='Grafico .png, .svg ou .pdf (padrao: resultados/comparacao.png)')
    parser.add_argument('--escala-y', choices=('auto', 'linear', 'log'), default='auto',
                        help='Eixo Y: auto usa log quando os tempos positivos variam pelo menos 100x (padrao: auto)')
    parser.add_argument('--repeticoes', type=positive_integer, default=1,
                        help='Execucoes por algoritmo e entrada; o grafico mostra a mediana (padrao: 1)')
    parser.add_argument('-s', '--sprints', type=positive_integer, help='Limite de sprints, somente na fonte banco')
    parser.add_argument('-p', '--projetos', type=positive_integer, help='Limite de projetos, somente na fonte banco')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    algorithms = ['brute_force' if name == 'brute' else name for name in args.algoritmos]
    if len(set(algorithms)) != len(algorithms):
        parser.error('Selecione cada algoritmo apenas uma vez (brute e brute_force sao o mesmo solver).')
    if len(set(args.entradas)) != len(args.entradas):
        parser.error('Informe cada entrada apenas uma vez.')
    if args.saida.suffix.lower() not in FORMATS:
        parser.error('A saida deve ter extensao .png, .svg ou .pdf.')
    if args.saida.with_suffix('.json').resolve() == args.config.resolve():
        parser.error('O JSON de medicoes nao pode substituir o arquivo de configuracao; escolha outra saida.')
    if args.fonte == 'sintetico' and (args.sprints is not None or args.projetos is not None):
        parser.error('--sprints e --projetos se aplicam somente a --fonte banco.')
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('A configuracao deve ser um objeto JSON.')
    config = deepcopy(config)
    # Esta execucao usa a selecao da CLI, nao o algoritmo individual do JSON.
    config.pop('algoritmo', None)
    config['quantidade_devs'] = max(size[0] for size in args.entradas)
    config['quantidade_tarefas'] = max(size[1] for size in args.entradas)
    if args.fonte == 'banco':
        if args.sprints is not None:
            config['quantidade_sprints'] = args.sprints
        if args.projetos is not None:
            config['quantidade_projetos'] = args.projetos
        validate_config(config)
        # A selecao/ordem de cada tamanho sera aplicada por allocate, uma unica vez.
        developers, tasks = load_data({**config, 'semente_embaralhamento': None})
        print('Fonte: MySQL; filtros e criterios da configuracao aplicados.')
    else:
        dev_count, task_count = config['quantidade_devs'], config['quantidade_tarefas']
        config = {key: config[key] for key in ('direcao', 'semente_embaralhamento') if key in config}
        validate_config(config)
        developers, tasks = synthetic_data(dev_count, task_count)
        print('Fonte: sintetica; todos os pares permitidos, notas iguais; criterios e filtros ignorados.')
    print(f'Medicao: solver somente, {args.repeticoes} execucao(oes) por algoritmo e entrada; sem trace ou aquecimento.')
    print('O grafico mostra a mediana dos tempos; todas as amostras sao salvas no JSON.')
    cases = benchmark(developers, tasks, config, args.entradas, algorithms, repetitions=args.repeticoes)
    effective_scale = plot_benchmark(cases, algorithms, args.fonte, args.saida,
                                     scale=args.escala_y, repetitions=args.repeticoes)
    measurements = args.saida.with_suffix('.json')
    save_result({
        'fonte': args.fonte, 'algoritmos': algorithms, 'metrica': 'matching_ms', 'unidade': 'ms',
        'escala_y': effective_scale, 'escala_y_solicitada': args.escala_y,
        'formato_versao': 2, 'agregacao': 'mediana', 'execucoes_por_ponto': args.repeticoes,
        'aquecimento': False, 'configuracao_efetiva': config,
        'ambiente': {'python': platform.python_version(), 'sistema': platform.system(),
                     'arquitetura': platform.machine(), 'relogio': vars(get_clock_info('perf_counter'))},
        'entradas': cases,
    }, measurements)
    print(f'Grafico salvo em: {args.saida.resolve()}')
    print(f'Escala do eixo Y: {effective_scale}')
    print(f'Medicoes e contadores salvos em: {measurements.resolve()}')
    return cases


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, MySQLError, KeyError, RecursionError) as error:
        print(f'Erro na comparacao: {error}', file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print('\nComparacao interrompida.', file=sys.stderr)
        raise SystemExit(130)
