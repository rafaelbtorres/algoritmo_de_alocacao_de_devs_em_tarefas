#!/usr/bin/env python3
"""Recorte real do TAWOS com varios projetos/sprints e tamanho aproximado em MB.

Execute: python -m scripts.criar_dataset_ampliado origem.sql saida.sql
"""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re

from scripts.reduzir_tawos import INSERT, METADATA, number, rows, usable

HEADER = (b'-- TAWOS ampliado: recorte real com tarefas, usuarios, sprints e contexto.\n'
          b'-- Usa o banco selecionado pelo cliente; substitui as 13 tabelas do dataset.\n'
          b'SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n'
          b'SET @OLD_SQL_MODE=@@SQL_MODE;\nSET SQL_MODE=\'NO_AUTO_VALUE_ON_ZERO\';\n')
FOOTER = b'\nSET SQL_MODE=@OLD_SQL_MODE;\nSET FOREIGN_KEY_CHECKS=1;\n'


def record_sql(table, raw):
    return f'INSERT INTO `{table}` VALUES '.encode() + raw + b';\n'


def extract(source, destination, projects_count=3, sprints_per_project=4,
            tasks_per_sprint=40, target_bytes=5_000_000):
    if destination.exists() or source.resolve() == destination.resolve():
        raise ValueError('A saida deve ser nova e diferente da origem.')
    if min(projects_count, sprints_per_project, tasks_per_sprint, target_bytes) < 1:
        raise ValueError('Quantidades e tamanho devem ser positivos.')
    schemas, columns = {}, {}
    metadata = {table: {} for table in METADATA}
    counts = Counter()
    current = None
    print('1/3 Lendo estrutura, usuarios e disponibilidade de tarefas por sprint...', flush=True)
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
        if count >= tasks_per_sprint and record and number(record[1][8]) == project:
            candidates[project].append(sprint)
    project_ids = [pid for pid in sorted(candidates) if len(candidates[pid]) >= sprints_per_project][:projects_count]
    if len(project_ids) != projects_count:
        raise ValueError('Nao ha projetos/sprints suficientes com a quantidade de tarefas solicitada.')
    sprint_ids = []
    for pid in project_ids:
        sprint_ids.extend(sorted(candidates[pid], key=lambda sid: (metadata['Sprint'][sid][1][4], sid))[:sprints_per_project])
    project_set, sprint_set = set(project_ids), set(sprint_ids)
    print(f'2/3 Selecionando {tasks_per_sprint} tarefas por sprint em {len(sprint_ids)} sprints...', flush=True)
    selected = {table: [] for table in schemas}
    chosen, users = Counter(), set()
    with source.open('rb') as stream:
        for line in stream:
            match = INSERT.match(line)
            if not match or match[1] != b'Issue':
                continue
            for raw, fields in rows(line[match.end():]):
                project, sprint = number(fields[28]), number(fields[29])
                if project not in project_set or sprint not in sprint_set or chosen[sprint] >= tasks_per_sprint or not usable(fields):
                    continue
                related = {number(fields[i]) for i in (25, 26, 27)} - {None}
                if any(uid not in metadata['User'] or number(metadata['User'][uid][1][1]) != project for uid in related):
                    continue
                selected['Issue'].append((raw, fields))
                users.update(related)
                chosen[sprint] += 1
            if all(chosen[sid] == tasks_per_sprint for sid in sprint_ids):
                break
    if any(chosen[sid] != tasks_per_sprint for sid in sprint_ids):
        raise ValueError('Faltam tarefas com referencias validas; reduza --tarefas-por-sprint.')
    selected['User'] = [metadata['User'][uid] for uid in sorted(users)]
    selected['Sprint'] = [metadata['Sprint'][sid] for sid in sprint_ids]
    selected['Project'] = [metadata['Project'][pid] for pid in project_ids]
    repository_ids = {number(fields[8]) for _, fields in selected['Project']} - {None}
    selected['Repository'] = [metadata['Repository'][rid] for rid in sorted(repository_ids)]
    structures = {table: f'\nDROP TABLE IF EXISTS `{table}`;\n'.encode() + re.sub(rb' AUTO_INCREMENT=\d+', b'', schema) for table, schema in schemas.items()}
    size = len(HEADER) + len(FOOTER) + sum(map(len, structures.values()))
    size += sum(len(record_sql(table, raw)) for table, records in selected.items() for raw, _ in records)
    if size > target_bytes:
        raise ValueError('As tarefas ja ultrapassam o tamanho alvo. Reduza o numero de tarefas ou aumente --tamanho-mb.')
    issue_ids = {number(fields[0]) for _, fields in selected['Issue']}
    # O contexto vem apenas de comentarios/historico reais das tarefas escolhidas.
    # Autores adicionais sao incluidos com suas referencias, sem inventar registros.
    print(f'3/3 Adicionando contexto real ate aproximadamente {target_bytes:,} bytes...', flush=True)
    for table in ('Comment', 'Change_Log'):
        author_index = columns[table].index('Author_ID')
        issue_index = columns[table].index('Issue_ID')
        if target_bytes - size < 8192:
            break
        print(f'  Buscando {table} das tarefas selecionadas...', flush=True)
        with source.open('rb') as stream:
            for line in stream:
                match = INSERT.match(line)
                if not match or match[1].decode() != table:
                    continue
                for raw, fields in rows(line[match.end():]):
                    if number(fields[issue_index]) not in issue_ids:
                        continue
                    author = number(fields[author_index])
                    extra_user = None
                    if author is not None and author not in users:
                        extra_user = metadata['User'].get(author)
                        if extra_user is None or number(extra_user[1][1]) not in project_set:
                            continue
                    cost = len(record_sql(table, raw))
                    if extra_user:
                        cost += len(record_sql('User', extra_user[0]))
                    if size + cost > target_bytes:
                        continue
                    selected[table].append((raw, fields))
                    if extra_user:
                        selected['User'].append(extra_user)
                        users.add(author)
                    size += cost
                    if target_bytes - size < 8192:
                        break
                if target_bytes - size < 8192:
                    break
    validate_references(schemas, columns, selected)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as output:
        output.write(HEADER)
        for table in schemas:
            output.write(structures[table])
            for raw, _ in selected[table]:
                output.write(record_sql(table, raw))
        output.write(FOOTER)
    print(f'Criado: {destination} ({destination.stat().st_size:,} bytes)', flush=True)
    for table, records in selected.items():
        print(f'  {table}: {len(records)}')
    if target_bytes - size >= 8192:
        print('O contexto disponivel terminou antes do tamanho alvo; nao foi adicionado preenchimento artificial.')
    return selected


def validate_references(schemas, columns, selected):
    for table, schema in schemas.items():
        for column, target, target_column in re.findall(rb'FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\)', schema):
            index = columns[table].index(column.decode())
            target = target.decode()
            target_index = columns[target].index(target_column.decode())
            valid = {fields[target_index] for _, fields in selected[target]}
            for _, fields in selected[table]:
                if fields[index] != b'NULL' and fields[index] not in valid:
                    raise ValueError(f'Referencia ausente: {table}.{column.decode()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('origem', type=Path)
    parser.add_argument('saida', type=Path)
    parser.add_argument('--projetos', type=int, default=3)
    parser.add_argument('--sprints-por-projeto', type=int, default=4)
    parser.add_argument('--tarefas-por-sprint', type=int, default=40)
    parser.add_argument('--tamanho-mb', type=float, default=5)
    args = parser.parse_args()
    extract(args.origem, args.saida, args.projetos, args.sprints_por_projeto,
            args.tarefas_por_sprint, int(args.tamanho_mb * 1_000_000))
