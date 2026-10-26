'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {config: {}, catalog: {}, devs: [], tasks: [], tab: 'tasks', result: null, runConfig: null, index: 0, pairs: [], active: null, playing: false, timer: null, busy: false, loadId: 0, started: 0, timelineEvents: [], matrix: null, matrixConfig: null, matrixPage: 0, selectedCell: null, detailsId: 0, comparison: null};
const labels = {matriz:'MATRIZ DE PONTUAÇÕES', resolver:'SOLUÇÃO GLOBAL CALCULADA', buscar:'BUSCA POR UM PAR', avaliar:'AVALIANDO UMA CONEXÃO', ocupada:'BUSCANDO CAMINHO ALTERNATIVO', sem_par:'SEM PAR DISPONÍVEL', alocar:'PAR DA SOLUÇÃO', concluir:'APRESENTAÇÃO CONCLUÍDA'};
const number = value => Number(value).toLocaleString('pt-BR', {maximumFractionDigits: 3});
const algorithms = {
  bfs: {name:'BFS', label:'BFS · CAMINHOS AUMENTANTES', realSteps:true,
    hint:'Algoritmo anterior: maximiza pares; os pesos servem apenas para avaliar a solução.',
    initial:'Inicie para acompanhar as buscas e os caminhos aumentantes reais do BFS.'},
  scipy: {name:'SciPy', label:'SCIPY · SOLUÇÃO GLOBAL', realSteps:false,
    hint:'Boa escolha geral, especialmente quando muitos pares são permitidos. Maximiza pares e depois a pontuação total.',
    initial:'Inicie o cálculo para apresentar a solução encontrada pelo SciPy.'},
  ssp: {name:'SSP', label:'SSP · GULOSO POR CAMINHOS', realSteps:true,
    hint:'Escolhe o caminho de menor custo e pode refazer pares anteriores. Use para acompanhar decisões reais com a mesma quantidade e pontuação ótimas do SciPy.',
    initial:'Inicie para acompanhar os caminhos de menor custo e as reatribuições reais do SSP.'},
  kwok: {name:'Kwok', label:'KWOK · ATRIBUIÇÃO PONDERADA', realSteps:false,
    hint:'Algoritmo de 2025 para matching ponderado com pares bloqueados e grupos de tamanhos diferentes. Preserva a quantidade e pontuação ótimas do SciPy; compare os tempos no seu cenário.',
    initial:'Inicie o cálculo para apresentar a solução encontrada pelo Kwok.'}
};
const algorithmInfo = (code = $('algorithm').value) => algorithms[code];

function message(text, error = false) { $('message').textContent = text; $('message').className = error ? 'error' : ''; $('message').hidden = !text; }
async function api(path, options = {}) {
  const response = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const body = await response.json();
  if (!response.ok) throw new Error(body.erro || 'Não foi possível concluir a operação.');
  return body;
}
function getConfig() {
  return {...state.config, algoritmo:$('algorithm').value, quantidade_devs: $('dev-limit').value === '' ? null : Number($('dev-limit').value), quantidade_tarefas: $('task-limit').value === '' ? null : Number($('task-limit').value), direcao: $('direction').value, projeto_id: $('project').value ? Number($('project').value) : null, sprint_id: $('sprint').value ? Number($('sprint').value) : null,
    criterios:{mesmo_projeto:$('same-project').checked, disponibilidade:$('availability').checked, habilidades:$('skills').checked, max_story_points_por_tarefa:$('points').value === '' ? null : Number($('points').value)},
    pesos:{mesmo_projeto:Number($('weight-project').value), disponibilidade:Number($('weight-availability').value), habilidades:Number($('weight-skills').value)},
    dados_devs:state.config.dados_devs || {}, habilidades_tarefas:state.config.habilidades_tarefas || {}};
}
function populateSprints(selected = '') {
  const project = $('project').value;
  $('sprint').innerHTML = '<option value="">Todas as sprints</option>' + state.catalog.sprints.filter(s => !project || String(s.Project_ID) === project).map(s => `<option value="${s.ID}">${escapeHTML(s.Name)} · #${s.ID}</option>`).join('');
  $('sprint').value = selected === null ? '' : String(selected);
}
function setBusy(busy) {
  state.busy = busy;
  document.querySelectorAll('.config-panel input,.config-panel select,#data-table input,#data-table select,#data-table button,#save-config,#save-data-config,#reload,#fill-manual,#shuffle-order,#restore-order,#preview-matrix,#compare').forEach(el => el.disabled = busy);
  $('fill-manual').disabled = busy || !(state.tab === 'tasks' ? state.tasks.length : state.devs.length);
  updateControls();
}
function updateControls() {
  $('compare').disabled = state.busy || !state.devs.length || !state.tasks.length;
  $('preview-matrix').disabled = state.busy || !state.devs.length || !state.tasks.length;
  $('shuffle-order').disabled = state.busy || (state.devs.length < 2 && state.tasks.length < 2);
  $('restore-order').disabled = state.busy || state.config.semente_embaralhamento == null;
  $('order-status').textContent = state.config.semente_embaralhamento == null ? 'Ordem por ID' : 'Ordem embaralhada';
  $('start').disabled = state.busy || !state.devs.length || !state.tasks.length;
  $('start').textContent = state.busy ? 'Carregando…' : state.playing ? 'Ⅱ Pausar' : state.result ? (state.index >= state.result.passos.length ? '↺ Reproduzir novamente' : '▶ Continuar') : '▶ Iniciar alocação';
  $('next').disabled = state.busy || !state.result || state.index >= state.result.passos.length;
  $('reset').disabled = state.busy || !state.result;
}
function pause() { clearTimeout(state.timer); state.timer = null; state.playing = false; if (state.result && state.index < state.result.passos.length) $('run-status').textContent = 'Pausado'; updateControls(); }
function clearRun(keepComparison = false) {
  $('data-save-message').hidden = true;
  if (!keepComparison) { state.comparison = null; renderComparison(); }
  pause(); state.result = null; state.runConfig = null; state.index = 0; state.pairs = []; state.active = null;
  $('results-content').hidden = true; $('results-empty').hidden = false; $('download').disabled = true;
  $('pair-count').textContent = '0'; $('run-status').textContent = 'Pronto para começar'; $('step-label').textContent = 'O PONTO DE PARTIDA';
  state.matrix = null; state.matrixConfig = null; state.matrixPage = 0; state.selectedCell = null; state.detailsId++; renderMatrix();
  $('pair-details').textContent = 'Clique em uma célula para ver a composição da nota ou os motivos do bloqueio.';
  $('step-text').textContent = algorithmInfo().initial; $('progress-count').textContent = '0 / 0'; $('progress-bar').style.width = '0%';
  updateControls();
}
function updateCriteriaCount() {
  const c = getConfig().criterios;
  const count = Number(c.mesmo_projeto) + Number(c.disponibilidade) + Number(c.habilidades) + Number(c.max_story_points_por_tarefa !== null);
  $('criteria-count').textContent = `${count} ${count === 1 ? 'ativo' : 'ativos'}`;
}
async function loadData() {
  const requestId = ++state.loadId;
  clearRun(); setBusy(true); message('');
  try {
    const data = await api('/api/dados', {method:'POST', body:JSON.stringify(getConfig())});
    if (requestId !== state.loadId) return;
    state.devs = data.devs; state.tasks = data.tarefas;
    $('dev-count').textContent = state.devs.length; $('task-count').textContent = state.tasks.length;
    $('sprint-count').textContent = new Set(state.tasks.map(t => t.Sprint_ID).filter(v => v !== null)).size;
    $('tasks-tab-count').textContent = state.tasks.length; $('devs-tab-count').textContent = state.devs.length;
    $('db-dot').classList.add('online'); $('db-status').textContent = 'Conectado ao MySQL';
    renderGraph(); renderTable();
  } catch (error) {
    if (requestId !== state.loadId) return;
    state.devs = []; state.tasks = [];
    $('dev-count').textContent = '—'; $('task-count').textContent = '—'; $('sprint-count').textContent = '—';
    $('db-dot').classList.remove('online'); $('db-status').textContent = 'Confira o banco de dados';
    message(error.message, true); renderGraph(); renderTable();
  } finally { if (requestId === state.loadId) { setBusy(false); renderGraph(); } }
}

function renderGraph() {
  const svg = $('graph');
  const count = Math.max(state.devs.length, state.tasks.length, 1);
  const height = Math.max(425, count * 30 + 95);
  svg.setAttribute('viewBox', `0 0 760 ${height}`);
  const position = (index, total) => 65 + (total <= 1 ? (height - 105) / 2 : index * (height - 105) / (total - 1));
  const reverse = getConfig().direcao === 'tarefas_para_devs';
  const devX = reverse ? 625 : 135, taskX = reverse ? 135 : 625;
  const devY = new Map(state.devs.map((d, i) => [d.ID, position(i, state.devs.length)]));
  const taskY = new Map(state.tasks.map((t, i) => [t.ID, position(i, state.tasks.length)]));
  const matchedDevs = new Set(state.pairs.map(p => p.dev_id));
  const matchedTasks = new Set(state.pairs.map(p => p.tarefa_id));
  const active = state.active;
  const edge = (devId, taskId, css) => {
    if (!devY.has(devId) || !taskY.has(taskId)) return '';
    const y1 = devY.get(devId), y2 = taskY.get(taskId);
    return `<path class="edge ${css}" d="M ${devX + (reverse ? -12 : 12)} ${y1} C ${reverse ? 470 : 300} ${y1}, ${reverse ? 300 : 470} ${y2}, ${taskX + (reverse ? 12 : -12)} ${y2}"/>`;
  };
  let html = `<text class="graph-column-label" x="135" y="23" text-anchor="middle">${reverse ? 'TAREFAS' : 'DESENVOLVEDORES'}</text><text class="graph-column-label" x="625" y="23" text-anchor="middle">${reverse ? 'DESENVOLVEDORES' : 'TAREFAS'}</text>`;
  if (!state.result && state.devs.length && state.tasks.length) html += `<text class="graph-sub-label" x="380" y="${height / 2}" text-anchor="middle">Os pares da solução aparecem durante a apresentação</text>`;
  html += state.pairs.map(p => edge(p.dev_id, p.tarefa_id, 'matched')).join('');
  if (active?.tarefa_id !== undefined && active?.dev_id !== undefined) html += edge(active.dev_id, active.tarefa_id, 'examining');
  const personIcon = '<circle cx="0" cy="-4" r="3"/><path d="M-6 7V5a6 6 0 0 1 12 0v2"/>';
  const documentIcon = '<path d="M-5-8h7l4 4V8H-5Z"/><path d="M2-8v4h4M-2 0h5M-2 3h5M-2 6h3"/>';
  const nodeIcon = (type, x, y, chosen, focused, label) => `<g class="graph-node ${type}-node ${chosen ? 'chosen' : ''} ${focused ? 'focused' : ''}" transform="translate(${x} ${y})" role="img" aria-label="${escapeHTML(label)}"><title>${escapeHTML(label)}</title><rect class="node-background" x="-12" y="-12" width="24" height="24" rx="${type === 'dev' ? 7 : 4}"/><g class="node-symbol" aria-hidden="true">${type === 'dev' ? personIcon : documentIcon}</g></g>`;
  state.devs.forEach(d => {
    const y = devY.get(d.ID);
    html += nodeIcon('dev', devX, y, matchedDevs.has(d.ID), active?.dev_id === d.ID, `Desenvolvedor ${d.ID}`);
    html += `<text class="node-label" x="${reverse ? devX + 24 : devX - 24}" y="${y + 3}" text-anchor="${reverse ? 'start' : 'end'}">Dev ${d.ID}</text>`;
  });
  state.tasks.forEach(t => {
    const y = taskY.get(t.ID);
    html += nodeIcon('task', taskX, y, matchedTasks.has(t.ID), active?.tarefa_id === t.ID, `Tarefa ${t.Issue_Key || t.ID}`);
    html += `<text class="node-label" x="${reverse ? taskX - 24 : taskX + 24}" y="${y + 3}" text-anchor="${reverse ? 'end' : 'start'}">${escapeHTML(t.Issue_Key || `#${t.ID}`)}</text>`;
  });
  svg.innerHTML = html;
  $('graph-empty').hidden = Boolean(state.devs.length && state.tasks.length);
  $('graph-empty').textContent = state.busy ? 'Carregando os dados do banco…' : 'Sem pares possíveis. Confira os filtros e o dataset.';
}

function skillPicker(kind, id, skills) {
  const selected = skills || [], isTask = kind === 'task-skills';
  const owner = isTask ? `tarefa ${id}` : `dev ${id}`;
  const selectedNames = new Set(selected.map(skill=>skill.trim().toLocaleLowerCase('pt-BR')));
  const options = state.catalog.areas.filter(area=>!selectedNames.has(area.toLocaleLowerCase('pt-BR')));
  const tags = selected.map(skill=>`<span class="skill-tag">${escapeHTML(skill)}<button type="button" data-remove-skill="${escapeHTML(skill)}" data-kind="${kind}" data-id="${id}" aria-label="Remover ${escapeHTML(skill)} da ${isTask ? 'tarefa' : 'seleção do dev'} ${id}" ${state.busy ? 'disabled' : ''}>×</button></span>`).join('');
  return `<div class="skill-picker"><select class="table-input skill-select" data-kind="${kind}" data-id="${id}" aria-label="${isTask ? 'Habilidades exigidas pela tarefa' : 'Habilidades do dev'} ${id}" ${state.busy ? 'disabled' : ''}><option value="" selected disabled>Adicionar área…</option>${options.map(area=>`<option value="${escapeHTML(area)}">${escapeHTML(area)}</option>`).join('')}<optgroup label="Limpar seleção"><option value="__none__">${isTask ? 'Sem requisitos' : 'Nenhuma habilidade declarada'}</option><option value="__unset__">Não informado</option></optgroup></select><div class="skill-tags" aria-label="Áreas selecionadas para ${owner}">${tags || `<span class="skill-empty">${skills === undefined ? 'Não informado' : isTask ? 'Sem requisitos' : 'Nenhuma declarada'}</span>`}</div></div>`;
}
function setSkills(kind, id, skills) {
  state.config.dados_devs ||= {}; state.config.habilidades_tarefas ||= {};
  if (kind === 'task-skills') {
    if (skills === undefined) delete state.config.habilidades_tarefas[id];
    else state.config.habilidades_tarefas[id] = skills;
  } else {
    state.config.dados_devs[id] ||= {};
    if (skills === undefined) delete state.config.dados_devs[id].habilidades;
    else state.config.dados_devs[id].habilidades = skills;
  }
}
function refreshManualData(kind, id) {
  clearRun(); renderGraph(); renderTable();
  const control = Array.from($('data-table').querySelectorAll('select')).find(el=>el.dataset.kind === kind && el.dataset.id === id);
  control?.focus({preventScroll:true});
}

function renderTable() {
  const isTasks = state.tab === 'tasks';
  $('tasks-tab').classList.toggle('active', isTasks); $('devs-tab').classList.toggle('active', !isTasks);
  $('tasks-tab').setAttribute('aria-selected', isTasks); $('devs-tab').setAttribute('aria-selected', !isTasks);
  $('fill-manual').textContent = isTasks ? 'Declarar tarefas sem requisitos' : 'Marcar devs disponíveis';
  const search = $('search').value.trim().toLocaleLowerCase('pt-BR');
  const records = (isTasks ? state.tasks : state.devs).filter(row => JSON.stringify(row).toLocaleLowerCase('pt-BR').includes(search));
  const headers = isTasks ? ['Tarefa', 'Título', 'Sprint', 'Story points', 'Dev histórico', 'Alocação', 'Áreas exigidas'] : ['Desenvolvedor', 'Projeto', 'Disponibilidade manual', 'Áreas de atuação', 'Tarefa alocada'];
  $('data-table').querySelector('thead').innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
  $('data-table').querySelector('tbody').innerHTML = records.map(row => {
    if (isTasks) {
      const pair = state.pairs.find(p => p.tarefa_id === row.ID);
      const skills = state.config.habilidades_tarefas?.[String(row.ID)];
      return `<tr><td><span class="task-code">${escapeHTML(row.Issue_Key || row.ID)}</span></td><td class="title-cell">${escapeHTML(row.Title)}</td><td><span class="table-tag">#${escapeHTML(row.Sprint_ID ?? '—')}</span></td><td>${escapeHTML(row.Story_Point ?? '—')}</td><td>${escapeHTML(row.Assignee_ID ?? '—')}</td><td><span class="table-tag ${pair ? 'matched' : ''}">${pair ? `Dev ${pair.dev_id}` : 'Sem alocação'}</span></td><td>${skillPicker('task-skills', row.ID, skills)}</td></tr>`;
    }
    const data = state.config.dados_devs?.[String(row.ID)] || {};
    const pair = state.pairs.find(p => p.dev_id === row.ID);
    return `<tr><td class="title-cell">Dev ${row.ID}</td><td>#${escapeHTML(row.Project_ID ?? '—')}</td><td><select class="table-input" data-kind="availability" data-id="${row.ID}" aria-label="Disponibilidade do dev ${row.ID}"><option value="">Não informado</option><option value="true" ${data.disponivel === true ? 'selected' : ''}>Disponível</option><option value="false" ${data.disponivel === false ? 'selected' : ''}>Indisponível</option></select></td><td>${skillPicker('dev-skills', row.ID, data.habilidades)}</td><td>${pair ? `Tarefa #${pair.tarefa_id}` : '—'}</td></tr>`;
  }).join('') || `<tr><td colspan="${headers.length}" style="text-align:center;padding:28px">Nenhum registro encontrado.</td></tr>`;
  $('table-count').textContent = `${records.length} de ${isTasks ? state.tasks.length : state.devs.length} registros`;
  $('fill-manual').disabled = state.busy || !(isTasks ? state.tasks.length : state.devs.length);
}
function applyStep() {
  if (!state.result || state.index >= state.result.passos.length) return;
  const event = state.result.passos[state.index++];
  state.active = event.tarefa_id !== undefined || event.dev_id !== undefined ? event : null;
  if (event.tipo === 'alocar') {
    state.pairs = event.pares; state.active = null;
    state.timelineEvents.push({elapsed_ms: performance.now() - state.started, pairs: state.pairs.length});
  }
  $('pair-count').textContent = state.pairs.length;
  $('step-label').textContent = labels[event.tipo] || 'PASSO DO ALGORITMO'; $('step-text').textContent = event.mensagem;
  $('progress-count').textContent = `${state.index} / ${state.result.passos.length}`;
  $('progress-bar').style.width = `${100 * state.index / state.result.passos.length}%`;
  $('run-status').textContent = event.tipo === 'alocar' ? `${state.pairs.length} pares formados` : state.playing ? 'Em execução' : 'Pausado';
  if (event.tipo === 'alocar') {
    const pair = event.caminho?.at(-1) || event;
    const i = state.matrix.dev_ids.indexOf(pair.dev_id), j = state.matrix.tarefa_ids.indexOf(pair.tarefa_id);
    if (i >= 0 && j >= 0) state.matrixPage = Math.floor(i / 20) * Math.ceil(state.tasks.length / 20) + Math.floor(j / 20);
  }
  renderGraph(); renderTable(); renderMatrix();
  if (state.index === state.result.passos.length) finish();
  updateControls();
}
function tick() {
  if (!state.playing) return;
  applyStep();
  if (state.playing) state.timer = setTimeout(tick, Number($('speed').value));
}
function play() { state.playing = true; $('run-status').textContent = 'Em execução'; updateControls(); tick(); }
function rewind() {
  pause(); state.index = 0; state.pairs = []; state.active = null; state.started = performance.now(); state.timelineEvents = [];
  $('results-content').hidden = true; $('results-empty').hidden = false; $('download').disabled = true; $('pair-count').textContent = '0';
  $('progress-count').textContent = `0 / ${state.result.passos.length}`; $('progress-bar').style.width = '0%'; $('run-status').textContent = 'Pausado';
  $('step-label').textContent = 'PRONTO PARA REPRODUZIR'; $('step-text').textContent = 'Use Continuar ou avance um passo de cada vez.';
  renderGraph(); renderTable(); renderMatrix(); updateControls();
}
async function startRun() {
  if (state.playing) { pause(); $('run-status').textContent = 'Pausado'; return; }
  if (state.result) { if (state.index >= state.result.passos.length) rewind(); play(); return; }
  const config = getConfig(); setBusy(true); message('');
  try {
    const data = await api('/api/alocar', {method:'POST', body:JSON.stringify(config)});
    state.result = data.resultado; state.runConfig = data.config; state.devs = data.devs; state.tasks = data.tarefas; state.started = performance.now(); state.timelineEvents = [];
    state.index = 0; state.pairs = []; state.active = null;
    state.matrix = data.resultado.matriz; state.matrixConfig = structuredClone(data.config); state.matrixPage = 0; renderMatrix();
    setBusy(false); play();
  } catch (error) { message(error.message, true); setBusy(false); }
}
function renderAllocationTimeline(result) {
  const width = 840, height = 275, left = 65, right = 25, top = 25, bottom = 55;
  const count = result.alocacoes.length;
  const timeline = result.apresentacao_tempo || {eventos: [], duracao_ms: 0};
  const durationMs = Math.max(timeline.duracao_ms, ...timeline.eventos.map(event => event.elapsed_ms), 1);
  const x = value => left + (width - left - right) * value / durationMs;
  const y = value => top + (height - top - bottom) * (1 - value / Math.max(count, 1));
  let pairs = 0, path = `M ${x(0)} ${y(0)}`, markers = '', axes = '';
  timeline.eventos.forEach(event => {
    pairs = event.pairs;
    const time = Math.min(event.elapsed_ms, durationMs);
    path += ` L ${x(time)} ${y(pairs)}`;
    markers += `<circle class="timeline-point" cx="${x(time)}" cy="${y(pairs)}" r="4" tabindex="0" role="img" aria-label="${pairs} pares após ${number(event.elapsed_ms / 1000)} segundos"><title>${number(event.elapsed_ms / 1000)} s: ${pairs} pares</title></circle>`;
  });
  path += ` H ${x(durationMs)}`;
  const ticks = new Set([0,count]);
  for (let i = Math.max(1,Math.ceil(count / 5)); i < count; i += Math.max(1,Math.ceil(count / 5))) ticks.add(i);
  for (const tick of ticks) axes += `<line class="timeline-grid" x1="${x(0)}" y1="${y(tick)}" x2="${x(durationMs)}" y2="${y(tick)}"/><text class="timeline-tick" x="${left - 12}" y="${y(tick) + 4}" text-anchor="end">${tick}</text>`;
  for (let i = 0; i <= 5; i++) {
    const tick = durationMs * i / 5;
    axes += `<text class="timeline-tick" x="${x(tick)}" y="${height-bottom+21}" text-anchor="middle">${number(tick/1000)} s</text>`;
  }
  $('allocation-timeline').innerHTML = `<div class="timeline-scroll"><svg class="timeline-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Pares acumulados ao longo do tempo decorrido da apresentação"><title>Evolução da apresentação da solução</title>${axes}<path class="timeline-line" d="${path}"/>${markers}<text class="timeline-axis-label" x="${width/2}" y="${height-8}" text-anchor="middle">Tempo decorrido na apresentação</text><text class="timeline-axis-label" transform="translate(17 ${height/2}) rotate(-90)" text-anchor="middle">Pares apresentados</text></svg></div><div class="timeline-summary">Apresentação: ${number(durationMs/1000)} s, incluindo pausas. O tempo de cálculo do ${algorithmInfo(result.codigo_algoritmo).name} (${number(result.metricas.matching_ms)} ms) é medido separadamente.</div>`;
}

function finish() {
  pause(); state.active = null; state.pairs = state.result.alocacoes;
  state.result.apresentacao_tempo = {eventos: state.timelineEvents, duracao_ms: performance.now() - state.started};
  $('run-status').textContent = 'Concluído'; $('download').disabled = false;
  $('results-empty').hidden = true; $('results-content').hidden = false;
  const r = state.result, m = r.metricas, count = r.alocacoes.length;
  $('result-pairs').textContent = count; $('result-unmatched').textContent = r.tarefas_sem_dev.length;
  $('result-time').textContent = `${number(m.matching_ms)} ms`; $('result-edges').textContent = number(r.pontuacao_total);
  const ratio = r.total_tarefas ? count / r.total_tarefas : 0;
  $('distribution-chart').innerHTML = `<div class="donut-wrap"><svg width="132" height="132" viewBox="0 0 132 132" role="img" aria-label="${count} tarefas alocadas e ${r.tarefas_sem_dev.length} sem desenvolvedor"><circle cx="66" cy="66" r="47" fill="none" stroke="#eaf0e0" stroke-width="13"/><circle cx="66" cy="66" r="47" fill="none" stroke="#668b55" stroke-width="13" stroke-dasharray="${ratio * 295.31} 295.31" transform="rotate(-90 66 66)"/><text x="66" y="65" text-anchor="middle" fill="#375332" font-size="24">${number(ratio * 100)}%</text><text x="66" y="82" text-anchor="middle" fill="#95a184" font-size="9">alocadas</text></svg><div class="chart-key"><div><i style="background:#668b55"></i>${count} alocadas</div><div><i style="background:#e0e9d3"></i>${r.tarefas_sem_dev.length} sem dev</div></div></div>`;
  const info = algorithmInfo(r.codigo_algoritmo);
  const times = [['Leitura do banco', m.leitura_ms], ['Preparação da matriz e do solver', m.preparacao_ms], [`Cálculo ${info.name}${info.realSteps && m.registro_passos ? ' e registro' : ''}`, m.matching_ms]];
  const max = Math.max(...times.map(t => t[1]), .001);
  $('time-chart').innerHTML = '<div class="time-bars">' + times.map(([label, value]) => `<div class="time-row"><div><span>${label}</span><span>${number(value)} ms</span></div><div class="bar-track"><div class="bar-fill" style="width:${100 * value / max}%"></div></div></div>`).join('') + '</div>';
  renderAllocationTimeline(r);
  const wallSeconds = (performance.now() - state.started) / 1000;
  const reverse = r.direcao === 'tarefas_para_devs';
  $('results-explanation').textContent = `Sentido: ${reverse ? 'tarefas → desenvolvedores' : 'desenvolvedores → tarefas'}. ${count} pares formados entre ${r.total_devs} devs e ${r.total_tarefas} tarefas. ${r.devs_sem_tarefa.length} devs ficaram sem tarefa. ${m.arestas_validas} de ${m.arestas_possiveis} pares são compatíveis com os critérios. Pontuação total: ${number(r.pontuacao_total)}. ${r.codigo_algoritmo === 'bfs' ? 'BFS maximiza pares; os pesos só avaliam o resultado, sem guiar a busca.' : `${info.name} maximiza pares e depois a pontuação total. Soluções empatadas podem conter pares diferentes.`} Tempo de preparação e cálculo: ${number(m.total_ms)} ms; reprodução visual: ${number(wallSeconds)} s (inclui pausas). O limite é de uma tarefa por dev no conjunto selecionado. As atribuições históricas do banco foram preservadas.`;
  $('allocation-list').innerHTML = r.alocacoes.map(row => `<span class="allocation-chip">${reverse ? escapeHTML(row.tarefa || row.tarefa_id) : `Dev ${row.dev_id}`} <span>→</span> ${reverse ? `Dev ${row.dev_id}` : escapeHTML(row.tarefa || row.tarefa_id)}</span>`).join('');
  renderGraph(); renderTable(); renderMatrix();
}

const criterionNames = {mesmo_projeto:'Mesmo projeto', disponibilidade:'Disponibilidade', habilidades:'Habilidades atendidas'};
function renderMatrix() {
  const matrix = state.matrix;
  const head = $('score-matrix').querySelector('thead'), body = $('score-matrix').querySelector('tbody');
  if (!matrix || !matrix.dev_ids.length || !matrix.tarefa_ids.length) {
    head.innerHTML = ''; body.innerHTML = ''; $('matrix-summary').classList.remove('matrix-alert');
    $('matrix-summary').textContent = matrix ? 'Nenhum par neste recorte.' : 'Calcule as pontuações ou inicie a alocação para visualizar a matriz.';
    $('matrix-page').textContent = '—'; $('matrix-prev').disabled = true; $('matrix-next').disabled = true;
    return;
  }
  const columnPages = Math.ceil(matrix.tarefa_ids.length / 20), totalPages = Math.ceil(matrix.dev_ids.length / 20) * columnPages;
  state.matrixPage = Math.min(state.matrixPage, totalPages - 1);
  const rowStart = Math.floor(state.matrixPage / columnPages) * 20, columnStart = state.matrixPage % columnPages * 20;
  const devs = matrix.dev_ids.slice(rowStart,rowStart + 20), tasks = matrix.tarefa_ids.slice(columnStart,columnStart + 20);
  const pairs = new Set(state.pairs.map(p=>`${p.dev_id}:${p.tarefa_id}`));
  const taskLabels = new Map(state.tasks.map(t=>[t.ID,t.Issue_Key || `#${t.ID}`]));
  head.innerHTML = '<tr><th scope="col">Dev / tarefa</th>' + tasks.map(id=>`<th scope="col">${escapeHTML(taskLabels.get(id))}</th>`).join('') + '</tr>';
  body.innerHTML = devs.map((id,i)=>`<tr><th scope="row">Dev ${id}</th>${tasks.map((tid,j)=>{
    const value = matrix.valores[rowStart + i][columnStart + j], blocked = value === null, paired = pairs.has(`${id}:${tid}`);
    const missingSkills = matrix.sem_dados?.[rowStart + i]?.[columnStart + j] || false;
    const noScore = matrix.sem_pontuacao?.[rowStart + i]?.[columnStart + j] || false;
    const selected = state.selectedCell === `${id}:${tid}`;
    const color = blocked ? '' : `background:hsl(91 35% ${96 - value * .48}%);color:${value > 65 ? '#fff' : '#183b30'}`;
    const text = blocked ? '×' : `${paired ? '✓ ' : ''}${number(value)}`;
    const description = blocked ? 'bloqueado' : `nota ${number(value)} de 100${missingSkills ? noScore ? ', pontuação zero porque não há outro critério informado; peso de habilidades ignorado por falta de dados' : ', peso de habilidades ignorado por falta de dados' : ''}${paired ? ', par apresentado' : ''}`;
    return `<td><button type="button" style="${color}" class="${blocked ? 'blocked' : ''} ${missingSkills ? 'partial' : ''} ${paired ? 'paired' : ''} ${selected ? 'selected' : ''}" data-dev="${id}" data-task="${tid}" aria-pressed="${selected}" aria-label="Dev ${id}, tarefa ${tid}: ${description}">${text}</button></td>`;
  }).join('')}</tr>`).join('');
  const noWeights = !Object.values(matrix.pesos).some(weight=>weight > 0);
  $('matrix-summary').classList.toggle('matrix-alert', noWeights);
  const missingCells = matrix.sem_dados?.flat().filter(Boolean).length || 0;
  $('matrix-summary').textContent = (noWeights ? 'Pesos de preferência em zero: todas as notas são 0. Defina um peso maior que zero na configuração para pontuar. ' : '') +
    `${matrix.dev_ids.length} devs × ${matrix.tarefa_ids.length} tarefas. Nota 0 é permitida; × indica bloqueio.` +
    (missingCells ? ` Em ${missingCells} pares faltam dados de habilidades: esse peso é ignorado, e os outros pesos são recalculados para eles. O contorno tracejado marca esses casos.` : '') +
    ' Clique em uma célula para entender a nota.';
  $('matrix-page').textContent = `Devs ${rowStart + 1}–${rowStart + devs.length} · tarefas ${columnStart + 1}–${columnStart + tasks.length} · página ${state.matrixPage + 1}/${totalPages}`;
  $('matrix-prev').disabled = state.matrixPage === 0; $('matrix-next').disabled = state.matrixPage >= totalPages - 1;
}
async function inspectPair(devId, taskId) {
  const token = ++state.detailsId;
  state.selectedCell = `${devId}:${taskId}`; renderMatrix();
  $('pair-details').textContent = 'Carregando a composição deste par…';
  try {
    const data = await api('/api/par', {method:'POST',body:JSON.stringify({config:state.matrixConfig,dev_id:devId,tarefa_id:taskId})});
    if (token !== state.detailsId) return;
    const contributions = data.componentes.filter(c=>c.peso > 0 && c.fator !== null);
    $('pair-details').innerHTML = `<h3>Dev ${data.dev_id} ↔ tarefa #${data.tarefa_id}</h3>` + (data.permitido ? `<strong>Nota: ${number(data.pontuacao)}/100</strong>` : `<strong>Par bloqueado</strong><ul>${data.motivos.map(reason=>`<li>${escapeHTML(reason)}</li>`).join('')}</ul>`) +
      (contributions.length ? '<ul>' + contributions.map(c=>`<li>${criterionNames[c.criterio]}: ${number(c.fator * 100)}% de atendimento × peso ${number(c.peso)} → ${number(c.contribuicao)} pontos.</li>`).join('') + '</ul><p class="matrix-cell-note">Contribuição = 100 × peso × atendimento ÷ soma dos pesos informados neste par.</p>' : (data.sem_pontuacao ? '<p>Nota 0: o peso de habilidades foi ignorado porque faltam dados neste par e não há outro peso com informação disponível para calcular uma nota.</p>' : '<p>Sem pesos ativos: todos os pares permitidos têm nota zero. O desempate pode produzir diferentes soluções igualmente válidas.</p>')) +
      (data.fatores_ignorados.length ? `<p>Critério ignorado neste par por falta de dados: ${data.fatores_ignorados.map(key=>criterionNames[key]).join(', ')}. A nota considera somente os pesos com informação disponível.</p>` : '') +
      (state.matrixConfig.pesos?.habilidades > 0 || state.matrixConfig.criterios?.habilidades ?
        data.habilidades_dev_informadas && data.habilidades_tarefa_informadas ? `<p>Habilidades atendidas: ${escapeHTML(data.habilidades_atendidas.join(', ') || 'nenhuma')}. Exigidas: ${escapeHTML(data.habilidades_exigidas.join(', ') || 'nenhuma; atendimento de 100%')}.</p>` : `<p>Habilidades: ${data.habilidades_dev_informadas ? 'dev classificado' : 'áreas do dev não informadas'}; ${data.habilidades_tarefa_informadas ? 'tarefa classificada' : 'requisitos da tarefa não informados'}.</p>` : '') +
      (state.matrixConfig.algoritmo === 'bfs' ? '<p class="matrix-cell-note">No BFS, os pesos apenas avaliam os pares: a busca não otimiza as notas. Cada dev e tarefa podem aparecer em apenas um par.</p>' : '<p class="matrix-cell-note">A maior nota individual nem sempre faz parte da melhor solução global. Cada dev e tarefa podem aparecer em apenas um par.</p>');
  } catch(error) { if(token === state.detailsId) $('pair-details').textContent = error.message; }
}
$('score-matrix').addEventListener('click',event=>{
  const cell = event.target.closest('button[data-dev]');
  if(cell) { pause(); inspectPair(Number(cell.dataset.dev),Number(cell.dataset.task)); }
});
$('matrix-prev').addEventListener('click',()=>{state.matrixPage--;renderMatrix();});
$('matrix-next').addEventListener('click',()=>{state.matrixPage++;renderMatrix();});
$('preview-matrix').addEventListener('click',async()=>{
  clearRun(); setBusy(true); message('');
  const config = getConfig();
  try {
    const data = await api('/api/matriz',{method:'POST',body:JSON.stringify(config)});
    state.matrix = data.matriz; state.matrixConfig = structuredClone(config); state.devs = data.devs; state.tasks = data.tarefas;
    renderMatrix(); renderGraph(); renderTable();
  } catch(error) { message(error.message,true); }
  finally { setBusy(false); }
});

function updateAlgorithmHint() {
  const info = algorithmInfo(), bfs = $('algorithm').value === 'bfs';
  $('algorithm-hint').textContent = info.hint;
  $('algorithm-label').textContent = info.label;
  $('objective-note').textContent = bfs ? '↳ BFS respeita as restrições e maximiza os pares. Não usa pesos para escolher as combinações. Cada dev recebe no máximo uma tarefa.' : '↳ Primeiro, maximiza os pares válidos. Entre essas soluções, maximiza a soma das notas. Cada dev recebe no máximo uma tarefa.';
  $('animation-note').textContent = info.realSteps ? `A animação reproduz buscas e caminhos aumentantes realmente registrados pelo ${info.name}, incluindo reorganizações dos pares. O tempo inclui o registro dos passos; a comparação mede todos sem esse registro.` : `O ${info.name} calcula a solução completa antes da animação. Os controles apresentam os pares encontrados; não mostram operações internas do solver. Pausas não alteram o tempo de cálculo.`;
}
function renderComparison() {
  const data = state.comparison;
  $('comparison-content').hidden = !data; $('download-comparison').disabled = !data;
  if (!data) {
    $('comparison-summary').textContent = 'Use “Comparar algoritmos” na configuração para calcular os quatro resultados sobre os mesmos dados.';
    $('comparison-content').innerHTML = ''; return;
  }
  const entries = Object.keys(algorithms).filter(key=>data.resultados[key]).map(key=>[key,data.resultados[key]]);
  const reference = data.resultados.scipy;
  const pairs = new Set(reference.alocacoes.map(p=>`${p.dev_id}:${p.tarefa_id}`));
  const density = reference.metricas.arestas_possiveis ? 100 * reference.metricas.arestas_validas / reference.metricas.arestas_possiveis : 0;
  $('comparison-summary').textContent = `${reference.total_devs} devs e ${reference.total_tarefas} tarefas, com os mesmos filtros, restrições, pesos, sentido e ordem. ${number(density)}% dos pares possíveis são permitidos. SciPy é a referência de quantidade e pontuação ótimas.`;
  const metrics = [
    ['Pares formados', r=>r.alocacoes.length],
    ['Pontuação total', r=>number(r.pontuacao_total)],
    ['Devs sem tarefa', r=>r.devs_sem_tarefa.length],
    ['Tarefas sem dev', r=>r.tarefas_sem_dev.length],
    ['Pares em comum com SciPy', r=>r.alocacoes.filter(p=>pairs.has(`${p.dev_id}:${p.tarefa_id}`)).length],
    ['Diferença de pontuação para SciPy', r=>number(r.pontuacao_total - reference.pontuacao_total)],
    ['Cálculo sem registro de passos', r=>`${number(r.metricas.matching_ms)} ms`],
    ['Preparação e cálculo', r=>`${number(r.metricas.total_ms)} ms`]
  ];
  $('comparison-content').innerHTML = '<p class="comparison-scroll-hint">Deslize a tabela para ver todos os algoritmos →</p><div class="comparison-table-wrap" tabindex="0" aria-label="Comparação rolável dos quatro algoritmos"><table class="comparison-table"><thead><tr><th scope="col">Métrica</th>' + entries.map(([key])=>`<th scope="col">${algorithmInfo(key).name}</th>`).join('') + '</tr></thead><tbody>' + metrics.map(([label,value])=>`<tr><th scope="row">${label}</th>${entries.map(([,r])=>`<td>${value(r)}</td>`).join('')}</tr>`).join('') + '</tbody></table></div><p class="comparison-note">Todos maximizam a quantidade de pares válidos. SciPy, SSP e Kwok também maximizam a pontuação total entre soluções dessa quantidade; diferenças residuais de arredondamento podem ocorrer. Pares diferentes podem representar soluções igualmente ótimas. BFS usa as notas somente para avaliar o resultado. Kwok usa apenas pares permitidos no grafo do solver; a preparação ainda calcula a matriz completa para a interface. Compare preparação e cálculo, além do tempo do solver. Tempos medidos sem animação nem registro de passos, com uma execução por método; repita a comparação antes de escolher pelo desempenho.</p>' +
    '<details class="comparison-pairs"><summary>Ver pares encontrados por cada algoritmo</summary>' + entries.map(([key,r])=>`<p><strong>${algorithmInfo(key).name}:</strong> ${r.alocacoes.map(p=>`Dev ${p.dev_id} → ${escapeHTML(p.tarefa || p.tarefa_id)} (${number(p.pontuacao)} pontos)`).join(' · ') || 'Nenhum par válido.'}</p>`).join('') + '</details>';
}
$('algorithm').addEventListener('change',()=>{clearRun(true);updateAlgorithmHint();updateDirectionHint();renderGraph();renderTable();});
$('compare').addEventListener('click',async()=>{
  pause(); setBusy(true); message(''); state.comparison = null; renderComparison();
  try {
    state.comparison = await api('/api/comparar',{method:'POST',body:JSON.stringify(getConfig())});
    renderComparison(); $('comparacao').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(error) { message(error.message,true); }
  finally { setBusy(false); }
});
$('download-comparison').addEventListener('click',()=>{
  if (!state.comparison) return;
  const blob = new Blob([JSON.stringify(state.comparison,null,2)],{type:'application/json'});
  const url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = 'comparacao-algoritmos.json'; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});

$('start').addEventListener('click', startRun);
$('next').addEventListener('click', () => { pause(); applyStep(); });
$('reset').addEventListener('click', rewind);
$('speed').addEventListener('change', () => { if (state.playing) { clearTimeout(state.timer); state.timer = setTimeout(tick, Number($('speed').value)); } });
function updateDirectionHint() {
  const reverse = $('direction').value === 'tarefas_para_devs', code = $('algorithm').value;
  $('direction-hint').textContent = code === 'bfs' ? (reverse ? 'A busca BFS começa por cada tarefa, à esquerda do grafo.' : 'A busca BFS começa por cada desenvolvedor, à esquerda do grafo.') : code === 'ssp' ? (reverse ? 'O SSP busca caminhos a partir das tarefas livres, à esquerda do grafo.' : 'O SSP busca caminhos a partir dos devs livres, à esquerda do grafo.') : (reverse ? 'Tarefas à esquerda do grafo; cálculo com matriz transposta. A matriz visual mantém devs nas linhas.' : 'Devs à esquerda do grafo. A apresentação segue a ordem das linhas da solução.');
}
$('direction').addEventListener('change', () => { clearRun(); updateDirectionHint(); renderGraph(); renderTable(); });
$('project').addEventListener('change', () => { populateSprints(); loadData(); });
$('sprint').addEventListener('change', loadData);
$('dev-limit').addEventListener('change', loadData);
$('task-limit').addEventListener('change', loadData);
for (const id of ['same-project','availability','skills','points','weight-project','weight-availability','weight-skills']) $(id).addEventListener('change', () => { clearRun(); updateCriteriaCount(); renderGraph(); renderTable(); });
$('reload').addEventListener('click', loadData);
$('shuffle-order').addEventListener('click', () => {
  let seed = crypto.getRandomValues(new Uint32Array(1))[0];
  if (seed === state.config.semente_embaralhamento) seed = (seed + 1) % 4294967296;
  state.config.semente_embaralhamento = seed;
  loadData();
});
$('restore-order').addEventListener('click', () => {
  state.config.semente_embaralhamento = null;
  loadData();
});
$('search').addEventListener('input', renderTable);
$('tasks-tab').addEventListener('click', () => { state.tab = 'tasks'; renderTable(); });
$('devs-tab').addEventListener('click', () => { state.tab = 'devs'; renderTable(); });
$('data-table').addEventListener('focusin', () => { if (state.playing) pause(); });
$('data-table').addEventListener('change', event => {
  const input = event.target, id = input.dataset.id, kind = input.dataset.kind;
  if (!id || state.busy) return;
  if (kind === 'task-skills' || kind === 'dev-skills') {
    const current = kind === 'task-skills' ? state.config.habilidades_tarefas?.[id] : state.config.dados_devs?.[id]?.habilidades;
    if (input.value === '__unset__') setSkills(kind, id, undefined);
    else if (input.value === '__none__') setSkills(kind, id, []);
    else if (state.catalog.areas.includes(input.value)) {
      const skills = current || [];
      if (!skills.some(skill=>skill.trim().toLocaleLowerCase('pt-BR') === input.value.toLocaleLowerCase('pt-BR'))) setSkills(kind,id,[...skills,input.value]);
    } else return;
  } else if (kind === 'availability') {
    state.config.dados_devs ||= {}; state.config.dados_devs[id] ||= {};
    if (input.value === '') delete state.config.dados_devs[id].disponivel;
    else state.config.dados_devs[id].disponivel = input.value === 'true';
  } else return;
  refreshManualData(kind, id);
});
$('data-table').addEventListener('click', event=>{
  const button = event.target.closest('button[data-remove-skill]');
  if (!button || state.busy) return;
  const {id,kind,removeSkill} = button.dataset;
  const skills = kind === 'task-skills' ? state.config.habilidades_tarefas?.[id] : state.config.dados_devs?.[id]?.habilidades;
  setSkills(kind,id,(skills || []).filter(skill=>skill !== removeSkill));
  refreshManualData(kind,id);
});
$('fill-manual').addEventListener('click', () => {
  state.config.dados_devs ||= {}; state.config.habilidades_tarefas ||= {};
  if (state.tab === 'tasks') state.tasks.forEach(t => state.config.habilidades_tarefas[String(t.ID)] = []);
  else state.devs.forEach(d => { state.config.dados_devs[String(d.ID)] ||= {}; state.config.dados_devs[String(d.ID)].disponivel = true; });
  clearRun(); renderGraph(); renderTable();
  message(state.tab === 'tasks' ? 'Tarefas declaradas sem requisitos de habilidades nesta configuração.' : 'Devs marcados como disponíveis nesta configuração.');
});
async function saveCriteria() {
  if (state.busy) return;
  pause(); setBusy(true); message('');
  const status = $('data-save-message');
  status.hidden = false; status.className = 'data-save-message'; status.textContent = 'Salvando critérios…';
  try {
    const response = await api('/api/criterios', {method:'PUT', body:JSON.stringify(getConfig())});
    message(response.mensagem); status.textContent = response.mensagem;
  } catch (error) {
    message(error.message, true); status.textContent = error.message; status.classList.add('error');
  } finally { setBusy(false); }
}
$('save-config').addEventListener('click', saveCriteria);
$('save-data-config').addEventListener('click', saveCriteria);
$('download').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify({...state.result, configuracao:state.runConfig}, null, 2)], {type:'application/json'});
  const url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = 'alocacao-matching.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
async function initialize() {
  setBusy(true);
  try {
    const data = await api('/api/inicio'); state.catalog = data; state.config = data.config;
    $('project').innerHTML += data.projetos.map(p => `<option value="${p.ID}">${escapeHTML(p.Name)}</option>`).join('');
    $('dev-limit').value = data.config.quantidade_devs ?? ''; $('task-limit').value = data.config.quantidade_tarefas ?? '';
    $('algorithm').value = data.config.algoritmo || 'scipy'; updateAlgorithmHint();
    $('direction').value = data.config.direcao || 'devs_para_tarefas'; updateDirectionHint();
    $('project').value = data.config.projeto_id ?? ''; populateSprints(data.config.sprint_id ?? '');
    const weights = data.config.pesos || {};
    $('weight-project').value = weights.mesmo_projeto ?? 0; $('weight-availability').value = weights.disponibilidade ?? 0; $('weight-skills').value = weights.habilidades ?? 0;
    const c = data.config.criterios || {};
    $('same-project').checked = Boolean(c.mesmo_projeto); $('availability').checked = Boolean(c.disponibilidade); $('skills').checked = Boolean(c.habilidades); $('points').value = c.max_story_points_por_tarefa ?? '';
    updateCriteriaCount(); await loadData();
  } catch (error) { message(error.message, true); $('db-status').textContent = 'Banco indisponível'; setBusy(false); }
}
initialize();
