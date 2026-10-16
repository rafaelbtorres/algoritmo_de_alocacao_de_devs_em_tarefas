Algoritmo de Alocação de Desenvolvedores  para Realização de Tarefas

Problema Contexto
Hoje em dia no mercado de trabalho existem empresas cujo ramo é entregar projetos de desenvolvimento. Nesse cenário, a empresa ao fechar um novo contrato precisa alocar recursos humanos para o desenvolvimento do projeto. Porém isso não é uma tarefa fácil, principalmente porque o cenário de distribuição raramente é um dev para uma tarefa e sim várias tarefas para um dev ou vários dev para poucas tarefas.
	A distribuição de tarefas é feita manualmente pelo Gestor, e raramente é simples, um desenvolvedor assume diversas tarefas em um sprint, e as tarefas são associadas por uma skill específica, sem mencionar a capacidade de produção para cada desenvolvedor. Com dezenas de desenvolvedores e tarefas, trabalhar manualmente essa questão pode ocorrer erros e desperdício de mão de obra, afetando a produtividade e entrega dos projetos.
	Com isso, surge a necessidade da aplicação de um algoritmo que automatize essa distribuição de forma inteligente e eficaz. (Vamos trabalhar no texto)

Problema: 15.6 Matching

Algoritmo Potencial 
Com base no problema levantado acima, foi feito um levantamento de qual algoritmo seria mais adequado para iniciarmos à implementação. Escolhemos  inicialmente o Matching.
O Matching é um problema de otimização em grafos conhecido, utilizado para associar elementos de dois grupos distintos usando pesos e limites de associação. No cenário proposto, um grupo representa os desenvolvedores e o outro representa as tarefas. Então o algoritmo faz uso de pesos para indicar o nível de compatibilidade entre cada desenvolvedor e cada tarefa. Já os limites de associação definem quantas ligações um grupo pode ter com o outro.
Essa compatibilidade é definida a partir de critérios como habilidades necessárias, experiência, disponibilidade e capacidade de trabalho de cada desenvolvedor. O objetivo principal do algoritmo é de encontrar uma distribuição de tarefas que maximize a qualidade geral das alocações, respeitando as diferentes condições e situações de cada desenvolvedor e  tarefa.

Dataset público

TAWOS (Tawosi Agile Web-hosted Open-Source Issues) Dataset (V. 1.1) , criado por pesquisadores da University College London (UCL), contém tarefas de diferentes projetos.
GIT - https://github.com/SOLAR-group/TAWOS
SQL -  https://ndownloader.figshare.com/files/37806375
## Ambiente Docker e menu interativo

O ambiente inclui MySQL 8.4, phpMyAdmin e Python 3.12 com PyMySQL,
NumPy, pandas, SciPy, Flask e Gunicorn. O algoritmo em `app/matching.py` associa desenvolvedores a tarefas por matching
bipartido. A configuração inicial não aplica critérios de compatibilidade.

Use Bash e Docker Engine com Compose v2+ (ou Docker Desktop). Não é
necessário instalar Python, MySQL ou bibliotecas no computador; eles executam
nos containers. O menu usa utilitários do sistema (coreutils e gzip).
Execute na pasta do projeto:

```bash
bash start.sh
```

No Linux/macOS, execute pelo terminal Bash. No Windows, use WSL com a
integração do Docker Desktop ativada. O menu funciona a partir de qualquer
diretório, pois resolve os caminhos a partir do próprio script. Ao selecionar
uma operação de gerenciamento, ele cria `.env` com senhas aleatórias, caso
o arquivo ainda não exista; esse arquivo não é versionado. Confira portas e nome do banco antes de iniciar o ambiente.
Escolha **1** para construir e iniciar os containers. A primeira execução
precisa de internet e pode demorar para baixar imagens e dependências.

| Opção | Ação |
| --- | --- |
| 1 | Iniciar ou atualizar os containers, incluindo a interface web |
| 2 | Executar a alocação e mostrar os resultados |
| 3 | Banco de dados: importar um dataset SQL ou ver acesso ao phpMyAdmin |
| 4 | Encerrar os containers e a rede, preservando o banco |
| 5 | Analisar dependências e configuração do ambiente |
| 6 | Mostrar IP, porta e endereço da interface web |
| 0 | Sair do menu, mantendo o estado dos containers |

A opção 3 abre um menu com duas ações: **1 — Importar dataset SQL** e
**2 — Ver acesso ao phpMyAdmin**. Use 0 para
voltar. Para reiniciar o ambiente, escolha 4 e depois 1.

### Interface visual — Matching Lab

A pasta `web/` contém a interface e a API Flask. A opção **1** do menu sobe
o serviço web junto do MySQL e do phpMyAdmin. Acesse **http://127.0.0.1:8000**;
a opção **6** mostra o IP e a porta. Não é necessário instalar Node.js ou
executar um servidor separado. Os estilos, gráficos e scripts são locais,
sem depender de CDNs.

Na página, você pode:

- Selecionar **SciPy** ou **BFS (matching anterior)** e escolher o sentido
  desenvolvedores → tarefas ou tarefas → desenvolvedores.
- Usar **Comparar os dois** para ver quantidade de pares, pontuação total,
  participantes sem alocação e tempo de cada método no mesmo cenário. A
  comparação pode ser baixada em JSON; mudar critérios ou filtros a invalida.
- Selecionar projeto/sprint, limitar quantos devs e tarefas participam e explorar
  o recorte do banco antes de executar.
- Embaralhar a ordem inicial dos participantes ou restaurar a ordem por ID.
- Ativar critérios, definir o limite de story points e preencher habilidades
  e disponibilidade nas tabelas. Esses dados manuais complementam a simulação.
- Salvar os critérios no mesmo `config/critérios.json` usado pela linha de comando.
- Iniciar, pausar, continuar, avançar um passo, reiniciar a reprodução e ajustar
  sua velocidade. A cada alocação, o grafo mostra os pares atuais.
- Ver a distribuição de tarefas alocadas/sem dev, tempos de leitura do banco,
  preparação da matriz e cálculo SciPy, pontuação total e download JSON.
- Configurar pesos de preferência de 0 a 100 para mesmo projeto, disponibilidade
  e habilidades atendidas, independentemente das restrições obrigatórias.
- Calcular a matriz de pontuações antes da alocação, navegar em páginas de até
  20 devs × 20 tarefas e clicar nas células para ver a composição ou bloqueios.
- Acompanhar no gráfico de linhas os pares acumulados por etapa de apresentação.

No modo SciPy, a solução completa é calculada no servidor. A animação apresenta os pares
finais, com pausa, avanço e repetição; ela **não reproduz operações internas**
do solver. O gráfico de linhas usa etapas visuais, não tempos internos que a
biblioteca não fornece. No modo BFS, a animação reproduz os passos reais
de busca, avaliação e reorganização dos pares. O tempo real de preparação, leitura do banco e chamada
a cada algoritmo é medido separadamente; pausas não alteram essas medições.
Nenhum responsável histórico no MySQL é alterado. A execução web não
sobrescreve `resultados/alocacao.json`; use o botão de download para guardar
seu resultado. Esse arquivo local continua sendo gerado pela opção 2 do menu.

Alterar um critério, filtro ou dado manual limpa a reprodução e os gráficos
anteriores. O botão **Salvar critérios** valida os dados antes de gravar;
**Atualizar dados** relê o banco com os filtros da tela. Configurações editadas
externamente em JSON são carregadas ao recarregar a página.

O laboratório aceita até 200 desenvolvedores e 500 tarefas por recorte.
Para conjuntos maiores, selecione um projeto e/ou sprint menor. Os usuários
são identificados pelo ID, pois o dataset não fornece seus nomes.

A porta pode ser alterada por `WEB_PORT` no `.env` (padrão `8000`). O endereço
publicado é `WEB_HOST=127.0.0.1` por padrão, para uso no próprio computador.
Para acesso na sua rede, configure `WEB_HOST=0.0.0.0`, execute a opção 1 e
use `http://IP_DO_COMPUTADOR:PORTA` no outro dispositivo.

### Análise do ambiente

Escolha **5** antes de iniciar. A análise identifica utilitários ausentes,
Docker CLI, plugin Compose com suporte às opções usadas pelo projeto,
serviço Docker parado ou inacessível, arquivos necessários, permissões de
escrita e validade da configuração Compose quando `.env` já existe. Cada
pendência indica o que instalar ou corrigir. Ela não instala pacotes nem
modifica permissões ou cria `.env`.

Também é possível executar somente a análise:

```bash
bash start.sh --analisar
```

O comando retorna código diferente de zero se encontrar pendências. Não
confirma disponibilidade de portas nem conectividade com os registries:
essas condições são verificadas efetivamente ao iniciar/construir os containers.
No macOS, caso algum utilitário esteja ausente, instale GNU
coreutils pelo gerenciador de pacotes utilizado no computador.

### Acesso ao banco

Por padrão, acesse **http://localhost:8081** para abrir o phpMyAdmin.
O botão **Abrir phpMyAdmin** na interface web abre o painel já conectado,
usando `DB_USER` e `DB_PASSWORD` do `.env`. As credenciais são configuradas
no container do phpMyAdmin, sem enviá-las no link ou no HTML da aplicação.
O login automático usa `PMA_USER` e `PMA_PASSWORD`, conforme a
[documentação da imagem oficial](https://github.com/phpmyadmin/docker).
Para voltar ao formulário de login e acessar como `root`, remova essas duas
variáveis do serviço `phpmyadmin` no `compose.yaml` e execute a opção 1
novamente. Então use `root` e `MYSQL_ROOT_PASSWORD`.
O MySQL fica disponível para ferramentas locais em **127.0.0.1:3308**.
Dentro dos containers, o endereço do banco é `db:3306`.
As portas publicadas são acessíveis somente pelo próprio computador.

Se as portas estiverem ocupadas, altere `MYSQL_PORT` ou `PHPMYADMIN_PORT`
no `.env` e execute a opção 1 novamente. Alterações de nome, usuário e senha
em `.env` **não alteram usuários nem senhas de um volume MySQL existente**;
esse provisionamento acontece apenas na primeira inicialização. Para mudar
credenciais existentes, altere-as no MySQL e atualize `.env` em seguida.
O ambiente é destinado a desenvolvimento local.

### Dataset reduzido para começar

Use `datasets/TAWOS_reduzido.sql` para os testes iniciais: ele contém
40 tarefas reais de um projeto, distribuídas em duas sprints (20 por sprint),
com responsável e estimativa em story points. Os usuários referenciados,
o projeto, as sprints e o repositório são preservados com seus IDs originais.
As 13 tabelas mantêm a estrutura original; comentários, histórico de alterações
e tabelas auxiliares de vínculos ficam sem registros nesse recorte.
O recorte não representa a carga completa das sprints originais.

O arquivo completo fica preservado em `datasets/original/TAWOS.sql`.
O menu lista os arquivos `.sql` e `.sql.gz` diretamente em `datasets/`;
subpastas como `original/` ficam fora da lista.
A importação é feita pelo menu, inclusive quando o banco é novo. Escolha
**3 → 1** e selecione o número de `TAWOS_reduzido.sql`.
Para importar pelo caminho, você também pode escolher **I** e informar:

```text
datasets/TAWOS_reduzido.sql
```

A importação substitui as tabelas TAWOS do banco selecionado, após a
confirmação `IMPORTAR`. Ela não apaga outras tabelas que já existirem no banco.

### Dataset ampliado — aproximadamente 5 MB

O arquivo `datasets/TAWOS_ampliado.sql` contém **4.991.859 bytes** de dados
reais extraídos do mesmo TAWOS original:

| Conteúdo | Quantidade |
| --- | ---: |
| Projetos / repositórios | 3 / 3 |
| Sprints | 12 |
| Tarefas com estimativa e responsável | 480 (40 por sprint) |
| Usuários referenciados | 200 |
| Responsáveis históricos distintos por tarefas | 61 |
| Comentários | 1.751 |
| Registros de histórico de alterações | 8.080 |

Os 200 usuários incluem responsáveis, criadores, relatores e autores dos
comentários/histórico preservados. O algoritmo atual trata todos os registros
de `User` como candidatos; não há cargo ou habilidade real nessa tabela.
As sprints são recortes, não sua carga histórica completa.

O contexto de comentários e alterações é real e se refere somente às tarefas
selecionadas. Não foi adicionado preenchimento artificial para atingir o tamanho.
As 13 tabelas mantêm a estrutura do original; as demais tabelas auxiliares
ficam vazias. As referências são verificadas antes de gerar o arquivo.

Para usar, escolha **3 → 1** no menu e selecione pelo número o arquivo
**`datasets/TAWOS_ampliado.sql`**. Ele substitui o recorte atual no banco após confirmação. `TAWOS_reduzido.sql` continua disponível para voltar
aos testes pequenos. Depois de importar, clique em **Atualizar dados** na web.

O recorte cabe nos limites atuais da interface (200 usuários e 480 tarefas).
Para acompanhar a animação com mais clareza, filtre um projeto ou uma sprint;
cada uma das 12 sprints contém 40 tarefas. Os comentários e históricos
servem de contexto e não entram na compatibilidade do matching atual.

### Importar seu SQL / dataset TAWOS

Escolha **3 — Banco de dados**, depois **1 — Importar dataset SQL**,
e selecione o **número do arquivo** listado. A lista inclui os arquivos de
`datasets/`. Para um arquivo SQL externo,
escolha **I — Importar outro arquivo SQL** e informe o caminho. Use 0 ou Enter
para cancelar a seleção. Se não houver arquivos nessa pasta, o menu informa isso e mantém
a opção de importar um arquivo externo. Caminhos relativos são
resolvidos em relação à pasta do projeto; espaços são aceitos, sem envolver
o caminho em aspas. Também pode importar pela aba **Importar** do phpMyAdmin
(limite configurado de 1 GB). Para datasets grandes, prefira o menu, que não
está sujeito ao limite de upload HTTP.

A importação pelo menu executa o SQL como root e pode criar bancos. Se o dump
contiver `CREATE DATABASE` ou `USE` com outro nome, configure `DB_NAME` para
esse banco após a importação e escolha 1 para atualizar o container Python.
O usuário de aplicação recebe acesso inicialmente apenas ao banco configurado;
se o dump criou outro banco, conceda acesso pela aba SQL do phpMyAdmin, conectado como root, ajustando
os nomes abaixo:

```sql
GRANT ALL PRIVILEGES ON `nome_do_banco`.* TO 'alocacao'@'%';
```

O arquivo SQL não é reescrito automaticamente. Dumps de outros bancos, como
PostgreSQL ou SQL Server, precisam ser convertidos para MySQL. Erros de
compatibilidade em dumps antigos aparecem no terminal; uma importação pode
aplicar parte do SQL antes de falhar. Consulte o banco e corrija o arquivo antes de repetir a importação.

Para adicionar outros datasets à lista, coloque os arquivos `.sql` ou
`.sql.gz` diretamente em `datasets/` e abra novamente a seleção de arquivos.
A pasta não é importada automaticamente na inicialização do banco.

### Persistência do banco

Os dados ficam no volume Docker `mysql_data` do projeto Compose
`alocacao-devs`. Encerrar pela opção 4 preserva esse volume. O menu não oferece
exclusão permanente do banco. A importação executa o SQL no banco selecionado,
usando o nome indicado no próprio arquivo quando houver `USE`, e exige digitar
`IMPORTAR` antes de começar.

Arquivos `.sql.gz` são descompactados e verificados em arquivo temporário
antes de executar SQL; reserve espaço para o conteúdo descompactado.

### Executar a alocação e editar os critérios

No menu `bash start.sh`, escolha **2 — Executar alocação**. A aplicação
lê `User` e `Issue`, calcula os pares e grava a proposta em
`resultados/alocacao.json`, substituindo o resultado da execução anterior.
Ela não altera `Issue.Assignee_ID`: esse campo é o responsável histórico do
TAWOS. São considerados todos os registros de `User` selecionados, sem avaliar
cargo, experiência ou o responsável histórico da tarefa.

Cada desenvolvedor recebe no máximo **uma tarefa por execução**, e cada tarefa
recebe no máximo um desenvolvedor. Com o dataset reduzido padrão, são **10
alocações** e **30 tarefas sem desenvolvedor**. Mesmo que existam duas sprints,
o limite é aplicado ao conjunto inteiro dessa execução. Para executar somente
uma sprint, configure `sprint_id` como `63` (Sprint 4) ou `62` (Sprint 5).
Executar novamente recalcula a proposta; não acumula alocações anteriores.

Edite `config/critérios.json` para alterar o comportamento, sem reconstruir os
containers. `null` deixa um filtro/limite desativado; `false` desativa um critério.

| Variável | Comportamento quando configurada |
| --- | --- |
| `algoritmo` | `scipy` (padrão) otimiza pares e pontuação; `bfs` usa o matching anterior por caminhos aumentantes |
| `direcao` | Escolhe o grupo à esquerda do grafo; no BFS define as origens da busca e no SciPy orienta a matriz do cálculo |
| `semente_embaralhamento` | `null` usa ordem por ID; um inteiro de 0 a 4294967295 reproduz uma ordem embaralhada |
| `quantidade_devs` | Seleciona até N desenvolvedores; `null` usa todos os disponíveis no filtro |
| `quantidade_tarefas` | Seleciona até N tarefas; `null` usa todas as disponíveis no filtro |
| `projeto_id` | Seleciona usuários e tarefas de um projeto |
| `sprint_id` | Seleciona tarefas de uma sprint |
| `criterios.mesmo_projeto` | Só permite pares do mesmo projeto |
| `criterios.max_story_points_por_tarefa` | Exclui tarefas acima desse limite ou sem estimativa; não é capacidade acumulada por sprint |
| `criterios.habilidades` | Exige que o dev tenha todas as habilidades da tarefa |
| `criterios.disponibilidade` | Só permite devs marcados como disponíveis |
| `pesos.mesmo_projeto` | De 0 a 100; preferência por pares do mesmo projeto |
| `pesos.disponibilidade` | De 0 a 100; preferência por devs disponíveis |
| `pesos.habilidades` | De 0 a 100; preferência pela proporção de requisitos atendidos |

Os campos **Quantidade de devs** e **Quantidade de tarefas** definem o recorte
participante. Ao editá-los, a interface atualiza os números, tabelas e grafo,
e limpa a execução anterior. Deixe em branco para incluir todos os registros
permitidos pelos filtros; em JSON, use `null`. São aceitos inteiros positivos.
A seleção usa os primeiros IDs em ordem crescente, depois dos filtros de
projeto/sprint e antes dos critérios de compatibilidade. Se houver menos
registros do que o solicitado, são usados os disponíveis; não há reposição
automática de candidatos excluídos pelos critérios.

Por exemplo, 5 devs e 20 tarefas permitem **até 5 pares** na regra um para um;
as outras tarefas do recorte ficam sem dev. O limite de participantes não é
uma garantia de alocações quando os critérios impedem alguns pares. Esses
campos também são respeitados na execução pelo menu 2 e na saída JSON.

O botão **Embaralhar ordem** cria uma nova ordem para os dois grupos, atualiza
o grafo e as tabelas e limpa a execução anterior. Os participantes escolhidos
pelos filtros e quantidades continuam os mesmos. A ordem é usada nas linhas
e colunas entregues ao SciPy e na ordem da busca e dos vizinhos no BFS.
Os dois preservam a quantidade máxima de pares. No SciPy, a pontuação ótima
também é preservada; no BFS, a pontuação pode variar conforme a ordem.

Use **Restaurar ordem por ID** para desfazer. **Salvar critérios** guarda a
semente de embaralhamento no mesmo JSON de configuração; a opção 2 do menu
também a respeita. O resultado registra a semente e as listas `ordem_devs`
e `ordem_tarefas` para identificar a ordem utilizada. O banco não é alterado.

Na interface, o campo **Sentido da alocação** muda o grupo das linhas do
cálculo e coloca esse grupo à esquerda do grafo. A matriz visual mantém devs
nas linhas e tarefas nas colunas para facilitar a comparação. As mensagens, os pares exibidos
e o JSON registram o sentido escolhido. A escolha também pode ser salva em
`config/critérios.json` na variável `direcao`.

Em ambos os sentidos, cada dev recebe no máximo uma tarefa e cada tarefa
recebe no máximo um dev. A direção não habilita várias tarefas por dev ou
vários devs por tarefa. Com os mesmos dados e critérios, a quantidade máxima
de pares é a mesma. No SciPy, a pontuação ótima também é a mesma; no BFS,
a direção pode mudar os pares e sua pontuação.

As restrições estão inicialmente desativadas e os pesos começam em zero.
Sem pesos, todos os pares permitidos têm nota zero e o objetivo é maximizar
apenas a quantidade de alocações. Os mesmos dados, critérios e semente
reproduzem a ordem e o resultado na mesma versão do ambiente.

Com pesos, a nota de um par permitido é:

```text
nota do par = 100 × soma(peso × atendimento) / soma dos pesos informados para o par
```

Mesmo projeto e disponibilidade têm atendimento 0 ou 1. Habilidades usam a
fração das habilidades exigidas presentes no dev, sem distinguir maiúsculas
e minúsculas; tarefa explicitamente sem requisitos tem atendimento 1.
Peso zero não exige dados manuais. Restrições bloqueiam pares mesmo que
recebessem nota alta; pesos expressam preferências sem bloquear. As notas
ficam entre 0 e 100 e o resultado exporta `matriz`, `pesos`, `pontuacao_total`
e a pontuação de cada alocação. Uma célula bloqueada contém `null`; zero é
uma nota válida. Para preferir habilidades parcialmente atendidas, use o peso
e mantenha a restrição de habilidades desativada.

O peso de habilidades aceita classificações parciais. Quando falta a lista do
dev ou da tarefa, o par continua permitido e o componente de habilidades fica
fora da nota daquele par; os outros pesos são renormalizados. A matriz mostra
esses pares com contorno tracejado e exibe a nota calculada com os pesos
disponíveis (zero quando nenhum outro critério pode pontuar). A restrição
obrigatória de habilidades ainda exige classificação completa e bloqueia pares
que não atendem aos requisitos.

Na interface, as habilidades são selecionadas em menus de áreas de atuação,
com opções como Teste, Frontend, Backend, FullStack, DevOps, Mobile, UX/UI,
Dados, Segurança e Infraestrutura. O catálogo fica em `config/areas.json`.
Cada dev e tarefa pode ter várias áreas; selecione uma por vez e remova pelo
**×**. Categorias são comparadas pelo nome, sem diferenciar maiúsculas e
minúsculas; FullStack é uma categoria própria e não inclui automaticamente
Frontend e Backend. Para exigir as duas áreas, selecione ambas.

**Sem requisitos** na tarefa ou **Nenhuma habilidade declarada** no dev grava
uma lista vazia; **Não informado** remove a declaração. Na restrição obrigatória
isso exige preenchimento; no peso, o componente é ignorado para os pares com
dados incompletos. Valores salvos anteriormente continuam
visíveis e podem ser removidos, mesmo se não fizerem parte do catálogo.
**Salvar critérios** grava as seleções no mesmo JSON usado pelos dois algoritmos.

Como o TAWOS não informa habilidades nem disponibilidade, ao ativar restrições
obrigatórias preencha os dados manuais exigidos. O peso de habilidades aceita
listas incompletas; disponibilidade continua exigindo que os devs selecionados
tenham sido classificados.
Em `dados_devs`, as chaves são IDs de usuários como texto; por exemplo,
`"123": {"disponivel": true, "habilidades": ["python", "sql"]}`. Em
`habilidades_tarefas`, use IDs de tarefas como texto e listas de habilidades,
por exemplo `"456": ["python"]`. Os IDs acima são ilustrativos; use os IDs reais
do banco. Uma lista vazia declara explicitamente que não há habilidades
informadas/exigidas. A aplicação acusa configuração incompleta ao ativar um
critério sem os dados necessários, em vez de inventar essas informações.

Execute a alocação pela linha de comando dentro do container:

```bash
docker compose exec app python app/main.py -d 5 -t 10
```

Parâmetros disponíveis:

| Parâmetro | O que faz |
| --- | --- |
| `-d N`, `--devs N` | Limita a quantidade de desenvolvedores participantes a, no máximo, N. |
| `-t N`, `--tarefas N` | Limita a quantidade de tarefas participantes a, no máximo, N. |
| `-s N`, `--sprints N` | Seleciona até N sprints no total, em ordem crescente de ID. |
| `-p N`, `--projetos N` | Seleciona até N projetos, em ordem crescente de ID. |
| `-h`, `--help` | Mostra a ajuda e encerra sem executar a alocação. |

Exemplo com todos os parâmetros:

```bash
docker compose exec app python app/main.py -d 30 -t 50 -s 2 -p 3
```

As quantidades aceitam inteiros positivos e representam limites máximos. Se o
banco tiver menos registros, serão usados apenas os disponíveis. Os argumentos
informados substituem os valores correspondentes do JSON somente nessa execução;
parâmetros omitidos continuam usando o JSON, que não é alterado. Para ver a
ajuda, execute `docker compose exec app python app/main.py --help`. Ao terminar,
a saída informa o tempo total da execução, incluindo leitura do banco,
alocação e gravação do arquivo JSON.

Projetos são selecionados por ID crescente; depois, sprints dos projetos
selecionados, também por ID crescente. `-s` é o total de sprints do recorte,
não a quantidade por projeto. Esses filtros são aplicados antes dos limites
de devs e tarefas. O filtro de sprint afeta as tarefas; devs pertencem aos
projetos selecionados. Os filtros `projeto_id` e `sprint_id` do JSON continuam
valendo: `-p 3` significa até três projetos, e não o projeto de ID 3.
Se houver menos registros disponíveis, são usados apenas os existentes.
O matching continua limitado a uma tarefa por dev no conjunto da execução.

Existem dois algoritmos selecionáveis em `algoritmo`, compartilhando seleção de
participantes, restrições e cálculo das notas:

- **`scipy`**: [`scipy.optimize.linear_sum_assignment`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html),
  com `maximize=True`, uma variante de Jonker–Volgenant. Maximiza primeiro a
  quantidade de pares válidos e depois sua pontuação total. A utilidade interna
  de um par válido é `min(devs, tarefas) + 1 + nota / 100`; o bônus preserva a
  prioridade da quantidade de pares. Colunas fictícias de utilidade zero permitem
  participantes sem alocação, e pares proibidos têm utilidade negativa infinita.
  A animação apresenta a solução final, com `tipo_passos: apresentacao_da_solucao`.
- **`bfs`**: o algoritmo anterior, com busca em largura por caminhos aumentantes.
  Maximiza a quantidade de pares respeitando as restrições, sem usar pesos para
  orientar as escolhas. A pontuação é calculada para avaliar a solução. Os passos
  são registrados durante a busca (`tipo_passos: execucao_real`), com timestamps
  reais. A estrutura do grafo usa dicionários Python, sem dependência do NetworkX.

**Comparar os dois** faz uma única leitura do banco e fornece o mesmo recorte,
ordem, sentido, restrições e pesos aos métodos. Cada um executa uma vez, sem
registro de passos e sem animação; a tabela separa tempo do cálculo e tempo
com preparação. São medições pontuais, sujeitas à carga do ambiente, não um
benchmark estatístico. O tempo da execução visual do BFS inclui o registro de
passos e não deve ser confundido com o tempo sem registro da comparação.

O comparativo também mostra pares em comum e a diferença de pontuação.
Ambos devem produzir a mesma quantidade máxima; o SciPy busca a melhor
pontuação entre soluções dessa quantidade. Sem pesos, todas as notas são
zero, embora possam existir pares diferentes igualmente válidos. O aviso na
matriz orienta a definir pesos maiores que zero para gerar notas. Habilidades
e disponibilidade precisam ser declaradas manualmente quando seus pesos
estiverem ativos. Restrições obrigatórias, sozinhas, não acrescentam pontos.

A mesma função atende à linha de comando e à web. **Salvar critérios** guarda
o algoritmo escolhido em `config/critérios.json`, também usado pelo menu 2.
O JSON de resultado identifica `codigo_algoritmo`, `algoritmo` e `objetivo`.
O botão de download da comparação exporta os dois resultados e a configuração.

### Desenvolvimento local

A pasta do projeto é montada em `/workspace` no container Python. Mudanças em
`app/` e `web/` ficam disponíveis no volume; alterações nas dependências
em `requirements.txt` exigem reconstruir pela opção 1. Alterações no Python
da API ou nos templates HTML exigem reiniciar o serviço
(`docker compose restart web`); alterações em CSS/JS aparecem ao atualizar
a página.
Use `app/db.py` para obter uma conexão configurada pelas variáveis de ambiente.
A opção 2 executa a alocação em `app/main.py` e salva a proposta em JSON,
sem alterar as tabelas do dataset.
Para executar manualmente outros comandos de desenvolvimento, use:

```bash
docker compose exec app python -m app.main
docker compose exec app sh
```

Testes podem ser criados localmente em `tests/`, mas essa pasta é ignorada
pelo Git e pelo build Docker. A aplicação não depende dela para construir
as imagens, iniciar o ambiente ou executar o algoritmo. Nenhum pacote de
testes é instalado nas dependências da aplicação.

Se aparecer erro de acesso ao Docker, confirme que o serviço está iniciado e
que seu usuário tem permissão para acessá-lo. Em Linux, após uma alteração
administrativa nos grupos do usuário pode ser necessário iniciar uma nova
sessão. O menu não modifica permissões do sistema nem executa `sudo`.

Referências da configuração: [ordem de inicialização no Compose](https://docs.docker.com/compose/how-tos/startup-order/)
e [imagem oficial do phpMyAdmin](https://hub.docker.com/_/phpmyadmin).
