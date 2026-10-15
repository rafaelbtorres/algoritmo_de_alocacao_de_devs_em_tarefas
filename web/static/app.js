'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {config: {}, catalog: {}, devs: [], tasks: [], tab: 'tasks', result: null, runConfig: null, index: 0, pairs: [], active: null, playing: false, timer: null, busy: false, loadId: 0, started: 0};
const labels = {buscar:'BUSCA POR UM PAR', avaliar:'AVALIANDO UMA CONEXÃO', ocupada:'EXPLORANDO UM CAMINHO ALTERNATIVO', alocar:'MAIS UM PAR FORMADO', sem_par:'SEM CAMINHO DISPONÍVEL', concluir:'MATCHING CONCLUÍDO'};
const number = value => Number(value).toLocaleString('pt-BR', {maximumFractionDigits: 3});

function message(text, error = false) { $('message').textContent = text; $('message').className = error ? 'error' : ''; $('message').hidden = !text; }
async function api(path, options = {}) {
  const response = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const body = await response.json();
  if (!response.ok) throw new Error(body.erro || 'Não foi possível concluir a operação.');
  return body;
}
function getConfig() {
  return {...state.config, quantidade_devs: $('dev-limit').value === '' ? null : Number($('dev-limit').value), quantidade_tarefas: $('task-limit').value === '' ? null : Number($('task-limit').value), direcao: $('direction').value, projeto_id: $('project').value ? Number($('project').value) : null, sprint_id: $('sprint').value ? Number($('sprint').value) : null,
    criterios:{mesmo_projeto:$('same-project').checked, disponibilidade:$('availability').checked, habilidades:$('skills').checked, max_story_points_por_tarefa:$('points').value === '' ? null : Number($('points').value)},
    dados_devs:state.config.dados_devs || {}, habilidades_tarefas:state.config.habilidades_tarefas || {}};
}
function populateSprints(selected = '') {
  const project = $('project').value;
  $('sprint').innerHTML = '<option value="">Todas as sprints</option>' + state.catalog.sprints.filter(s => !project || String(s.Project_ID) === project).map(s => `<option value="${s.ID}">${escapeHTML(s.Name)} · #${s.ID}</option>`).join('');
  $('sprint').value = selected === null ? '' : String(selected);
}
function setBusy(busy) {
  state.busy = busy;
  document.querySelectorAll('.config-panel input,.config-panel select,#data-table input,#data-table select,#save-config,#reload,#fill-manual').forEach(el => el.disabled = busy);
  $('fill-manual').disabled = busy || !(state.tab === 'tasks' ? state.tasks.length : state.devs.length);
  updateControls();
}
function updateControls() {
  $('start').disabled = state.busy || !state.devs.length || !state.tasks.length;
  $('start').textContent = state.busy ? 'Carregando…' : state.playing ? 'Ⅱ Pausar' : state.result ? (state.index >= state.result.passos.length ? '↺ Reproduzir novamente' : '▶ Continuar') : '▶ Iniciar alocação';
  $('next').disabled = state.busy || !state.result || state.index >= state.result.passos.length;
  $('reset').disabled = state.busy || !state.result;
}
function pause() { clearTimeout(state.timer); state.timer = null; state.playing = false; if (state.result && state.index < state.result.passos.length) $('run-status').textContent = 'Pausado'; updateControls(); }
function clearRun() {
  pause(); state.result = null; state.runConfig = null; state.index = 0; state.pairs = []; state.active = null;
  $('results-content').hidden = true; $('results-empty').hidden = false; $('download').disabled = true;
  $('pair-count').textContent = '0'; $('run-status').textContent = 'Pronto para começar'; $('step-label').textContent = 'O PONTO DE PARTIDA';
  $('step-text').textContent = 'Inicie a alocação para acompanhar a busca por pares válidos.'; $('progress-count').textContent = '0 / 0'; $('progress-bar').style.width = '0%';
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
  if (!state.result && state.devs.length && state.tasks.length) html += `<text class="graph-sub-label" x="380" y="${height / 2}" text-anchor="middle">As conexões aparecem durante a busca</text>`;
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

function renderTable() {
  const isTasks = state.tab === 'tasks';
  $('tasks-tab').classList.toggle('active', isTasks); $('devs-tab').classList.toggle('active', !isTasks);
  $('tasks-tab').setAttribute('aria-selected', isTasks); $('devs-tab').setAttribute('aria-selected', !isTasks);
  $('fill-manual').textContent = isTasks ? 'Declarar tarefas sem requisitos' : 'Marcar devs disponíveis';
  const search = $('search').value.trim().toLocaleLowerCase('pt-BR');
  const records = (isTasks ? state.tasks : state.devs).filter(row => JSON.stringify(row).toLocaleLowerCase('pt-BR').includes(search));
  const headers = isTasks ? ['Tarefa', 'Título', 'Sprint', 'Story points', 'Dev histórico', 'Alocação', 'Habilidades exigidas'] : ['Desenvolvedor', 'Projeto', 'Disponibilidade manual', 'Habilidades manuais', 'Tarefa alocada'];
  $('data-table').querySelector('thead').innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
  $('data-table').querySelector('tbody').innerHTML = records.map(row => {
    if (isTasks) {
      const pair = state.pairs.find(p => p.tarefa_id === row.ID);
      const skills = state.config.habilidades_tarefas?.[String(row.ID)];
      return `<tr><td><span class="task-code">${escapeHTML(row.Issue_Key || row.ID)}</span></td><td class="title-cell">${escapeHTML(row.Title)}</td><td><span class="table-tag">#${escapeHTML(row.Sprint_ID ?? '—')}</span></td><td>${escapeHTML(row.Story_Point ?? '—')}</td><td>${escapeHTML(row.Assignee_ID ?? '—')}</td><td><span class="table-tag ${pair ? 'matched' : ''}">${pair ? `Dev ${pair.dev_id}` : 'Sem alocação'}</span></td><td><input class="table-input" data-kind="task-skills" data-id="${row.ID}" aria-label="Habilidades exigidas pela tarefa ${row.ID}" value="${escapeHTML(skills?.join(', ') || '')}" placeholder="${skills ? 'Sem requisitos' : 'Não informado'}"></td></tr>`;
    }
    const data = state.config.dados_devs?.[String(row.ID)] || {};
    const pair = state.pairs.find(p => p.dev_id === row.ID);
    return `<tr><td class="title-cell">Dev ${row.ID}</td><td>#${escapeHTML(row.Project_ID ?? '—')}</td><td><select class="table-input" data-kind="availability" data-id="${row.ID}" aria-label="Disponibilidade do dev ${row.ID}"><option value="">Não informado</option><option value="true" ${data.disponivel === true ? 'selected' : ''}>Disponível</option><option value="false" ${data.disponivel === false ? 'selected' : ''}>Indisponível</option></select></td><td><input class="table-input" data-kind="dev-skills" data-id="${row.ID}" aria-label="Habilidades do dev ${row.ID}" value="${escapeHTML(data.habilidades?.join(', ') || '')}" placeholder="${data.habilidades ? 'Nenhuma declarada' : 'Não informado'}"></td><td>${pair ? `Tarefa #${pair.tarefa_id}` : '—'}</td></tr>`;
  }).join('') || `<tr><td colspan="${headers.length}" style="text-align:center;padding:28px">Nenhum registro encontrado.</td></tr>`;
  $('table-count').textContent = `${records.length} de ${isTasks ? state.tasks.length : state.devs.length} registros`;
  $('fill-manual').disabled = state.busy || !(isTasks ? state.tasks.length : state.devs.length);
}
function applyStep() {
  if (!state.result || state.index >= state.result.passos.length) return;
  const event = state.result.passos[state.index++];
  state.active = event.tarefa_id !== undefined || event.dev_id !== undefined ? event : null;
  if (event.tipo === 'alocar') { state.pairs = event.pares; state.active = null; }
  $('pair-count').textContent = state.pairs.length;
  $('step-label').textContent = labels[event.tipo] || 'PASSO DO ALGORITMO'; $('step-text').textContent = event.mensagem;
  $('progress-count').textContent = `${state.index} / ${state.result.passos.length}`;
  $('progress-bar').style.width = `${100 * state.index / state.result.passos.length}%`;
  $('run-status').textContent = event.tipo === 'alocar' ? `${state.pairs.length} pares formados` : state.playing ? 'Em execução' : 'Pausado';
  renderGraph(); renderTable();
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
  pause(); state.index = 0; state.pairs = []; state.active = null; state.started = performance.now();
  $('results-content').hidden = true; $('results-empty').hidden = false; $('download').disabled = true; $('pair-count').textContent = '0';
  $('progress-count').textContent = `0 / ${state.result.passos.length}`; $('progress-bar').style.width = '0%'; $('run-status').textContent = 'Pausado';
  $('step-label').textContent = 'PRONTO PARA REPRODUZIR'; $('step-text').textContent = 'Use Continuar ou avance um passo de cada vez.';
  renderGraph(); renderTable(); updateControls();
}
async function startRun() {
  if (state.playing) { pause(); $('run-status').textContent = 'Pausado'; return; }
  if (state.result) { if (state.index >= state.result.passos.length) rewind(); play(); return; }
  const config = getConfig(); setBusy(true); message('');
  try {
    const data = await api('/api/alocar', {method:'POST', body:JSON.stringify(config)});
    state.result = data.resultado; state.runConfig = data.config; state.devs = data.devs; state.tasks = data.tarefas; state.started = performance.now();
    state.index = 0; state.pairs = []; state.active = null;
    setBusy(false); play();
  } catch (error) { message(error.message, true); setBusy(false); }
}
function finish() {
  pause(); state.active = null; state.pairs = state.result.alocacoes;
  $('run-status').textContent = 'Concluído'; $('download').disabled = false;
  $('results-empty').hidden = true; $('results-content').hidden = false;
  const r = state.result, m = r.metricas, count = r.alocacoes.length;
  $('result-pairs').textContent = count; $('result-unmatched').textContent = r.tarefas_sem_dev.length;
  $('result-time').textContent = `${number(m.matching_ms)} ms`; $('result-edges').textContent = m.arestas_avaliadas;
  const ratio = r.total_tarefas ? count / r.total_tarefas : 0;
  $('distribution-chart').innerHTML = `<div class="donut-wrap"><svg width="132" height="132" viewBox="0 0 132 132" role="img" aria-label="${count} tarefas alocadas e ${r.tarefas_sem_dev.length} sem desenvolvedor"><circle cx="66" cy="66" r="47" fill="none" stroke="#eaf0e0" stroke-width="13"/><circle cx="66" cy="66" r="47" fill="none" stroke="#668b55" stroke-width="13" stroke-dasharray="${ratio * 295.31} 295.31" transform="rotate(-90 66 66)"/><text x="66" y="65" text-anchor="middle" fill="#375332" font-size="24">${number(ratio * 100)}%</text><text x="66" y="82" text-anchor="middle" fill="#95a184" font-size="9">alocadas</text></svg><div class="chart-key"><div><i style="background:#668b55"></i>${count} alocadas</div><div><i style="background:#e0e9d3"></i>${r.tarefas_sem_dev.length} sem dev</div></div></div>`;
  const times = [['Leitura do banco', m.leitura_ms], ['Preparação do grafo', m.preparacao_ms], ['Busca de matching', m.matching_ms]];
  const max = Math.max(...times.map(t => t[1]), .001);
  $('time-chart').innerHTML = '<div class="time-bars">' + times.map(([label, value]) => `<div class="time-row"><div><span>${label}</span><span>${number(value)} ms</span></div><div class="bar-track"><div class="bar-fill" style="width:${100 * value / max}%"></div></div></div>`).join('') + '</div>';
  const wallSeconds = (performance.now() - state.started) / 1000;
  const reverse = r.direcao === 'tarefas_para_devs';
  $('results-explanation').textContent = `Sentido: ${reverse ? 'tarefas → desenvolvedores' : 'desenvolvedores → tarefas'}. ${count} pares formados entre ${r.total_devs} devs e ${r.total_tarefas} tarefas. ${r.devs_sem_tarefa.length} devs ficaram sem tarefa. ${m.arestas_validas} de ${m.arestas_possiveis} pares são compatíveis com os critérios. Tempo do algoritmo: ${number(m.total_ms)} ms; reprodução visual: ${number(wallSeconds)} s (inclui pausas). O limite é de uma tarefa por dev no conjunto selecionado. As atribuições históricas do banco foram preservadas.`;
  $('allocation-list').innerHTML = r.alocacoes.map(row => `<span class="allocation-chip">${reverse ? escapeHTML(row.tarefa || row.tarefa_id) : `Dev ${row.dev_id}`} <span>→</span> ${reverse ? `Dev ${row.dev_id}` : escapeHTML(row.tarefa || row.tarefa_id)}</span>`).join('');
  renderGraph(); renderTable();
}

$('start').addEventListener('click', startRun);
$('next').addEventListener('click', () => { pause(); applyStep(); });
$('reset').addEventListener('click', rewind);
$('speed').addEventListener('change', () => { if (state.playing) { clearTimeout(state.timer); state.timer = setTimeout(tick, Number($('speed').value)); } });
function updateDirectionHint() { $('direction-hint').textContent = $('direction').value === 'tarefas_para_devs' ? 'A busca começa por cada tarefa, procurando um dev.' : 'A busca começa por cada desenvolvedor, procurando uma tarefa.'; }
$('direction').addEventListener('change', () => { clearRun(); updateDirectionHint(); renderGraph(); renderTable(); });
$('project').addEventListener('change', () => { populateSprints(); loadData(); });
$('sprint').addEventListener('change', loadData);
$('dev-limit').addEventListener('change', loadData);
$('task-limit').addEventListener('change', loadData);
for (const id of ['same-project','availability','skills','points']) $(id).addEventListener('change', () => { clearRun(); updateCriteriaCount(); renderGraph(); renderTable(); });
$('reload').addEventListener('click', loadData);
$('search').addEventListener('input', renderTable);
$('tasks-tab').addEventListener('click', () => { state.tab = 'tasks'; renderTable(); });
$('devs-tab').addEventListener('click', () => { state.tab = 'devs'; renderTable(); });
$('data-table').addEventListener('focusin', () => { if (state.playing) pause(); });
$('data-table').addEventListener('change', event => {
  const input = event.target, id = input.dataset.id;
  if (!id) return;
  state.config.dados_devs ||= {}; state.config.habilidades_tarefas ||= {};
  const list = () => input.value.split(',').map(s => s.trim()).filter(Boolean);
  if (input.dataset.kind === 'task-skills') state.config.habilidades_tarefas[id] = list();
  else {
    state.config.dados_devs[id] ||= {};
    if (input.dataset.kind === 'availability') {
      if (input.value === '') delete state.config.dados_devs[id].disponivel;
      else state.config.dados_devs[id].disponivel = input.value === 'true';
    } else state.config.dados_devs[id].habilidades = list();
  }
  clearRun(); renderGraph(); renderTable();
});
$('fill-manual').addEventListener('click', () => {
  state.config.dados_devs ||= {}; state.config.habilidades_tarefas ||= {};
  if (state.tab === 'tasks') state.tasks.forEach(t => state.config.habilidades_tarefas[String(t.ID)] = []);
  else state.devs.forEach(d => { state.config.dados_devs[String(d.ID)] ||= {}; state.config.dados_devs[String(d.ID)].disponivel = true; });
  clearRun(); renderGraph(); renderTable();
  message(state.tab === 'tasks' ? 'Tarefas declaradas sem requisitos de habilidades nesta configuração.' : 'Devs marcados como disponíveis nesta configuração.');
});
$('save-config').addEventListener('click', async () => {
  pause(); setBusy(true); message('');
  try { const response = await api('/api/criterios', {method:'PUT', body:JSON.stringify(getConfig())}); message(response.mensagem); }
  catch (error) { message(error.message, true); }
  finally { setBusy(false); }
});
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
    $('direction').value = data.config.direcao || 'devs_para_tarefas'; updateDirectionHint();
    $('project').value = data.config.projeto_id ?? ''; populateSprints(data.config.sprint_id ?? '');
    const c = data.config.criterios || {};
    $('same-project').checked = Boolean(c.mesmo_projeto); $('availability').checked = Boolean(c.disponibilidade); $('skills').checked = Boolean(c.habilidades); $('points').value = c.max_story_points_por_tarefa ?? '';
    updateCriteriaCount(); await loadData();
  } catch (error) { message(error.message, true); $('db-status').textContent = 'Banco indisponível'; setBusy(false); }
}
initialize();
