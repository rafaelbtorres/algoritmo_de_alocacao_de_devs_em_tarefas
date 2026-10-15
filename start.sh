#!/usr/bin/env bash
# Menu local em Bash. Python e bibliotecas executam somente no container.
set -o pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || exit 1
ENV_FILE="$ROOT/.env"
MYSQL_IMPORT='export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysql -uroot --default-character-set=utf8mb4 --binary-mode=1 "$MYSQL_DATABASE"'

compose() {
    docker compose --project-directory "$ROOT" --env-file "$ENV_FILE" -f "$ROOT/compose.yaml" "$@"
}

check_tools() {
    local tool missing=0
    for tool in docker dirname od tr mktemp mkdir rm cat gzip; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            printf '[FALTA] %s\n' "$tool"
            missing=1
        fi
    done
    if (( missing )); then
        printf '%s\n' 'Instale Docker Engine com Compose v2+ ou Docker Desktop.' \
            'Utilitarios ausentes: instale coreutils e gzip pelo gerenciador de pacotes do sistema.'
        return 1
    fi
}

check_docker() {
    command -v docker >/dev/null 2>&1 || { echo 'Docker nao instalado. Instale Docker Engine/Desktop.'; return 1; }
    docker compose version >/dev/null 2>&1 || { echo 'Compose ausente. Instale o plugin Docker Compose v2+ ou Docker Desktop.'; return 1; }
    docker info >/dev/null 2>&1 || {
        echo 'Docker indisponivel: inicie Docker Engine/Desktop e verifique a permissao do usuario.'
        docker info >/dev/null
        return 1
    }
}

analyze() {
    local failures=0 help_text tool
    echo '=== Analise do ambiente ==='
    printf '[OK] Bash %s\n' "$BASH_VERSION"
    for tool in dirname od tr mktemp mkdir rm cat gzip; do
        if command -v "$tool" >/dev/null 2>&1; then
            printf '[OK] %s\n' "$tool"
        else
            printf '[FALTA] %s: instale coreutils/gzip pelo gerenciador de pacotes.\n' "$tool"
            failures=$((failures + 1))
        fi
    done
    if command -v docker >/dev/null 2>&1; then
        echo '[OK] Docker CLI instalado'
        if docker compose version; then
            help_text=$(docker compose up --help 2>/dev/null)
            if [[ "$help_text" != *--wait-timeout* ]]; then
                echo '[FALTA] Atualize o Compose: este ambiente requer suporte a --wait-timeout.'
                failures=$((failures + 1))
            fi
        else
            echo '[FALTA] Instale o plugin Docker Compose v2+ ou Docker Desktop.'
            failures=$((failures + 1))
        fi
        if docker info >/dev/null 2>&1; then
            echo '[OK] Servico Docker ativo e acessivel'
        else
            echo '[ERRO] Docker inacessivel. Inicie o servico/Desktop e confira as permissoes do usuario.'
            docker info >/dev/null
            failures=$((failures + 1))
        fi
    else
        echo '[FALTA] Instale Docker Engine com Compose v2+ ou Docker Desktop.'
        failures=$((failures + 1))
    fi
    for tool in compose.yaml Dockerfile requirements.txt .env.example config/critérios.json app/main.py app/db.py app/matching.py web/app.py web/templates/index.html web/static/app.js web/static/style.css; do
        if [[ -r "$ROOT/$tool" ]]; then
            printf '[OK] Arquivo %s\n' "$tool"
        else
            printf '[FALTA] Arquivo %s: restaure os arquivos do projeto.\n' "$tool"
            failures=$((failures + 1))
        fi
    done
    if [[ ! -w "$ROOT" ]]; then
        echo '[ERRO] Sem permissao de escrita no projeto.'
        failures=$((failures + 1))
    else
        echo '[OK] Permissao para criar configuracao e resultados'
    fi
    if [[ -f "$ENV_FILE" ]]; then
        if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
            if compose config --quiet; then
                echo '[OK] Configuracao Compose e .env validos'
            else
                echo '[ERRO] Corrija .env/compose.yaml antes de iniciar.'
                failures=$((failures + 1))
            fi
        fi
    else
        echo '[INFO] .env sera criado com senhas aleatorias ao usar o menu.'
    fi
    echo '[INFO] Python, MySQL e phpMyAdmin serao instalados nas imagens Docker.'
    echo '[INFO] O primeiro build precisa de internet e espaco em disco para imagens e datasets.'
    if (( failures )); then
        printf 'Analise concluida: %s pendencia(s). Corrija as mensagens acima.\n' "$failures"
        return 1
    fi
    echo 'Analise concluida: dependencias verificadas. Use a opcao 1 para iniciar.'
}

ensure_env() (
    [[ -e "$ENV_FILE" ]] && return 0
    [[ -r "$ROOT/.env.example" ]] || { echo 'Arquivo .env.example ausente.'; return 1; }
    local root_password password line
    root_password=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n') || return 1
    password=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n') || return 1
    [[ ${#root_password} == 48 && ${#password} == 48 ]] || return 1
    umask 077
    # noclobber impede sobrescrever configuracao criada por outro processo.
    set -o noclobber
    {
        while IFS= read -r line || [[ -n "$line" ]]; do
            line=${line//troque_esta_senha_root/$root_password}
            line=${line//troque_esta_senha/$password}
            printf '%s\n' "$line"
        done < "$ROOT/.env.example"
    } > "$ENV_FILE" || return 1
    echo '.env criado com senhas aleatorias e acesso restrito ao usuario.'
)

setting() {
    local key value
    while IFS='=' read -r key value; do
        if [[ "$key" == "$1" ]]; then
            value=${value%$'\r'}
            value=${value#\"}; value=${value%\"}
            value=${value#\'}; value=${value%\'}
            printf '%s' "$value"
            return
        fi
    done < "$ENV_FILE"
    printf '%s' "$2"
}

access() {
    printf 'phpMyAdmin: http://localhost:%s\n' "$(setting PHPMYADMIN_PORT 8081)"
    printf 'MySQL no host: 127.0.0.1:%s\n' "$(setting MYSQL_PORT 3308)"
    printf 'Banco: %s | Usuario: %s\n' "$(setting DB_NAME alocacao)" "$(setting DB_USER alocacao)"
    echo 'Senhas em .env. Para dumps que criam outros bancos, use root.'
}

import_sql() (
    local path="${1:-}" confirmation unpacked=''
    if [[ -z "$path" ]]; then
        read -r -p 'Caminho .sql ou .sql.gz (Enter cancela): ' path || return 1
    fi
    [[ -n "$path" ]] || return 0
    case "$path" in '~/'*) path="$HOME/${path:2}" ;; esac
    [[ "$path" == /* ]] || path="$ROOT/$path"
    case "$path" in *.sql|*.sql.gz) ;; *) echo 'Extensao invalida: use .sql ou .sql.gz.'; return 1 ;; esac
    [[ -f "$path" && -r "$path" ]] || { echo 'Arquivo inexistente ou sem permissao de leitura.'; return 1; }
    echo 'O SQL sera executado como root e pode substituir dados ou criar bancos.'
    echo 'Um erro SQL pode deixar comandos parcialmente aplicados.'
    read -r -p 'Digite IMPORTAR para confirmar: ' confirmation || return 1
    [[ "$confirmation" == IMPORTAR ]] || { echo 'Operacao cancelada.'; return 0; }
    if [[ "$path" == *.gz ]]; then
        unpacked=$(mktemp) || return 1
        trap 'rm -f -- "$unpacked"' EXIT
        trap 'exit 130' INT
        trap 'exit 143' TERM
        # Descompacta e valida todo o arquivo antes de executar SQL.
        gzip -dc -- "$path" > "$unpacked" || { echo 'Falha ao descompactar. Nenhum SQL foi importado.'; return 1; }
        compose exec -T db sh -c "$MYSQL_IMPORT" < "$unpacked" || return 1
    else
        compose exec -T db sh -c "$MYSQL_IMPORT" < "$path" || return 1
    fi
    echo 'Importacao concluida.'
    echo 'Se o dump usa outro banco, ajuste DB_NAME no .env e use a opcao 1.'
)

select_sql() {
    local path choice index
    local -a files=()
    for path in "$ROOT/datasets/"*.sql "$ROOT/datasets/"*.sql.gz; do
        [[ -f "$path" ]] && files+=("$path")
    done
    echo 'Datasets disponiveis:'
    if (( ${#files[@]} == 0 )); then
        echo 'Nenhum arquivo SQL disponivel em datasets/.'
    else
        for ((index=0; index<${#files[@]}; index++)); do
            printf ' %s - %s\n' "$((index + 1))" "${files[index]#"$ROOT/"}"
        done
    fi
    echo ' I - Importar outro arquivo SQL'
    echo ' 0 - Voltar'
    while true; do
        read -r -p 'Escolha o numero do arquivo ou I para importar (Enter cancela): ' choice || return 0
        case "$choice" in
            ''|0) return 0 ;;
            i|I) import_sql; return $? ;;
        esac
        # Compara texto sem avaliar a entrada como expressao aritmetica.
        for ((index=0; index<${#files[@]}; index++)); do
            if [[ "$choice" == "$((index + 1))" ]]; then
                printf 'Arquivo selecionado: %s\n' "${files[index]#"$ROOT/"}"
                import_sql "${files[index]}"
                return $?
            fi
        done
        echo 'Opcao invalida. Escolha um numero listado, I ou 0.'
    done
}

database_menu() {
    local choice
    while true; do
        cat <<'MENU'

=== Banco de dados ===
 1 - Importar dataset SQL
 2 - Ver acesso ao phpMyAdmin
 0 - Voltar
MENU
        read -r -p 'Escolha: ' choice || return 0
        case "$choice" in
            0) return 0 ;;
            1) check_docker && select_sql ;;
            2) access ;;
            *) echo 'Opcao invalida.'; continue ;;
        esac
        if (( $? != 0 )); then echo 'Operacao falhou. Confira o Docker e a configuracao em .env.'; fi
    done
}

web_access() {
    local host port
    host=$(setting WEB_HOST 127.0.0.1)
    port=$(setting WEB_PORT 8000)
    printf 'Interface web | IP: %s | Porta: %s\n' "$host" "$port"
    if [[ "$host" == 0.0.0.0 ]]; then
        printf 'Acesso neste computador: http://127.0.0.1:%s\n' "$port"
        echo 'Para outro computador, use o IP de rede deste computador.'
    else
        printf 'Acesse: http://%s:%s\n' "$host" "$port"
    fi
    echo 'Se a pagina nao abrir, inicie o ambiente pela opcao 1.'
}

start_environment() {
    compose up -d --build --wait --wait-timeout 360 && access && web_access
}

run_allocation() {
    mkdir -p -- "$ROOT/resultados" &&
        compose ps --all && access &&
        compose exec -T app python -m app.main
}

main() {
    local choice
    trap 'echo; echo "Operacao interrompida. Use a opcao 5 para verificar o ambiente."' INT
    while true; do
        cat <<'MENU'

=== Ambiente de alocacao de desenvolvedores ===
 1 - Iniciar / atualizar ambiente
 2 - Executar alocacao
 3 - Banco de dados (importar e acesso)
 4 - Encerrar ambiente (preserva banco)
 5 - Analisar ambiente e dependencias
 6 - Mostrar IP e porta da interface web
 0 - Sair
MENU
        read -r -p 'Escolha: ' choice || return 0
        case "$choice" in
            0) return 0 ;;
            5) analyze; continue ;;
            1|2|3|4|6) ;;
            *) echo 'Opcao invalida.'; continue ;;
        esac
        check_tools || continue
        ensure_env || { echo 'Nao foi possivel criar/ler .env.'; continue; }
        if [[ "$choice" != 3 && "$choice" != 6 ]]; then check_docker || continue; fi
        case "$choice" in
            1) start_environment ;;
            2) run_allocation ;;
            3) database_menu ;;
            6) web_access ;;
            4) compose down --remove-orphans && echo 'Ambiente encerrado. Banco preservado.' ;;
        esac
        if (( $? != 0 )); then echo 'Operacao falhou. Use a analise (5) e confira .env.'; fi
    done
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    case "${1:-}" in
        --analisar) analyze ;;
        '') main ;;
        *) echo 'Uso: bash start.sh [--analisar]'; exit 2 ;;
    esac
fi
