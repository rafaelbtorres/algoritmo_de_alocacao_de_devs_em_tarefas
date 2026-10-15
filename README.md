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
NumPy, pandas, SciPy, NetworkX, Flask e Gunicorn. O algoritmo em `app/matching.py` associa desenvolvedores a tarefas por matching
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

- Escolher o sentido: desenvolvedores → tarefas ou tarefas → desenvolvedores.
- Selecionar projeto/sprint, limitar quantos devs e tarefas participam e explorar
  o recorte do banco antes de executar.
- Embaralhar a ordem inicial dos participantes ou restaurar a ordem por ID.
- Ativar critérios, definir o limite de story points e preencher habilidades
  e disponibilidade nas tabelas. Esses dados manuais complementam a simulação.
- Salvar os critérios no mesmo `config/critérios.json` usado pela linha de comando.
- Iniciar, pausar, continuar, avançar um passo, reiniciar a reprodução e ajustar
  sua velocidade. A cada alocação, o grafo mostra os pares atuais.
- Ver a distribuição de tarefas alocadas/sem dev, tempos de leitura do banco,
  preparação do grafo e matching, além de baixar o resultado em JSON.
- Acompanhar no gráfico de linhas a quantidade acumulada de alocações em
  função do tempo real da busca, com um marcador por novo par formado.

A execução é calculada no servidor e registra as buscas, arestas avaliadas
e caminhos aumentantes realmente usados. A página reproduz esse registro:
pausar não mantém uma consulta SQL aberta nem muda o resultado calculado.
O tempo de reprodução (incluindo pausas) é exibido separadamente dos tempos
reais de processamento. O tempo de matching inclui o registro dos passos.
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
| `direcao` | `devs_para_tarefas` inicia a busca pelos devs; `tarefas_para_devs` inicia pelas tarefas |
| `semente_embaralhamento` | `null` usa ordem por ID; um inteiro de 0 a 4294967295 reproduz uma ordem embaralhada |
| `quantidade_devs` | Seleciona até N desenvolvedores; `null` usa todos os disponíveis no filtro |
| `quantidade_tarefas` | Seleciona até N tarefas; `null` usa todas as disponíveis no filtro |
| `projeto_id` | Seleciona usuários e tarefas de um projeto |
| `sprint_id` | Seleciona tarefas de uma sprint |
| `criterios.mesmo_projeto` | Só permite pares do mesmo projeto |
| `criterios.max_story_points_por_tarefa` | Exclui tarefas acima desse limite ou sem estimativa; não é capacidade acumulada por sprint |
| `criterios.habilidades` | Exige que o dev tenha todas as habilidades da tarefa |
| `criterios.disponibilidade` | Só permite devs marcados como disponíveis |

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
pelos filtros e quantidades continuam os mesmos. A busca realmente usa essa
ordem, inclusive ao avaliar os vizinhos de cada nó; não se trata apenas de
uma mudança visual. Os pares e os passos podem mudar quando há empates,
mas a cardinalidade máxima continua a mesma para o mesmo grafo.

Use **Restaurar ordem por ID** para desfazer. **Salvar critérios** guarda a
semente de embaralhamento no mesmo JSON de configuração; a opção 2 do menu
também a respeita. O resultado registra a semente e as listas `ordem_devs`
e `ordem_tarefas` para identificar a ordem utilizada. O banco não é alterado.

Na interface, o campo **Sentido da alocação** muda o grupo que inicia a
busca e coloca esse grupo à esquerda do grafo. As mensagens, os pares exibidos
e o JSON registram o sentido escolhido. A escolha também pode ser salva em
`config/critérios.json` na variável `direcao`.

Em ambos os sentidos, cada dev recebe no máximo uma tarefa e cada tarefa
recebe no máximo um dev. A direção não habilita várias tarefas por dev ou
vários devs por tarefa. Com os mesmos dados e critérios, a quantidade máxima
de pares é a mesma; a ordem da busca, os passos e os pares escolhidos em caso
de empate podem mudar.

Todos os critérios estão inicialmente desativados. Não há pesos ou preferência
entre pares: o algoritmo busca a maior quantidade de pares válidos. A busca
percorre os grupos na ordem exibida no grafo: por ID, ou embaralhada quando
essa opção estiver ativa. Os mesmos dados, critérios e semente reproduzem a
mesma ordem e o mesmo resultado no ambiente atual.

Como o TAWOS não informa habilidades nem disponibilidade, ao ativar esses
critérios preencha os dados manualmente para todos os devs/tarefas selecionados.
Em `dados_devs`, as chaves são IDs de usuários como texto; por exemplo,
`"123": {"disponivel": true, "habilidades": ["python", "sql"]}`. Em
`habilidades_tarefas`, use IDs de tarefas como texto e listas de habilidades,
por exemplo `"456": ["python"]`. Os IDs acima são ilustrativos; use os IDs reais
do banco. Uma lista vazia declara explicitamente que não há habilidades
informadas/exigidas. A aplicação acusa configuração incompleta ao ativar um
critério sem os dados necessários, em vez de inventar essas informações.

Também é possível executar diretamente:

```bash
docker compose exec app python -m app.main
```

A implementação constrói um grafo bipartido com NetworkX e usa busca em
largura por caminhos aumentantes para obter o matching de cardinalidade
máxima. A mesma função atende a linha de comando e a interface, usando a
representação de grafo do [NetworkX](https://networkx.org/documentation/stable/reference/algorithms/bipartite.html).

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
