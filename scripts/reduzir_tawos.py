#!/usr/bin/env python3
"""Extrai dados reais de um projeto e duas sprints sem carregar o dump na RAM."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re

INSERT = re.compile(rb'^INSERT INTO `([^`]+)` VALUES ')
TOKEN = re.compile(rb"'(?:[^'\\]+|\\.)*'|[(),]|[^'(),]+")
METADATA = {'Sprint', 'Project', 'Repository', 'User'}


def rows(payload):
    """Separa tuplas/colunas respeitando virgulas, parenteses e escapes nas strings."""
    start = field_start = None
    fields = []
    for token in TOKEN.finditer(payload):
        value = token.group()
        if value == b'(':
            start = token.start()
            field_start = token.end()
            fields = []
        elif value == b',' and start is not None:
            fields.append(payload[field_start:token.start()].strip())
            field_start = token.end()
        elif value == b')' and start is not None:
            fields.append(payload[field_start:token.start()].strip())
            yield payload[start:token.end()], fields
            start = None


def number(value):
    return None if value == b'NULL' else int(value)


def usable(fields):
    return (fields[27] != b'NULL' and fields[16] != b'NULL'
            and float(fields[16]) > 0 and fields[29] != b'NULL')


def extract(source, destination, per_sprint=20):
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Escolha uma saida nova, diferente do arquivo original.')
    schemas, columns = {}, {}
    metadata = {table: {} for table in METADATA}
    counts = Counter()
    current = None
    print('Lendo estrutura e identificando sprints com tarefas estimadas...', flush=True)
    with source.open('rb') as stream:
        for line in stream:
            if line.startswith(b'CREATE TABLE `'):
                current = line.split(b'`')[1].decode()
                schemas[current] = bytearray(line)
                columns[current] = []
                continue
            if current:
                schemas[current].extend(line)
                if line.startswith(b'  `'):
                    columns[current].append(line.split(b'`')[1].decode())
                if line.startswith(b') ENGINE='):
                    current = None
                continue
            match = INSERT.match(line)
            if not match:
                continue
            table = match[1].decode()
            if table not in METADATA and table != 'Issue':
                continue
            for raw, fields in rows(line[match.end():]):
                if table in METADATA:
                    metadata[table][number(fields[0])] = (raw, fields)
                elif usable(fields):
                    counts[(number(fields[28]), number(fields[29]))] += 1
    candidates = defaultdict(list)
    for (project, sprint), count in counts.items():
        record = metadata['Sprint'].get(sprint)
        if count >= per_sprint and record and number(record[1][8]) == project:
            candidates[project].append(sprint)
    project = next((p for p in sorted(candidates) if len(candidates[p]) >= 2), None)
    if project is None:
        raise ValueError(f'Nao foram encontradas duas sprints com {per_sprint} tarefas estimadas e com responsavel.')
    sprint_ids = sorted(candidates[project], key=lambda sid: (
        metadata['Sprint'][sid][1][4], sid))[:2]
    print(f'Projeto {project}, sprints {sprint_ids}: selecionando ate {per_sprint} tarefas por sprint...', flush=True)
    selected = {table: [] for table in schemas}
    chosen = Counter()
    user_ids = set()
    with source.open('rb') as stream:
        for line in stream:
            match = INSERT.match(line)
            if not match or match[1] != b'Issue':
                continue
            for raw, fields in rows(line[match.end():]):
                sprint = number(fields[29])
                if (number(fields[28]) != project or sprint not in sprint_ids
                        or chosen[sprint] >= per_sprint or not usable(fields)):
                    continue
                users = {number(fields[i]) for i in (25, 26, 27)} - {None}
                if any(uid not in metadata['User'] or number(metadata['User'][uid][1][1]) != project for uid in users):
                    continue
                selected['Issue'].append((raw, fields))
                user_ids.update(users)
                chosen[sprint] += 1
            if all(chosen[sid] == per_sprint for sid in sprint_ids):
                break
    if any(chosen[sid] != per_sprint for sid in sprint_ids):
        raise ValueError('Nao ha tarefas suficientes com usuarios do mesmo projeto; reduza --tarefas-por-sprint.')
    selected['User'] = [metadata['User'][uid] for uid in sorted(user_ids)]
    selected['Sprint'] = [metadata['Sprint'][sid] for sid in sprint_ids]
    selected['Project'] = [metadata['Project'][project]]
    repository = number(selected['Project'][0][1][8])
    if repository is not None:
        selected['Repository'] = [metadata['Repository'][repository]]
    # Confere cada FK, inclusive tabelas que ficam vazias, antes de gravar.
    for table, schema in schemas.items():
        foreign_keys = re.findall(rb'FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\)', schema)
        for column, target, target_column in foreign_keys:
            index = columns[table].index(column.decode())
            target = target.decode()
            target_index = columns[target].index(target_column.decode())
            valid = {fields[target_index] for _, fields in selected[target]}
            for _, fields in selected[table]:
                if fields[index] != b'NULL' and fields[index] not in valid:
                    raise ValueError(f'Referencia ausente: {table}.{column.decode()}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as output:
        output.write(b'-- TAWOS reduzido: dados reais, sem comentarios ou historico de alteracoes.\n')
        output.write(f'-- Projeto {project}; sprints {sprint_ids}; {sum(chosen.values())} tarefas.\n'.encode())
        output.write(b'-- Usa o banco selecionado pelo cliente MySQL; substitui as 13 tabelas do dataset.\n')
        output.write(b'SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\nSET @OLD_SQL_MODE=@@SQL_MODE;\nSET SQL_MODE=\'NO_AUTO_VALUE_ON_ZERO\';\n')
        for table, schema in schemas.items():
            output.write(f'\nDROP TABLE IF EXISTS `{table}`;\n'.encode())
            # Reinicia a sequencia a partir dos IDs efetivamente importados.
            output.write(re.sub(rb' AUTO_INCREMENT=\d+', b'', schema))
            for raw, _ in selected[table]:
                output.write(f'INSERT INTO `{table}` VALUES '.encode() + raw + b';\n')
        output.write(b'\nSET SQL_MODE=@OLD_SQL_MODE;\nSET FOREIGN_KEY_CHECKS=1;\n')
    print(f'Arquivo criado: {destination} ({destination.stat().st_size:,} bytes)', flush=True)
    for table, records in selected.items():
        print(f'  {table}: {len(records)}')
    return selected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('origem', type=Path)
    parser.add_argument('saida', type=Path)
    parser.add_argument('--tarefas-por-sprint', type=int, default=20)
    args = parser.parse_args()
    if args.tarefas_por_sprint < 1:
        parser.error('--tarefas-por-sprint deve ser maior que zero')
    extract(args.origem, args.saida, args.tarefas_por_sprint)
