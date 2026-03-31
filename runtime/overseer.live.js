/**
 * Ficheiro: frontend-src/apps/overseer/overseer.js
 * Finalidade: Controlador frontend can?nico da app Overseer.
 * Depende de: DOM da p?gina, config local, shared UI MAIATRON e endpoints/dados da superf?cie respetiva.
 * Entradas/Sa?das principais: Recebe eventos do utilizador, estado remoto/local e atualiza UI, estado e pedidos de rede.
 * Efeitos laterais: Pode manipular DOM, timers, fetch, localStorage/sessionStorage e estados visuais.
 * Rela??o can?nica: Source can?nico em frontend-src; o runtime p?blico correspondente ? publicado como copia real sincronizada.
 */
const CONFIG={themeKey:'overseer_theme',refreshMs:30000,apiBaseUrl:'api.php',authConfigUrl:'../../config/auth.local.json',triggerKey:'overseer_trigger_history_v1',inflightKey:'overseer_inflight_v1'};

/* ====== i18n — PT-PT / EN ====== */
const LANG={
pt:{
  brandTag:'Monitorização e orquestração de pipelines',
  signalsTitle:'Sinais operacionais',
  chartHistory:'Histórico de Runs',chartHealth:'Saúde dos Pipelines',healthLabel:'saúde',
  granHour:'Hora',granDay:'Dia',granWeek:'Semana',granMonth:'Mês',
  navDashboard:'Dashboard',navPipelines:'Pipelines',navOrchestrator:'Orquestração',navInsights:'Insights',navRuns:'Runs',navLineage:'Lineage',
  searchPlaceholder:'Pesquisar por ID, script, host ou erro...',
  home:'Home',refresh:'Atualizar agora',toggleTheme:'Alternar tema',changeLang:'Mudar idioma',
  lastUpdate:'Última atualização:',logout:'Terminar sessão',
  healthOk:'Operação estável',healthWarn:'Atenção — pipelines em risco',healthCrit:'Atenção operacional',
  hintAtRisk:'Pipelines com falha recente, execução atrasada ou degradação contínua. Requerem atenção prioritária.',
  hintStale:'Pipelines que não executaram dentro da janela esperada (>24h). Podem indicar scheduler parado ou erro silencioso.',
  hintRegressions:'Pipelines onde a taxa de falha dos últimos 7 dias piorou face à semana anterior. Tendência negativa.',
  hintVolume:'Comparação de execuções recentes (24h) com a média histórica. Desvios podem indicar problemas.',
  labelAtRisk:'Pipelines com atenção',labelStale:'Pipelines sem runs (24h)',labelRegressions:'Regressões ativas',labelVolume:'Anomalia de volume',
  hintAtRiskShort:'Sem risco detetado',hintStaleShort:'Cobertura atualizada',hintRegressionsShort:'Sem regressões relevantes',hintVolumeShort:'Volume dentro do padrão',
  colId:'#',colPipeline:'Pipeline',colStatus:'Estado',colRequested:'Requested by (actor)',colRunner:'Runner target',colHost:'Host executado',colOS:'SO',colStart:'Início',colEnd:'Fim',colDuration:'Duração',colCPU:'CPU',colMem:'Memória',colDetails:'Detalhes',
  colOwner:'Owner',colCriticality:'Criticidade',colSuccess7d:'Sucesso 7d',colRegression:'Regressão',colStale:'Stale(h)',colRisk:'Risco',colSchedule:'Schedule',colPermission:'Permissão',colActions:'Ações',
  pipeTitle:'Pipelines (prioridade operacional)',orchTitle:'Orquestração de Pipelines',orchRunsTitle:'Runs de Orquestração',
  filterAllRisks:'Todos os riscos',filterCritical:'Crítico',filterHigh:'Alto',filterMedium:'Médio',filterLow:'Baixo',
  filterPeriod:'Período de runs',filter24h:'Últimas 24 horas',filter7d:'Últimos 7 dias',filter30d:'Últimos 30 dias',filterAll:'Todos',
  prev:'Anterior',next:'Seguinte',noRecords:'Sem registos',lines:'Linhas',
  alertsRecent:'Alertas recentes (FAILED)',pipeFailures:'Pipelines com mais falhas (7 dias)',incidentsTimeline:'Timeline de incidentes',topRegressions:'Top regressões',quickActions:'Ações rápidas',
  btnShowNok:'Ver FAILED (7d)',btnOpenNok:'Abrir último FAILED',btnResetOverview:'Reset overview',
  lineageTitle:'Lineage / Pipelines (dados atuais)',filterPipeline:'Filtrar pipeline...',clear:'Limpar',
  orchNoApi:'Modo sem API — use "Run now" para disparar execução imediata, ou edite o schedule para alterar o agendamento. Permissões baseadas no seu perfil de utilizador.',
  runNow:'Run now',copyCli:'Copiar cmd',save:'Guardar',pause:'Pause',resume:'Resume',
  dataUpdated:'Dados atualizados',dataFail:'Falha a carregar JSON de monitorização',invalidPayload:'Payload inválido — dados mantidos',
  orchLocalUpdated:'Orquestração local atualizada',
  freshness:'Frescura de dados',qualityGates:'Quality gates (7d)',execEfficiency:'Eficiência de execução',
  riskLabel:'Risco',success7dLabel:'Sucesso 7d',staleLabel:'Stale',
  owner:'Owner',schedule:'Schedule',
  healthy:'Saudável',attention:'Atenção',failed:'Falhado',
  modalTitle:'Detalhe da Run',logTitle:'Log completo',close:'Fechar',details:'Detalhes',
  noData:'Sem dados',noPipeline:'Sem pipeline selecionado.',noMatch:'Sem correspondências',adjustFilter:'Ajusta o filtro de pipeline.',
  scripts:'scripts',executed:'executados',modules:'módulos',errors:'erros',warnings:'warnings',
  lastActivity:'Última atividade:',noScripts:'Sem scripts',noInventory:'Não há inventário para este pipeline.',
  noModules:'Sem módulos',noModuleEvents:'Ainda sem eventos de módulo para este pipeline.',
  noDeps:'Sem dependências declaradas.',logNotAvail:'Sem logs disponíveis para este script',
  drawerTitle:'Glossário de métricas',
  noNoKFilter:'Sem runs FAILED no filtro atual',
  copied:'Comando copiado para terminal',triggerOk:'Run now enviado com sucesso',triggerFail:'Erro ao enviar trigger. Comando CLI copiado.',
  schedInvalidMsg:'Schedule inválido. Use expressão cron (ex: 30 7 * * *) ou "manual".',
  schedChanged:'alterado com sucesso',schedFail:'Erro ao enviar trigger de schedule. Comando CLI copiado.',
  noPerm:'Sem permissão para executar este pipeline',noPermShort:'Sem permissão — contacta o owner',
  running:'A executar agora',
  results:'resultado',resultsPlural:'resultados',
  all:'Todos',manual:'Manual',paused:'Paused',
},
en:{
  brandTag:'Pipeline monitoring and orchestration',
  signalsTitle:'Operational signals',
  chartHistory:'Run History',chartHealth:'Pipeline Health',healthLabel:'health',
  granHour:'Hour',granDay:'Day',granWeek:'Week',granMonth:'Month',
  navDashboard:'Dashboard',navPipelines:'Pipelines',navOrchestrator:'Orchestration',navInsights:'Insights',navRuns:'Runs',navLineage:'Lineage',
  searchPlaceholder:'Search by ID, script, host or error...',
  home:'Home',refresh:'Refresh now',toggleTheme:'Toggle theme',changeLang:'Change language',
  lastUpdate:'Last update:',logout:'Sign out',
  healthOk:'Stable operation',healthWarn:'Warning — pipelines at risk',healthCrit:'Operational alert',
  hintAtRisk:'Pipelines with recent failure, overdue execution or ongoing degradation. Require priority attention.',
  hintStale:'Pipelines with no execution in the expected window (>24h). May indicate stopped scheduler or silent error.',
  hintRegressions:'Pipelines where the failure rate over the last 7 days worsened vs the previous week. Negative trend.',
  hintVolume:'Comparison of recent executions (24h) vs historical average. Deviations may indicate issues.',
  labelAtRisk:'At-risk pipelines',labelStale:'Stale pipelines (24h)',labelRegressions:'Active regressions',labelVolume:'Volume anomaly',
  hintAtRiskShort:'No risk detected',hintStaleShort:'Coverage up to date',hintRegressionsShort:'No relevant regressions',hintVolumeShort:'Volume within norm',
  colId:'#',colPipeline:'Pipeline',colStatus:'Status',colRequested:'Requested by (actor)',colRunner:'Runner target',colHost:'Executed host',colOS:'OS',colStart:'Start',colEnd:'End',colDuration:'Duration',colCPU:'CPU',colMem:'Memory',colDetails:'Details',
  colOwner:'Owner',colCriticality:'Criticality',colSuccess7d:'Success 7d',colRegression:'Regression',colStale:'Stale(h)',colRisk:'Risk',colSchedule:'Schedule',colPermission:'Permission',colActions:'Actions',
  pipeTitle:'Pipelines (operational priority)',orchTitle:'Pipeline Orchestration',orchRunsTitle:'Orchestration Runs',
  filterAllRisks:'All risks',filterCritical:'Critical',filterHigh:'High',filterMedium:'Medium',filterLow:'Low',
  filterPeriod:'Run period',filter24h:'Last 24 hours',filter7d:'Last 7 days',filter30d:'Last 30 days',filterAll:'All',
  prev:'Previous',next:'Next',noRecords:'No records',lines:'Rows',
  alertsRecent:'Recent alerts (FAILED)',pipeFailures:'Pipelines with most failures (7 days)',incidentsTimeline:'Incident timeline',topRegressions:'Top regressions',quickActions:'Quick actions',
  btnShowNok:'Show FAILED (7d)',btnOpenNok:'Open latest FAILED',btnResetOverview:'Reset overview',
  lineageTitle:'Lineage / Pipelines (current data)',filterPipeline:'Filter pipeline...',clear:'Clear',
  orchNoApi:'No-API mode — use "Run now" to trigger immediate execution, or edit the schedule. Permissions based on your user profile.',
  runNow:'Run now',copyCli:'Copy cmd',save:'Save',pause:'Pause',resume:'Resume',
  dataUpdated:'Data updated',dataFail:'Failed to load monitoring JSON',invalidPayload:'Invalid payload — data retained',
  orchLocalUpdated:'Local orchestration updated',
  freshness:'Data freshness',qualityGates:'Quality gates (7d)',execEfficiency:'Execution efficiency',
  riskLabel:'Risk',success7dLabel:'Success 7d',staleLabel:'Stale',
  owner:'Owner',schedule:'Schedule',
  healthy:'Healthy',attention:'Warning',failed:'Failed',
  modalTitle:'Run Detail',logTitle:'Full log',close:'Close',details:'Details',
  noData:'No data',noPipeline:'No pipeline selected.',noMatch:'No matches',adjustFilter:'Adjust the pipeline filter.',
  scripts:'scripts',executed:'executed',modules:'modules',errors:'errors',warnings:'warnings',
  lastActivity:'Last activity:',noScripts:'No scripts',noInventory:'No inventory for this pipeline.',
  noModules:'No modules',noModuleEvents:'No module events for this pipeline yet.',
  noDeps:'No declared dependencies.',logNotAvail:'No logs available for this script',
  drawerTitle:'Metrics glossary',
  noNoKFilter:'No FAILED runs in current filter',
  copied:'Command copied to terminal',triggerOk:'Run now sent successfully',triggerFail:'Error sending trigger. CLI command copied.',
  schedInvalidMsg:'Invalid schedule. Use cron expression (e.g. 30 7 * * *) or "manual".',
  schedChanged:'changed successfully',schedFail:'Error sending schedule trigger. CLI command copied.',
  noPerm:'No permission to run this pipeline',noPermShort:'No permission — contact the owner',
  running:'Running now',
  results:'result',resultsPlural:'results',
  all:'All',manual:'Manual',paused:'Paused',
}
};
function t(key){return LANG[state.lang]?.[key]||LANG.pt[key]||key;}
function setLang(lang){state.lang=lang;localStorage.setItem('overseer_lang',lang);const flag=document.getElementById('langFlag');if(flag)flag.textContent=lang==='pt'?'PT':'EN';applyLangToStaticElements();if(state.payload)renderAll();}
function applyLangToStaticElements(){document.querySelectorAll('[data-i18n]').forEach((el)=>{const key=el.getAttribute('data-i18n');if(key){const txt=t(key);if(el.tagName==='INPUT'||el.tagName==='TEXTAREA')el.placeholder=txt;else el.textContent=txt;}});const q=document.getElementById('q');if(q)q.placeholder=t('searchPlaceholder');}

let maiatronUsers = [];
async function loadMaiatronUsers() {
  try {
    const d = await apiGet('list_users');
    if (d && d.status === 'ok' && Array.isArray(d.users)) {
      maiatronUsers = d.users;
    }
  } catch (e) {
    handleAuthApiError(e);
  }
}
const state={user:null,payload:null,details:{},runsAll:[],runsView:[],pipelinesAll:[],pipelinesView:[],overview:null,lineageNodes:[],moduleLineage:{},pipelineScripts:{},orchestratorPipelines:[],orchestratorTriggers:[],orchRuns:[],pipelinePermissions:{},pendingScheduleMutations:{},healthStatus:null,q:'',runsStatus:'',runsTimeFilter:'all',selectedPipelineId:'',lineageSelectedPipelineId:'',runsLimit:25,runsOffset:0,runsSortKey:'startDate',runsSortDir:'desc',pipelinesLimit:25,pipelinesOffset:0,orchLimit:20,orchOffset:0,historyGranularity:'day',lang:localStorage.getItem('overseer_lang')||'pt'};
let historyChart=null,healthChart=null,execTimeTrendChart=null,searchDebounceTimer=null;
const DASHBOARD_TIME_SERIES_CHART_IDS=['runsHistoryChart'];
let chartControlsBound=false;
let zoomPluginRegistered=false;
let expandedChartInstance=null;
let expandedChartSourceId=null;
let expandedChartTriggerEl=null;
const RUN_COLUMNS=[['id','colId'],['pipelineId','colPipeline'],['status','colStatus'],['requestedByActor','colRequested'],['runnerHost','colRunner'],['hostname','colHost'],['osName','colOS'],['startDate','colStart'],['endDate','colEnd'],['durationLabel','colDuration'],['cpuLabel','colCPU'],['memLabel','colMem'],['details','colDetails']];

function normalizeRunStatus(raw){
  const status=String(raw||'').trim().toUpperCase();
  if(['OK','SUCCESS','SUCESSO'].includes(status))return 'OK';
  if(['WARNING','WARN'].includes(status))return 'WARNING';
  if(['FAILED','FAIL','ERROR','NOK'].includes(status))return 'FAILED';
  return status||'UNKNOWN';
}
function isOkStatus(raw){return normalizeRunStatus(raw)==='OK';}
function isWarningStatus(raw){return normalizeRunStatus(raw)==='WARNING';}
function isFailedStatus(raw){return normalizeRunStatus(raw)==='FAILED';}

document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initUi();
  initAuthUi();
  if (window.MaiatronAuthUI?.mount) {
    window.MaiatronAuthUI.mount({
      configUrl: CONFIG.authConfigUrl,
      toast: showToast,
      onAuthLost: () => location.reload(),
      menu: { passwordSource: 'shared' },
      appPermissions: {
        enabled: true,
        appKey: 'overseer',
        appLabel: 'Overseer',
        allowScopes: false
      }
    });
  }
  await checkSession();
});

function resolveInitialAuthGate() {
  if (window.__maiatronAuthGateFallback) {
    window.clearTimeout(window.__maiatronAuthGateFallback);
    window.__maiatronAuthGateFallback = null;
  }
  document.documentElement.classList.remove('maiatron-auth-pending');
}

async function checkSession() {
  try {
    if (!window.MaiatronAuth) throw new Error('Auth module indisponível');
    await window.MaiatronAuth.requireAuth({
      options: { configUrl: CONFIG.authConfigUrl, appKey: 'overseer' },
      onAuthorized: async (session) => {
        state.user = {
          username: session.username,
          displayName: (window.MaiatronAuth?.getDisplayName
            ? window.MaiatronAuth.getDisplayName(session)
            : session.displayName || session.username),
        };
        window.MaiatronAuthUI?.setSession(session || null);
        showMainApp();
        await loadMaiatronUsers();
        await refreshAllData({ showSuccessToast: false, hardRefresh: true, force: true });
        startAutoRefresh();
      },
      onUnauthorized: () => {
        stopAutoRefresh();
        showLoginScreen();
      },
    });
  } catch (error) {
    console.error('checkSession error:', error);
    stopAutoRefresh();
    showLoginError('Falha ao inicializar autenticação.');
    showLoginScreen();
  } finally {
    resolveInitialAuthGate();
  }
}

function toggleUserMenu(){const m=document.querySelector('.user-menu');const b=document.getElementById('userBtn');if(!m)return;const open=m.classList.toggle('open');m.setAttribute('aria-expanded',String(open));b?.setAttribute('aria-expanded',String(open));}
function closeUserMenu(){const m=document.querySelector('.user-menu');const b=document.getElementById('userBtn');if(!m)return;m.classList.remove('open');m.setAttribute('aria-expanded','false');b?.setAttribute('aria-expanded','false');}

function initUi(){initMotion();setText('currentYear',new Date().getFullYear());document.getElementById('themeToggle')?.addEventListener('click',onToggleTheme);document.getElementById('loginThemeToggle')?.addEventListener('click',onToggleTheme);document.getElementById('refreshBtn')?.addEventListener('click',manualRefresh);document.querySelectorAll('.nav-tab').forEach((b)=>b.addEventListener('click',()=>switchView(b.dataset.view)));
document.getElementById('userBtn')?.addEventListener('click',toggleUserMenu);document.addEventListener('click',(e)=>{const m=document.querySelector('.user-menu');if(m&&!m.contains(e.target))closeUserMenu();});
document.getElementById('modalCloseBtn')?.addEventListener('click',closeModal);document.getElementById('runDetailOverlay')?.addEventListener('click',closeModal);
document.addEventListener('keydown',(e)=>{if(e.key==='Escape'){closeUserMenu();closeModal();closeMetricsDrawer();closeExpandedChartModal();}});
document.getElementById('q')?.addEventListener('input',(e)=>{const raw=(e.target.value||'').trim();if(searchDebounceTimer)clearTimeout(searchDebounceTimer);searchDebounceTimer=setTimeout(()=>{state.q=raw;state.selectedPipelineId='';state.runsOffset=0;applyRunFilters();applyPipelineFilters();renderRuns();renderPipelines();updateSearchCounter();if(state.q)switchView('runsView');},150);});
document.getElementById('timeFilter')?.addEventListener('change',(e)=>{state.runsTimeFilter=e.target.value||'all';state.runsOffset=0;applyRunFilters();renderRuns();});
document.getElementById('pageSize')?.addEventListener('change',(e)=>{state.runsLimit=Number(e.target.value)||25;state.runsOffset=0;renderRuns();});
document.getElementById('prevPage')?.addEventListener('click',()=>{state.runsOffset=Math.max(0,state.runsOffset-state.runsLimit);renderRuns();});
document.getElementById('nextPage')?.addEventListener('click',()=>{if(state.runsOffset+state.runsLimit>=state.runsView.length)return;state.runsOffset+=state.runsLimit;renderRuns();});
document.getElementById('pipelinesPrevPage')?.addEventListener('click',()=>{state.pipelinesOffset=Math.max(0,state.pipelinesOffset-state.pipelinesLimit);renderPipelines();});
document.getElementById('pipelinesNextPage')?.addEventListener('click',()=>{if(state.pipelinesOffset+state.pipelinesLimit>=state.pipelinesView.length)return;state.pipelinesOffset+=state.pipelinesLimit;renderPipelines();});
document.getElementById('pipelineRiskFilter')?.addEventListener('change',()=>{state.pipelinesOffset=0;applyPipelineFilters();renderPipelines();});
document.getElementById('historyGranularity')?.addEventListener('change',(e)=>{state.historyGranularity=e.target.value;renderCharts();});
document.getElementById('quickFilter')?.addEventListener('change',(e)=>{const v=e.target.value;state.q='';state.runsStatus=(v==='nok_24h'||v==='nok_7d')?'FAILED':'';if(v==='nok_24h'){state.runsTimeFilter='24h';}else if(v==='nok_7d'){state.runsTimeFilter='7d';}else{state.runsTimeFilter='all';}const tf=document.getElementById('timeFilter');if(tf)tf.value=state.runsTimeFilter;applyRunFilters();if(v==='high_cpu')state.runsView=state.runsView.filter((r)=>Number(r.usageCPU||0)>80);renderRuns();switchView('runsView');});
document.getElementById('qaShowNok')?.addEventListener('click',()=>{state.runsStatus='FAILED';state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');});
document.getElementById('qaOpenLatestNok')?.addEventListener('click',async()=>{const i=state.runsView.find((r)=>isFailedStatus(r.status));if(!i){showToast(t('noNoKFilter'),'info');return;}await openRun(i.id);});
document.getElementById('qaResetOverview')?.addEventListener('click',()=>{state.q='';state.runsStatus='';state.selectedPipelineId='';state.lineageSelectedPipelineId='';applyRunFilters();applyPipelineFilters();renderAll();switchView('dashboardView');});
document.getElementById('orchRefreshBtn')?.addEventListener('click',()=>{loadTriggerHistory();renderOrchestratorRuns();showToast(t('orchLocalUpdated'),'success');});
document.getElementById('orchPrevPage')?.addEventListener('click',()=>{state.orchOffset=Math.max(0,state.orchOffset-state.orchLimit);renderOrchestratorRuns();});
document.getElementById('orchNextPage')?.addEventListener('click',()=>{if(state.orchOffset+state.orchLimit>=state.orchRuns.length)return;state.orchOffset+=state.orchLimit;renderOrchestratorRuns();});
document.getElementById('metricsHelpHeaderBtn')?.addEventListener('click',toggleMetricsDrawer);
document.getElementById('metricsDrawerClose')?.addEventListener('click',toggleMetricsDrawer);
document.getElementById('metricsDrawerOverlay')?.addEventListener('click',toggleMetricsDrawer);
document.querySelectorAll('.signal-card').forEach((el)=>el.addEventListener('click',()=>{const sig=el.dataset.signal;if(sig==='atRisk'){state.pipelinesOffset=0;const rf=document.getElementById('pipelineRiskFilter');if(rf)rf.value='critical';applyPipelineFilters();renderPipelines();switchView('pipelinesView');}else if(sig==='stale'){state.runsTimeFilter='24h';state.runsStatus='';state.runsOffset=0;const tf=document.getElementById('timeFilter');if(tf)tf.value='24h';applyRunFilters();renderRuns();switchView('runsView');}else if(sig==='regressions'){state.pipelinesOffset=0;applyPipelineFilters();renderPipelines();switchView('pipelinesView');}else if(sig==='volume'){state.runsTimeFilter='24h';state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');}}));
document.getElementById('healthHighlight')?.addEventListener('click',()=>{switchView('insightsView');});
applyLangToStaticElements();bindRunLogToolbar();bindDashboardChartControls();bindChartExpandModal();state.activeView='dashboardView';switchView('dashboardView');}
function initAuthUi(){const f=document.getElementById('loginForm');f?.addEventListener('submit',async(e)=>{e.preventDefault();const u=(document.getElementById('username')?.value||'').trim();const p=document.getElementById('password')?.value||'';const rememberSession=document.getElementById('rememberSession')?.checked??true;const rememberUsername=document.getElementById('rememberUsername')?.checked??false;const b=f.querySelector('.login-btn');b?.classList.add('loading');try{const result=await window.MaiatronAuth.login(u,p,{configUrl:CONFIG.authConfigUrl,rememberSession});if(!result.ok){showLoginError('Utilizador ou password incorretos');return;}window.MaiatronAuth.saveLoginPreferences({rememberUsername,rememberSession,username:u});state.user={username:result.session.username,displayName:(window.MaiatronAuth?.getDisplayName?window.MaiatronAuth.getDisplayName(result.session):result.session.displayName||result.session.username)};window.MaiatronAuthUI?.setSession(result.session||null);clearLoginError();showMainApp();await refreshAllData();startAutoRefresh();}finally{b?.classList.remove('loading');}});
document.getElementById('logoutBtn')?.addEventListener('click',async()=>{await window.MaiatronAuth.logout({configUrl:CONFIG.authConfigUrl});window.MaiatronAuthUI?.setSession(null);stopAutoRefresh();showLoginScreen();});
document.getElementById('deniedLogoutBtn')?.addEventListener('click',async()=>{await window.MaiatronAuth.logout({configUrl:CONFIG.authConfigUrl});window.MaiatronAuthUI?.setSession(null);stopAutoRefresh();showLoginScreen();});
document.getElementById('forgotPasswordBtn')?.addEventListener('click',async()=>{if(!window.MaiatronAuth||typeof window.MaiatronAuth.forgotPassword!=='function'){showToast('Funcionalidade indisponível','error');return;}const cu=(document.getElementById('username')?.value||'').trim();const u=cu||window.prompt('Indique o utilizador para reset da password:');if(!u)return;const c=window.confirm('Vai gerar uma nova password temporária para "'+u+'". Continuar?');if(!c)return;const r=await window.MaiatronAuth.forgotPassword(u,{configUrl:CONFIG.authConfigUrl});if(!r.ok){showToast(r.reason==='invalid_user'?'Utilizador inexistente ou inativo.':'Erro ao recuperar password','error');return;}const pi=document.getElementById('password');if(pi){pi.value=r.temporaryPassword||'';pi.focus();pi.select();}showToast('Password temporária gerada. Faça login com a nova password.','success');});
syncLoginPreferencesUi();}
function syncLoginPreferencesUi(){if(!window.MaiatronAuth?.getLoginPreferences)return;const prefs=window.MaiatronAuth.getLoginPreferences();const ru=document.getElementById('rememberUsername');const rs=document.getElementById('rememberSession');const ui=document.getElementById('username');if(ru)ru.checked=prefs.rememberUsername;if(rs)rs.checked=prefs.rememberSession;if(ui&&prefs.username)ui.value=prefs.username;}

function apiBaseUrl(){return window.OVERSEER_ASSETS?.apiBaseUrl||CONFIG.apiBaseUrl;}

function rowToObj(fields,row){const o={};fields.forEach((f,i)=>{o[f]=row[i];});return o;}
function isTechnicalStepRunRow(run){
  const pipelineId=String(run?.pipelineId||'').trim();
  const scriptName=String(run?.scriptName||'').trim();
  const runLocalId=Number(run?.runLocalId||0);
  if(!pipelineId||!scriptName||!runLocalId)return false;
  return scriptName.startsWith(`${pipelineId}:`);
}
function dedupeRuns(runs){
  const byKey=new Map();
  for(const run of runs||[]){
    const runLocalId=Number(run?.runLocalId||0);
    const key=runLocalId>0
      ? `local:${runLocalId}`
      : `logical:${String(run?.pipelineId||'')}:${String(run?.startDate||'')}:${String(run?.scriptName||'')}`;
    const prev=byKey.get(key);
    if(!prev||Number(run?.id||0)>Number(prev?.id||0))byKey.set(key,run);
  }
  return Array.from(byKey.values());
}
function enrichRun(run){
  const c={...run};
  c.id=Number(c.id||0);
  c.runLocalId=Number(c.runLocalId||c.run_local_id||0)||null;
  c.pipelineId=c.pipelineId||c.pipeline_id||c.scriptName||'pipeline-sem-nome';
  c.status=normalizeRunStatus(c.status);
  c.execTime=toNum(c.execTime);
  c.usageCPU=toNum(c.usageCPU);
  c.usageMemoria=toNum(c.usageMemoria);
  c.durationLabel=c.durationLabel||formatDuration(c.execTime);
  c.cpuLabel=c.cpuLabel||`${c.usageCPU.toFixed(1)}%`;
  c.memLabel=c.memLabel||`${c.usageMemoria.toFixed(1)} MB`;
  c.owner=c.owner||'unknown';
  c.criticality=c.criticality||'medium';
  c.errorPreview=c.errorPreview||'';
  c.run_id_pipeline=c.run_id_pipeline||`${c.pipelineId}#${c.id}`;
  c.requestedByActor=c.requestedByActor||c.requestedBy||c.requested_by||'-';
  c.requestedBySSO=c.requestedBySSO||c.requested_by_sso||c.requestedByActor||'-';
  c.requestedBy=c.requestedByActor;
  c.runnerHost=c.runnerHost||c.runner_host||'-';
  c.hostname=c.hostname||'-';
  c.osName=c.osName||'desconhecido';
  c.osRelease=c.osRelease||c.os_release||'';
  c.osPlatform=c.osPlatform||c.os_platform||'';
  const d=state.details?.[String(c.id)]||state.details?.[c.id]||null;
  if(d?.errorMessage&&!c.errorMessage)c.errorMessage=d.errorMessage;
  if(d?.run_id_pipeline)c.run_id_pipeline=d.run_id_pipeline;
  if(d?.run_local_id && !c.runLocalId)c.runLocalId=Number(d.run_local_id)||null;
  return c;
}
function deriveOverview(runs,summary){const total=runs.length,ok=runs.filter((r)=>isOkStatus(r.status)).length,warning=runs.filter((r)=>isWarningStatus(r.status)).length,failedCount=runs.filter((r)=>isFailedStatus(r.status)).length;const grouped=groupByPipeline(runs);let atRisk=0,stale=0,failed=0,regressions=0;for(const list of Object.values(grouped)){if(!list.length)continue;const latest=list[0];const staleHours=Math.floor((Date.now()-dateValue(latest.startDate))/3600000);const isStale=!latest.startDate||staleHours>24;const isFailed=isFailedStatus(latest.status);const failRate=list.slice(0,7).filter((x)=>isFailedStatus(x.status)).length/Math.max(1,Math.min(7,list.length));if(isFailed)failed+=1;if(isStale)stale+=1;if(failRate>0.2)regressions+=1;if(isFailed||isStale||failRate>0.2)atRisk+=1;}
const immediate=runs.filter((r)=>isFailedStatus(r.status)).slice(0,5).map((r)=>({pipelineId:r.pipelineId,name:r.scriptName,runId:r.id,run_id_pipeline:r.run_id_pipeline,reason:'última run FAILED',when:r.startDate}));
const incidents=runs.filter((r)=>isFailedStatus(r.status)||!r.startDate||Math.floor((Date.now()-dateValue(r.startDate))/3600000)>24).slice(0,10).map((r)=>({pipelineId:r.pipelineId,name:r.scriptName,runId:r.id,run_id_pipeline:r.run_id_pipeline,reason:isFailedStatus(r.status)?'falha':'stale',when:r.startDate}));
return {generatedAt:summary.generated_at||new Date().toISOString(),globalKpis:{totalRuns:Number(summary.total_runs||total),okRuns:Number(summary.ok_runs||ok),warningRuns:Number(summary.warning_runs||warning),failedRuns:Number(summary.failed_runs||summary.nok_runs||failedCount),nokRuns:Number(summary.nok_runs||summary.failed_runs||failedCount),successRate:Number(summary.success_rate||(total?(ok/total)*100:100)),avgExecTime:Number(summary.avg_exec_time||avg(runs.map((r)=>r.execTime))),avgCpu:Number(summary.avg_cpu||avg(runs.map((r)=>r.usageCPU))),avgMem:Number(summary.avg_mem||avg(runs.map((r)=>r.usageMemoria))),p95ExecTime:Number(summary.p95_exec_time||percentile(runs.map((r)=>r.execTime),0.95))},operationalSignals:{pipelineCount:Number(summary.pipeline_count||Object.keys(grouped).length),atRisk:Number(summary.at_risk||atRisk),stale:Number(summary.stale||stale),regressions:Number(summary.regressions||regressions),failed,warnings:Number(summary.warning_runs||warning),volume:{status:'good',ratio:1,runs24h:runs.filter((r)=>Date.now()-dateValue(r.startDate)<=86400000).length,baseline:0}},topAlerts:{immediate,incidents}};}
function derivePipelines(runs){const grouped=groupByPipeline(runs),items=[];for(const [pipelineId,list] of Object.entries(grouped)){const latest=list[0],recent=list.slice(0,7),failedRecent=recent.filter((r)=>isFailedStatus(r.status)).length,successRate7d=recent.length?((recent.length-failedRecent)/recent.length)*100:100,staleHours=latest.startDate?Math.floor((Date.now()-dateValue(latest.startDate))/3600000):null;const riskScore=Math.max(0,Math.min(100,(isFailedStatus(latest.status)?45:isWarningStatus(latest.status)?20:0)+((staleHours??999)>24?25:0)+(failedRecent/Math.max(1,recent.length)>0.2?20:0)));const riskLevel=riskScore>=80?'critical':riskScore>=55?'high':riskScore>=30?'medium':'low';items.push({pipelineId,name:latest.scriptName||pipelineId,owner:latest.owner||'unknown',criticality:latest.criticality||'medium',lastRun:latest.startDate||null,lastStatus:normalizeRunStatus(latest.status),successRate7d,regressionDelta:0,staleHours,riskScore,riskLevel});}return items.sort((a,b)=>b.riskScore-a.riskScore||dateValue(b.lastRun)-dateValue(a.lastRun));}
function deriveLineage(pipelines){return pipelines.slice(0,60).map((p)=>({pipelineId:p.pipelineId,name:p.name,status:p.lastStatus}));}
function applyRunFilters(){
  let runs=[...state.runsAll];
  if(state.runsTimeFilter&&state.runsTimeFilter!=='all'){
    const now=Date.now();
    const ms=state.runsTimeFilter==='24h'?86400000:state.runsTimeFilter==='7d'?604800000:state.runsTimeFilter==='30d'?2592000000:0;
    if(ms>0)runs=runs.filter((r)=>dateValue(r.startDate)>=now-ms);
  }
  if(state.q){
    const q=state.q.toLowerCase();
    runs=runs.filter((r)=>[
      r.id,r.run_id_pipeline,r.pipelineId,r.scriptName,r.hostname,r.runnerHost,r.requestedByActor,r.requestedBySSO,r.osName,r.errorPreview,
    ].map((v)=>String(v||'').toLowerCase()).some((v)=>v.includes(q)));
  }
  if(state.runsStatus)runs=runs.filter((r)=>normalizeRunStatus(r.status)===normalizeRunStatus(state.runsStatus));
  if(state.selectedPipelineId)runs=runs.filter((r)=>r.pipelineId===state.selectedPipelineId);
  state.runsView=sortRuns(runs);
  if(state.runsOffset>=state.runsView.length)state.runsOffset=0;
}
function applyPipelineFilters(){let items=[...state.pipelinesAll];const risk=document.getElementById('pipelineRiskFilter')?.value||'';if(risk)items=items.filter((p)=>p.riskLevel===risk);if(state.q){const q=state.q.toLowerCase();items=items.filter((p)=>[p.pipelineId,p.name,p.owner].join(' ').toLowerCase().includes(q));}state.pipelinesView=items;if(state.pipelinesOffset>=items.length)state.pipelinesOffset=0;}
function renderAll(){const _safeCall=(fn)=>{try{fn();}catch(e){console.error('renderAll sub-error in '+fn.name+':',e);}};_safeCall(renderOverview);_safeCall(renderPipelineAssetCards);_safeCall(renderQualitySection);_safeCall(renderPipelines);_safeCall(renderRuns);_safeCall(renderLineage);_safeCall(renderInsights);_safeCall(renderOrchestratorSchedules);_safeCall(renderOrchestratorRuns);_safeCall(renderCharts);_safeCall(renderMetricHelp);_safeCall(updateFooter);_safeCall(updateSearchCounter);revealOverseerSurface();}
function renderOverview(){if(!state.overview)return;const stats=document.getElementById('stats');if(stats){stats.innerHTML='';stats.style.display='none';}
const s=state.overview.operationalSignals||{};setText('signalAtRisk',s.atRisk??'-');setText('signalStale',s.stale??'-');setText('signalRegressions',s.regressions??'-');setText('signalVolume',`${Math.round(Number(s.volume?.ratio||1)*100)}%`);setText('signalAtRiskHint',t('hintAtRisk'));setText('signalStaleHint',t('hintStale'));setText('signalRegressionsHint',t('hintRegressions'));setText('signalVolumeHint',t('hintVolume'));
const isCritical=(s.failed||0)>0;const isWarning=(s.atRisk||0)>0&&!(s.failed>0);const hl=document.getElementById('healthHighlight');if(hl){hl.classList.remove('health-ok','health-warning','health-critical');hl.classList.add(isCritical?'health-critical':isWarning?'health-warning':'health-ok');}setText('healthTitle',isCritical?t('healthCrit'):isWarning?t('healthWarn'):t('healthOk'));setText('healthMessage',`${s.pipelineCount||0} pipelines | ${state.overview?.globalKpis?.totalRuns||0} runs | ${t('lastUpdate')} ${fmt(state.overview.generatedAt)}`);
/* Apply signal classes */
document.querySelectorAll('.signal-card').forEach((el)=>{el.classList.remove('signal-good','signal-warning','signal-critical');const sig=el.dataset.signal;const val=Number(sig==='atRisk'?s.atRisk:sig==='stale'?s.stale:sig==='regressions'?s.regressions:0);if(sig==='volume'){const ratio=Number(s.volume?.ratio||1);el.classList.add(ratio<0.5||ratio>2?'signal-critical':ratio<0.7||ratio>1.5?'signal-warning':'signal-good');}else{el.classList.add(val>0?'signal-critical':'signal-good');}});animateOverviewCountersOnce();}
function renderRuns(){const th=document.getElementById('tableHead'),tb=document.getElementById('tableBody');if(!th||!tb)return;th.innerHTML=`<tr>${RUN_COLUMNS.map(([k,lk])=>{const l=t(lk);if(k==='details')return `<th>${l}</th>`;const active=state.runsSortKey===k;const arrow=active?(state.runsSortDir==='asc'?' ↑':' ↓'):'';return `<th data-sort-key="${esc(k)}" class="sortable${active?' sorted':''}" style="cursor:pointer;">${l}${arrow}</th>`;}).join('')}</tr>`;const page=state.runsView.slice(state.runsOffset,state.runsOffset+state.runsLimit);tb.innerHTML=page.map((r)=>`<tr data-run="${r.id}">${RUN_COLUMNS.map(([k,lk])=>`<td data-label="${esc(t(lk))}">${runCell(k,r)}</td>`).join('')}</tr>`).join('');th.querySelectorAll('th[data-sort-key]').forEach((el)=>el.addEventListener('click',()=>toggleRunsSort(el.dataset.sortKey||'')));tb.querySelectorAll('button[data-run]').forEach((btn)=>btn.addEventListener('click',async(e)=>{e.stopPropagation();await openRun(Number(btn.dataset.run));}));setText('pageInfo',page.length?`${state.runsOffset+1}-${state.runsOffset+page.length} de ${state.runsView.length}`:'Sem registos');const prev=document.getElementById('prevPage'),next=document.getElementById('nextPage');if(prev)prev.disabled=state.runsOffset<=0;if(next)next.disabled=state.runsOffset+state.runsLimit>=state.runsView.length;}
function toggleRunsSort(key){if(!key||key==='details')return;if(state.runsSortKey===key){state.runsSortDir=state.runsSortDir==='asc'?'desc':'asc';}else{state.runsSortKey=key;state.runsSortDir='desc';}state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');}
function sortRuns(runs){const sorted=[...runs];const key=state.runsSortKey||'startDate';const dir=state.runsSortDir==='asc'?1:-1;sorted.sort((a,b)=>{const av=getRunSortValue(a,key);const bv=getRunSortValue(b,key);if(typeof av==='number'&&typeof bv==='number'){if(av===bv)return 0;return av>bv?dir:-dir;}const at=String(av??'').toLowerCase();const bt=String(bv??'').toLowerCase();if(at===bt)return 0;return at>bt?dir:-dir;});return sorted;}
function getRunSortValue(run,key){
  if(key==='id')return Number(run.id||0);
  if(key==='startDate'||key==='endDate')return dateValue(run[key]);
  if(key==='durationLabel')return Number(run.execTime||0);
  if(key==='cpuLabel')return Number(run.usageCPU||0);
  if(key==='memLabel')return Number(run.usageMemoria||0);
  if(key==='status')return String(run.status||'');
  if(key==='pipelineId')return String(run.pipelineId||'');
  if(key==='requestedByActor')return String(run.requestedByActor||'');
  if(key==='runnerHost')return String(run.runnerHost||'');
  if(key==='hostname')return String(run.hostname||'');
  if(key==='osName')return String(run.osName||'');
  return String(run[key]||'');
}
function renderInsights(){const o=state.overview;if(!o)return;const immediate=o.topAlerts?.immediate||[],incidents=o.topAlerts?.incidents||[];setHtml('recentFailuresList',listItems(immediate,'status-nok','FAILED'));setHtml('failingPipelinesList',listItems(state.pipelinesView.filter((p)=>p.riskLevel==='critical'),'status-nok','Risco'));setHtml('incidentsTimelineList',listItems(incidents,'status-warning','Incidente'));setHtml('topRegressionsList',listItems(state.pipelinesView.filter((p)=>Number(p.regressionDelta||0)>0),'status-warning','Regressão'));}
function renderOrchestratorSchedules(){const h=document.getElementById('orchPipelinesHead'),b=document.getElementById('orchPipelinesBody');if(!h||!b)return;h.innerHTML='<tr><th>Pipeline</th><th>Owner</th><th>Criticidade</th><th>Schedule</th><th>Permissão</th><th>Ações</th></tr>';b.innerHTML=state.orchestratorPipelines.map((p)=>{const pid=p.pipeline_id||p.pipelineId;const role=getUserRole(pid);const canRun=canUserRunPipeline(pid);const canEdit=role==='owner'||(state.payload?.authz?.app_role||'').toLowerCase()==='admin';const isPaused=(p.schedule||'').toLowerCase()==='paused';const isManual=(p.schedule||'').toLowerCase()==='manual';const isRunning=state.runningPipelines&&state.runningPipelines.has(pid);const runDot=isRunning?'<span class="pipeline-running-dot" title="A executar agora"></span>':'';const scheduleDisplay=isPaused?esc(p.prev_schedule||p.prevSchedule||'—'):esc(p.schedule||'manual');const currentVal=isPaused?(p.prev_schedule||p.prevSchedule||''):((p.schedule||'').toLowerCase()==='manual'?'manual':(p.schedule||''));const presets=[{label:'Manual',value:'manual'},{label:'5 min',value:'*/5 * * * *'},{label:'15 min',value:'*/15 * * * *'},{label:'Hourly',value:'0 * * * *'},{label:'Daily 08:00',value:'0 8 * * *'},{label:'Weekdays 08:00',value:'0 8 * * 1-5'},{label:'Custom...',value:'__custom__'}];const currentPreset=presets.find((p)=>p.value===currentVal);const optionsHtml=presets.map((p)=>`<option value="${esc(p.value)}" ${p.value===currentVal?'selected':''}>${esc(p.label)}</option>`).join('');let pauseBtn='';if(canEdit&&!isManual){if(isPaused){pauseBtn=`<button class="btn-detail btn-resume" data-pause-toggle="${esc(pid)}" data-pause-action="resume" title="Retomar schedule">Resume</button>`;}else{pauseBtn=`<button class="btn-detail btn-pause" data-pause-toggle="${esc(pid)}" data-pause-action="pause" title="Pausar schedule">Pause</button>`;}}return `<tr class="${isPaused?'row-paused':''}"><td data-label="Pipeline">${runDot}${esc(pid)}</td><td data-label="Owner">${canEdit ? `<select class="schedule-select" style="min-width:120px" data-owner-pipeline="${esc(pid)}"><option value="unknown" ${!p.owner || p.owner==='unknown'?'selected':''}>unknown</option>${maiatronUsers.map(u => `<option value="${esc(u.username)}" ${p.owner===u.username?'selected':''}>${esc(u.username)}</option>`).join('')}</select>` : esc(p.owner||'unknown')}</td><td data-label="Criticidade">${canEdit ? `<select class="schedule-select" style="min-width:120px" data-crit-pipeline="${esc(pid)}">${['low','medium','high','critical'].map(c => `<option value="${c}" ${(p.criticality||'medium')===c?'selected':''}>${c}</option>`).join('')}</select>` : esc(p.criticality||'medium')}</td><td data-label="Schedule"><div class="schedule-cell">${canEdit&&!isPaused?`<select class="schedule-select${isPaused?' schedule-paused':''}" data-schedule-pipeline="${esc(pid)}">${optionsHtml}</select>`:`<span class="schedule-display">${scheduleDisplay}</span>`}${isPaused?'<span class="schedule-paused-label">PAUSED</span>':''}${canEdit&&!isPaused?`<button class="btn-detail btn-schedule-save" data-schedule-save="${esc(pid)}">Guardar</button>`:''}</div></td><td data-label="Permissão"><span class="role-badge role-${esc(role)}">${esc(role)}</span></td><td data-label="Ações">${pauseBtn} <button class="btn-detail" data-orch-action="trigger" data-pipeline="${esc(pid)}" ${canRun?'':'disabled title="Sem permissão — contacta o owner"'}>Run now</button> <button class="btn-detail" data-orch-action="copy" data-pipeline="${esc(pid)}">Copiar cmd</button></td></tr>`;}).join('');b.querySelectorAll('button[data-orch-action]').forEach((btn)=>btn.addEventListener('click',async()=>{await handleOrchestratorAction(btn.dataset.orchAction,btn.dataset.pipeline);}));b.querySelectorAll('button[data-schedule-save]').forEach((btn)=>btn.addEventListener('click',()=>{const pid=btn.dataset.scheduleSave;const sel=b.querySelector(`select[data-schedule-pipeline="${pid}"]`);if(sel){let val=sel.value;if(val==='__custom__'){val=prompt('Enter cron expression (or leave blank for Manual):','');if(val===null)return;val=val.trim()||'manual';}handleConfigChange(pid,val, b.querySelector(`select[data-owner-pipeline="${pid}"]`)?.value, b.querySelector(`select[data-crit-pipeline="${pid}"]`)?.value);}else{const inp=b.querySelector(`input[data-schedule-pipeline="${pid}"]`);if(inp)handleConfigChange(pid,inp.value.trim(), b.querySelector(`select[data-owner-pipeline="${pid}"]`)?.value, b.querySelector(`select[data-crit-pipeline="${pid}"]`)?.value);}}));b.querySelectorAll('select[data-schedule-pipeline]').forEach((sel)=>sel.addEventListener('change',()=>{let val=sel.value;if(val==='__custom__'){const inp=prompt('Enter cron expression (or leave blank for Manual):','');if(inp===null){sel.value=sel.getAttribute('data-previous-value')||'manual';return;}val=inp.trim()||'manual';}sel.setAttribute('data-previous-value',val);}));b.querySelectorAll('button[data-pause-toggle]').forEach((btn)=>btn.addEventListener('click',()=>{handlePauseToggle(btn.dataset.pauseToggle,btn.dataset.pauseAction);}));}
function renderOrchestratorRuns(){const h=document.getElementById('orchRunsHead'),b=document.getElementById('orchRunsBody');if(!h||!b)return;h.innerHTML='<tr><th>Pipeline</th><th>Status</th><th>Criado em</th><th>Origem</th></tr>';const page=state.orchRuns.slice(state.orchOffset,state.orchOffset+state.orchLimit);b.innerHTML=page.map((item)=>{const r=normalizeOrchestratorRow(item);const status=normalizeOrchestratorStatus(r.status);const source=r.delivery==='copied_cli'?'cli-copy':(r.source||r.triggerType||'frontend');return `<tr><td data-label="Pipeline">${esc(r.pipelineId||r.pipeline_id||'-')}</td><td data-label="Status"><span class="status-pill ${orchestratorStatusClass(status)}">${esc(status)}</span></td><td data-label="Criado em">${esc(fmt(r.createdAt||r.requested_at))}</td><td data-label="Origem">${esc(source)}</td></tr>`;}).join('');setText('orchPageInfo',page.length?`${state.orchOffset+1}-${state.orchOffset+page.length} de ${state.orchRuns.length}`:'Sem registos');const prev=document.getElementById('orchPrevPage'),next=document.getElementById('orchNextPage');if(prev)prev.disabled=state.orchOffset<=0;if(next)next.disabled=state.orchOffset+state.orchLimit>=state.orchRuns.length;}
async function handleOrchestratorAction(action,pipelineId){const by=state.user?.username||'frontend';if(action==='trigger'&&!canUserRunPipeline(pipelineId)){showToast(t('noPerm'),'error');return;}const cmd=`python orchestrator.py trigger enqueue ${pipelineId} --by ${by}`;if(action==='copy'){await copyText(cmd);showToast(t('copied'),'success');return;}if(action==='trigger'){const trigger={trigger_id:newTriggerId(),pipeline_id:pipelineId,requested_by:by,requested_by_sso:by,requested_at:new Date().toISOString(),source:'frontend',status:'queued',delivery:'delivered',notes:'Run now solicitado no frontend',command:cmd};let apiResp=null;try{apiResp=await writeRunNowTrigger(trigger);}catch{}const delivered=!!(apiResp&&(apiResp.status==='ok'||apiResp.ok===true));if(delivered){trigger.requested_by=apiResp.requested_by_actor||trigger.requested_by;trigger.requested_by_sso=apiResp.requested_by_sso||trigger.requested_by_sso;showToast(t('triggerOk'),'success');}else{trigger.delivery='copied_cli';trigger.source='frontend-cli-copy';await copyText(cmd);showToast(t('triggerFail'),'warning');}pushLocalTrigger(trigger);addInflight(pipelineId,trigger.trigger_id);const inflightRow=normalizeOrchestratorRow({runId:trigger.trigger_id,pipelineId,status:'running',source:'frontend',createdAt:trigger.requested_at});state.orchRuns=[inflightRow,...state.orchRuns];if(!state.runningPipelines)state.runningPipelines=new Set();state.runningPipelines.add(pipelineId);renderOrchestratorSchedules();renderOrchestratorRuns();}}
/* === v3.0 New functions: Pipeline asset cards, Quality section, Drawer, Search counter === */
function freshnessLevel(hours){if(hours==null||hours<0)return 'paused';if(hours<1)return 'fresh';if(hours<6)return 'ok';if(hours<24)return 'stale';return 'critical';}
function freshnessLabel(hours){if(hours==null||hours<0)return 'Paused';if(hours<1)return `${Math.round(hours*60)}m`;if(hours<24)return `${Math.round(hours)}h`;return `${Math.round(hours/24)}d`;}
function qualityGateLevel(rate){if(rate>=95)return 'pass';if(rate>=80)return 'warn';return 'fail';}
function qualityGateLabel(rate){if(rate>=95)return 'Pass';if(rate>=80)return 'Warning';return 'Fail';}
function cronToHuman(expr){if(!expr)return 'Manual';const s=expr.trim().toLowerCase();if(s==='paused')return 'Paused';if(s==='manual')return 'Manual';const parts=s.split(/\s+/);if(parts.length<5)return expr;const [min,h,dom,mon,dow]=parts;if(min==='*'&&h==='*')return 'Cada minuto';if(min.startsWith('*/')&&h==='*')return `A cada ${min.slice(2)} min`;if(h==='*'&&dom==='*')return `${min}' de cada hora`;if(dom==='*'&&mon==='*'&&dow==='*')return `${h}:${min.padStart(2,'0')} diário`;return expr;}
function renderPipelineAssetCards(){const c=document.getElementById('pipelineAssetCards');if(!c)return;if(!state.pipelinesAll.length&&!state.orchestratorPipelines.length){c.innerHTML='';return;}
const allPipelines=state.pipelinesAll.length?state.pipelinesAll:state.orchestratorPipelines.map((p)=>({pipelineId:p.pipeline_id||p.pipelineId,name:p.name||p.pipeline_id||p.pipelineId,owner:p.owner||'unknown',lastRun:null,lastStatus:'UNKNOWN',successRate7d:100,staleHours:null,riskScore:0,riskLevel:'low'}));
/* Dashboard: show only the 2 most recent pipelines (by lastRun) */
const pipelines=[...allPipelines].sort((a,b)=>{const da=a.lastRun?dateValue(a.lastRun):0;const db=b.lastRun?dateValue(b.lastRun):0;return db-da;}).slice(0,2);
c.innerHTML=pipelines.map((p)=>{const cat=state.orchestratorPipelines.find((cp)=>(cp.pipeline_id||cp.pipelineId)===p.pipelineId);const schedule=cat?.schedule||'manual';const isPaused=schedule.toLowerCase()==='paused';const hrs=p.staleHours!=null?p.staleHours:(p.lastRun?Math.floor((Date.now()-dateValue(p.lastRun))/3600000):null);const fl=isPaused?'paused':freshnessLevel(hrs);const sr=Number(p.successRate7d||100);const qg=qualityGateLevel(sr);const hue=hashPipelineHue(p.pipelineId);
/* Sparkline: last 2 runs for this pipeline */
const pipeRuns=(state.runsAll||[]).filter((r)=>r.pipelineId===p.pipelineId).slice(0,2).reverse();
const sparkHtml=pipeRuns.length?pipeRuns.map((r)=>{const s=normalizeRunStatus(r.status);const cls=s==='OK'?'spark-ok':s==='WARNING'?'spark-warning':'spark-nok';const h=s==='OK'?'100':s==='WARNING'?'65':'40';return `<div class="spark-bar ${cls}" style="height:${h}%"></div>`;}).join(''):'<div class="spark-bar spark-empty" style="height:30%"></div>'.repeat(2);
return `<article class="pipeline-asset-card" style="border-left-color:hsl(${hue},70%,55%);">
<div class="pac-header"><div><div class="pac-name">${esc(p.name||p.pipelineId)}</div><div class="pac-id">${esc(p.pipelineId)}</div><div class="pac-owner">${t('owner')}: ${esc(p.owner)}</div></div><div class="pac-sparkline">${sparkHtml}</div></div>
<div class="pac-pills">
<span class="status-pill ${p.lastStatus==='OK'?'status-ok':p.lastStatus==='WARNING'?'status-warning':'status-nok'}">${esc(p.lastStatus||'N/A')}</span>
<span class="freshness-pill freshness-${fl}">${fl==='paused'?'Paused':'Fresh: '+freshnessLabel(hrs)}</span>
<span class="qg-pill qg-${qg}">QG: ${qualityGateLabel(sr)} (${sr.toFixed(0)}%)</span>
<span class="schedule-pill${isPaused?' schedule-pill--paused':''}">${cronToHuman(isPaused?(cat?.prev_schedule||cat?.prevSchedule||schedule):schedule)}</span>
</div>
<div class="pac-metrics">
<div class="pac-metric"><span class="pac-metric-label">${t('riskLabel')}</span><span class="pac-metric-value"><span class="risk-pill risk-${esc(p.riskLevel)}">${esc(p.riskLevel)}</span></span></div>
<div class="pac-metric"><span class="pac-metric-label">${t('success7dLabel')}</span><span class="pac-metric-value">${sr.toFixed(1)}%</span></div>
<div class="pac-metric"><span class="pac-metric-label">${t('staleLabel')}</span><span class="pac-metric-value">${hrs!=null?freshnessLabel(hrs):'N/A'}</span></div>
</div>
</article>`;}).join('');
c.querySelectorAll('.pipeline-asset-card').forEach((el,i)=>{el.addEventListener('click',()=>{const pid=pipelines[i]?.pipelineId;if(!pid)return;state.selectedPipelineId=pid;state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');});});
}
function renderQualitySection(){const c=document.getElementById('qualitySection');if(!c||!state.overview)return;
const kpis=state.overview.globalKpis||{};const allPipelines=state.pipelinesAll||[];
/* Dashboard: show only the 2 most recent pipelines in freshness/quality */
const pipelines=[...allPipelines].sort((a,b)=>{const da=a.lastRun?dateValue(a.lastRun):0;const db=b.lastRun?dateValue(b.lastRun):0;return db-da;}).slice(0,2);
/* Freshness bars */
const freshRows=pipelines.map((p)=>{const cat=state.orchestratorPipelines.find((cp)=>(cp.pipeline_id||cp.pipelineId)===p.pipelineId);const isPaused=(cat?.schedule||'').toLowerCase()==='paused';const hrs=p.staleHours!=null?p.staleHours:(p.lastRun?Math.floor((Date.now()-dateValue(p.lastRun))/3600000):null);const fl=isPaused?'paused':freshnessLevel(hrs);const pct=isPaused?20:hrs==null?0:Math.min(100,Math.max(5,100-Math.min(hrs/48*100,100)));return `<div class="freshness-bar-item"><span class="freshness-bar-label" title="${esc(p.pipelineId)}">${esc(p.name||p.pipelineId)}</span><div class="freshness-bar-track"><div class="freshness-bar-fill fb-${fl}" style="width:${pct}%"></div></div><span class="freshness-bar-value">${hrs!=null?freshnessLabel(hrs):(isPaused?'Paused':'N/A')}</span></div>`;}).join('');
/* Efficiency */
const avgExec=Number(kpis.avgExecTime||0);const p95Exec=Number(kpis.p95ExecTime||0);const effRatio=p95Exec>0?Math.min(100,Math.round((avgExec/p95Exec)*100)):100;const effPct=Math.min(100,effRatio);
/* Quality gates summary — count ALL pipelines, not just the 2 displayed */
const qgPass=allPipelines.filter((p)=>qualityGateLevel(Number(p.successRate7d||100))==='pass').length;const qgWarn=allPipelines.filter((p)=>qualityGateLevel(Number(p.successRate7d||100))==='warn').length;const qgFail=allPipelines.filter((p)=>qualityGateLevel(Number(p.successRate7d||100))==='fail').length;
c.innerHTML=`
<article class="quality-card"><h4>${t('freshness')}</h4><div class="qc-meta">Última execução por pipeline</div><div class="freshness-bar-wrap">${freshRows||'<span class="muted">Sem pipelines</span>'}</div></article>
<article class="quality-card"><h4>${t('qualityGates')}</h4><div class="qc-meta">Checks por threshold de success rate</div><div class="pac-pills" style="margin-top:4px"><span class="qg-pill qg-pass">Pass: ${qgPass}</span><span class="qg-pill qg-warn">Warning: ${qgWarn}</span><span class="qg-pill qg-fail">Fail: ${qgFail}</span></div><div class="qc-meta" style="margin-top:8px">${allPipelines.length} pipeline(s) avaliados | Threshold: Pass >= 95%, Warning >= 80%, Fail < 80%</div></article>
<article class="quality-card"><h4>${t('execEfficiency')}</h4><div class="qc-meta">Tempo médio vs P95</div><div class="efficiency-row"><div class="efficiency-ring" style="--eff-pct:${effPct}%"><div class="efficiency-ring-inner">${effRatio}%</div></div><div class="efficiency-metrics"><span>Avg: <strong>${avgExec.toFixed(1)}s</strong></span><span>P95: <strong>${p95Exec.toFixed(1)}s</strong></span><span>Ratio: <strong>${p95Exec>0?(p95Exec/Math.max(avgExec,0.1)).toFixed(1)+'x':'N/A'}</strong></span>${p95Exec>3*avgExec&&avgExec>0?'<span style="color:#f59e0b;font-size:0.72rem">&#9888; P95 elevado — possível lentidão intermitente</span>':''}</div></div></article>`;
}
function toggleMetricsDrawer(){const d=document.getElementById('metricsDrawer');const o=document.getElementById('metricsDrawerOverlay');if(!d)return;const isOpen=d.classList.contains('open');if(isOpen){closeMetricsDrawer();}else{d.classList.add('open');o?.classList.add('open');d.setAttribute('aria-hidden','false');}}
function closeMetricsDrawer(){const d=document.getElementById('metricsDrawer');const o=document.getElementById('metricsDrawerOverlay');d?.classList.remove('open');o?.classList.remove('open');d?.setAttribute('aria-hidden','true');}
function updateSearchCounter(){const el=document.getElementById('searchCounter');if(!el)return;if(!state.q){el.textContent='';el.classList.remove('active');return;}const total=state.runsView.length+state.pipelinesView.length;el.textContent=`${total} resultado${total!==1?'s':''}`;el.classList.add('active');}
function highlightText(text,query){if(!query||!text)return esc(text);const escaped=esc(text);const qEsc=query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');try{return escaped.replace(new RegExp(`(${qEsc})`,'gi'),'<mark class="search-hl">$1</mark>');}catch{return escaped;}}

function renderCharts(){if(typeof Chart==='undefined'||!state.runsAll.length||!state.overview)return;ensureChartZoomPlugin();const chartReason=historyChart||healthChart?'major':'initial';const chartAnimation=window.MaiatronMotion?.selectiveChartAnimation?.(chartReason)??false;const chartUpdateMode=window.MaiatronMotion?.selectiveChartUpdateMode?.(chartReason)??'none';const buckets=bucketBy(state.runsAll,state.historyGranularity),labels=Object.keys(buckets),values=Object.values(buckets);const s=state.overview.operationalSignals,donut=[Math.max((s.pipelineCount||0)-(s.failed||0)-(s.atRisk||0),0),s.atRisk||0,s.failed||0];const cv=document.getElementById('runsHistoryChart');let barBg='rgba(0,212,255,0.55)';if(cv){const gx=cv.getContext('2d');const gr=gx.createLinearGradient(0,0,0,cv.parentElement?.clientHeight||200);gr.addColorStop(0,'rgba(0,212,255,0.7)');gr.addColorStop(1,'rgba(0,212,255,0.10)');barBg=gr;}const histCfg={type:'bar',data:{labels,datasets:[{label:t('chartHistory'),data:values,backgroundColor:barBg,borderColor:'rgba(0,212,255,0.9)',borderWidth:1,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,animation:chartAnimation,plugins:{legend:{display:false},zoom:{pan:{enabled:true,mode:'x'},zoom:{mode:'x',wheel:{enabled:true},pinch:{enabled:true},drag:{enabled:false}},limits:{x:{minRange:4}}}},scales:{x:{grid:{display:false},ticks:{maxTicksLimit:10,font:{size:10},color:'rgba(200,200,200,0.6)'}},y:{beginAtZero:true,grid:{color:'rgba(255,255,255,0.05)'},ticks:{font:{size:10},color:'rgba(200,200,200,0.6)'}}}}};
const donutCfg={type:'doughnut',data:{labels:[t('healthy'),t('attention'),t('failed')],datasets:[{data:donut,backgroundColor:['rgba(34,197,94,0.85)','rgba(245,158,11,0.85)','rgba(239,68,68,0.9)'],borderWidth:0,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,animation:chartAnimation,cutout:'65%',plugins:{legend:{display:false}}}};historyChart=upsertChart(historyChart,'runsHistoryChart',histCfg,chartUpdateMode);healthChart=upsertChart(healthChart,'successRateChart',donutCfg,chartUpdateMode);mountDashboardChartControls();const sr=Number(state.overview.globalKpis?.successRate||0);const pctEl=document.getElementById('donutPct');if(pctEl)pctEl.textContent=sr.toFixed(1)+'%';const dlbl=document.querySelector('.donut-label');if(dlbl)dlbl.textContent=t('healthLabel');revealOverseerSurface();}
function upsertChart(ex,id,cfg,updateMode='none'){const cv=document.getElementById(id);if(!cv)return ex;if(!ex)return new Chart(cv.getContext('2d'),cfg);ex.data=cfg.data;ex.options=cfg.options;ex.update(updateMode||'none');return ex;}
function ensureChartZoomPlugin(){if(zoomPluginRegistered||typeof Chart==='undefined')return;const candidate=window.ChartZoom||window['chartjs-plugin-zoom']||window.ChartZoomPlugin||null;if(!candidate||typeof Chart.register!=='function')return;try{Chart.register(candidate);zoomPluginRegistered=true;}catch(_err){zoomPluginRegistered=false;}}
function getDashboardChartById(chartId){if(chartId==='runsHistoryChart')return historyChart;if(chartId==='successRateChart')return healthChart;return null;}
function applyDashboardChartZoomIn(chartId=''){const chart=getDashboardChartById(chartId);if(chart)chart.zoom?.(1.2);}
function applyDashboardChartZoomOut(chartId=''){const chart=getDashboardChartById(chartId);if(chart)chart.zoom?.(0.8);}
function resetDashboardChartZoom(chartId=''){const chart=getDashboardChartById(chartId);if(chart)chart.resetZoom?.();}
function cloneChartPayload(value,fallback){if(typeof structuredClone==='function'){try{return structuredClone(value);}catch(_err){}}try{return JSON.parse(JSON.stringify(value));}catch(_err){return fallback;}}
function isChartExpandOpen(){const modal=document.getElementById('chartExpandModal');return !!(modal&&modal.classList.contains('open'));}
function getFocusableInChartExpandModal(){const dialog=document.querySelector('#chartExpandModal .chart-expand-dialog');if(!dialog)return[];const selector=['button:not([disabled])','a[href]','input:not([disabled])','select:not([disabled])','textarea:not([disabled])','[tabindex]:not([tabindex=\"-1\"])'].join(',');return Array.from(dialog.querySelectorAll(selector)).filter((node)=>node.offsetParent!==null||node===document.activeElement);}
function trapChartExpandModalFocus(event){if(!isChartExpandOpen()||event.key!=='Tab')return;const focusables=getFocusableInChartExpandModal();if(!focusables.length)return;const first=focusables[0],last=focusables[focusables.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
function closeExpandedChartModal(options={}){const restoreFocus=options.restoreFocus!==false;if(expandedChartInstance){try{expandedChartInstance.destroy();}catch(_err){}expandedChartInstance=null;}expandedChartSourceId=null;const modal=document.getElementById('chartExpandModal');if(modal){modal.classList.remove('open');modal.setAttribute('aria-hidden','true');}document.body.classList.remove('chart-expand-open');if(restoreFocus&&expandedChartTriggerEl&&typeof expandedChartTriggerEl.focus==='function'){try{expandedChartTriggerEl.focus();}catch(_err){}}expandedChartTriggerEl=null;}
function openExpandedChartModal(chartId,triggerEl=null){if(!chartId||typeof Chart==='undefined'){showToast('Gráfico indisponível para ampliar.','warning');return;}const sourceChart=getDashboardChartById(chartId);const canvas=document.getElementById('chartExpandCanvas');if(!sourceChart||!canvas){showToast('Gráfico ainda não está pronto.','warning');return;}closeExpandedChartModal({restoreFocus:false});const chartCard=sourceChart.canvas?.closest?.('.chart-card');const chartTitle=chartCard?.querySelector('.chart-header h3')?.textContent?.trim()||'Gráfico';const titleNode=document.getElementById('chartExpandTitle');if(titleNode)titleNode.textContent=chartTitle;const clonedData=cloneChartPayload(sourceChart.data,{datasets:[]});const clonedOptions=cloneChartPayload(sourceChart.options,{});clonedOptions.responsive=true;clonedOptions.maintainAspectRatio=false;clonedOptions.animation=false;const ctx=canvas.getContext('2d');if(!ctx){showToast('Não foi possível abrir o gráfico ampliado.','error');return;}expandedChartInstance=new Chart(ctx,{type:sourceChart.config?.type||'line',data:clonedData,options:clonedOptions});expandedChartSourceId=chartId;expandedChartTriggerEl=triggerEl||document.activeElement||null;const modal=document.getElementById('chartExpandModal');if(modal){modal.classList.add('open');modal.setAttribute('aria-hidden','false');}document.body.classList.add('chart-expand-open');window.requestAnimationFrame(()=>{expandedChartInstance?.resize?.();document.getElementById('chartExpandCloseBtn')?.focus?.();});}
function bindChartExpandModal(){if(state._chartExpandModalBound)return;state._chartExpandModalBound=true;const modal=document.getElementById('chartExpandModal');const closeBtn=document.getElementById('chartExpandCloseBtn');if(!modal)return;closeBtn?.addEventListener('click',()=>closeExpandedChartModal());modal.addEventListener('click',(event)=>{if(event.target===modal)closeExpandedChartModal();});document.addEventListener('keydown',trapChartExpandModalFocus);window.addEventListener('resize',()=>{if(expandedChartInstance&&isChartExpandOpen())expandedChartInstance.resize();});}
function mountDashboardChartControls(){const chartCanvases=Array.from(document.querySelectorAll('#dashboardView .chart-card canvas[id]'));chartCanvases.forEach((canvas)=>{const chartId=canvas.id;const card=canvas.closest('.chart-card');const header=card?.querySelector('.chart-header');if(!header)return;if(header.querySelector(`.chart-zoom-controls[data-chart-id=\"${chartId}\"]`))return;const controls=document.createElement('div');controls.className='chart-zoom-controls';controls.dataset.chartId=chartId;const isTimeSeries=DASHBOARD_TIME_SERIES_CHART_IDS.includes(chartId);controls.innerHTML=[isTimeSeries?`<button type=\"button\" class=\"theme-btn chart-zoom-btn chart-zoom-btn-icon\" data-zoom-action=\"out\" data-chart-id=\"${chartId}\" title=\"Zoom out\" aria-label=\"Zoom out\">-</button><button type=\"button\" class=\"theme-btn chart-zoom-btn chart-zoom-btn-icon\" data-zoom-action=\"in\" data-chart-id=\"${chartId}\" title=\"Zoom in\" aria-label=\"Zoom in\">+</button><button type=\"button\" class=\"theme-btn chart-zoom-btn\" data-zoom-action=\"reset\" data-chart-id=\"${chartId}\" title=\"Reset zoom\" aria-label=\"Reset zoom\">Reset</button>`:'',`<button type=\"button\" class=\"theme-btn chart-zoom-btn chart-expand-btn\" data-zoom-action=\"expand\" data-chart-id=\"${chartId}\" title=\"Ampliar gráfico\" aria-label=\"Ampliar gráfico\">Ampliar</button>`].join('');header.appendChild(controls);});}
function bindDashboardChartControls(){if(chartControlsBound)return;chartControlsBound=true;mountDashboardChartControls();document.addEventListener('click',(event)=>{const btn=event.target.closest('.chart-zoom-btn[data-zoom-action][data-chart-id]');if(!btn)return;event.preventDefault();const chartId=btn.dataset.chartId||'';const action=btn.dataset.zoomAction||'';if(!chartId||!action)return;if(action==='in'){applyDashboardChartZoomIn(chartId);}else if(action==='out'){applyDashboardChartZoomOut(chartId);}else if(action==='reset'){resetDashboardChartZoom(chartId);}else if(action==='expand'){openExpandedChartModal(chartId,btn);}});}
function renderMetricHelp(){document.querySelectorAll("[data-signal='atRisk']")?.forEach((el)=>{el.title=t('hintAtRisk');});document.querySelectorAll("[data-signal='stale']")?.forEach((el)=>{el.title=t('hintStale');});document.querySelectorAll("[data-signal='regressions']")?.forEach((el)=>{el.title=t('hintRegressions');});document.querySelectorAll("[data-signal='volume']")?.forEach((el)=>{el.title=t('hintVolume');});}
function updateFooter(){
  const generatedAt = state.payload?.generated_at || state.overview?.generatedAt || state.healthStatus?.status?.generated_at || null;
  setText('lastUpdateTime',fmt(generatedAt));
  setText('lastUpdateRuns',`${state.runsAll.length} runs | ${state.runsView.length} filtrados`);
  setText('headerUpdateTime',fmt(generatedAt));
  renderDataFeedStatus();
}

function renderDataFeedStatus() {
  const host = document.getElementById('headerDataFeedState');
  const textNode = host?.querySelector('.data-feed-text');
  if (!host || !textNode) return;

  const generatedAt = state.payload?.generated_at
    || state.overview?.generatedAt
    || state.healthStatus?.status?.generated_at
    || state.healthStatus?.files?.full_mtime
    || null;

  const modeRaw = state.healthStatus?.runtime_hints?.mode
    || state.healthStatus?.status?.db_connectivity?.overseer?.mode
    || state.healthStatus?.status?.db_connectivity?.overseer?.requested_mode
    || 'n/a';
  const mode = String(modeRaw || 'n/a').toUpperCase();

  const dbReachable = state.healthStatus?.db_reachability?.overseer_api_db;
  const staleMs = Number(CONFIG.dataStaleMs || 180000);
  const generatedTs = generatedAt ? dateValue(generatedAt) : 0;
  const ageMs = generatedTs > 0 ? Math.max(0, Date.now() - generatedTs) : null;

  let stateClass = 'is-unknown';
  let label = `DB ${mode} · sem dados`;

  if (dbReachable === false) {
    stateClass = 'is-critical';
    label = `DB ${mode} · indisponível`;
  } else if (ageMs != null) {
    if (ageMs > staleMs) {
      stateClass = 'is-stale';
      label = `DB ${mode} · stale`;
    } else {
      stateClass = 'is-fresh';
      label = `DB ${mode} · fresco`;
    }
  }

  host.classList.remove('is-fresh', 'is-stale', 'is-critical', 'is-unknown');
  host.classList.add(stateClass);
  textNode.textContent = label;

  const tip = [
    `Modo DB: ${mode}`,
    `Snapshot: ${generatedAt ? fmt(generatedAt) : '-'}`,
    `Reachability: ${dbReachable === false ? 'erro' : 'ok'}`,
    ageMs != null ? `Idade: ${Math.round(ageMs / 1000)}s` : null,
  ].filter(Boolean).join(' | ');
  host.title = tip;
}
function switchView(viewId){if(!viewId)return;const applyView=()=>{state.activeView=viewId||state.activeView||'dashboardView';document.querySelectorAll('.nav-tab').forEach((b)=>b.classList.toggle('active',b.dataset.view===viewId));document.querySelectorAll('.view').forEach((v)=>v.classList.toggle('active',v.id===viewId));document.body.classList.toggle('dash-lock',viewId==='dashboardView');if(viewId==='dashboardView')setTimeout(()=>{historyChart?.resize?.();healthChart?.resize?.();mountDashboardChartControls();revealOverseerSurface();},60);else{closeExpandedChartModal({restoreFocus:false});revealOverseerSurface();}};if(window.MaiatronMotion&&typeof window.MaiatronMotion.swap==='function'){void window.MaiatronMotion.swap(applyView,{root:document.getElementById('mainApp')||document,selectors:'.view.active > *, .signal-card, .chart-card, .list-card, .metric-card, .run-row, .pipeline-row'});return;}applyView();}
function showMainApp(){resolveInitialAuthGate();document.getElementById('accessDeniedScreen')?.classList.add('hidden');document.getElementById('loginScreen')?.classList.add('hidden');document.getElementById('mainApp')?.classList.remove('hidden');setText('userName',state.user?.displayName||state.user?.username||'admin');window.MaiatronAuthUI?.syncFromServer({configUrl:CONFIG.authConfigUrl});}
function showLoginScreen(){resolveInitialAuthGate();document.getElementById('accessDeniedScreen')?.classList.add('hidden');document.getElementById('mainApp')?.classList.add('hidden');document.getElementById('loginScreen')?.classList.remove('hidden');window.MaiatronAuthUI?.setSession(null);}
function showAccessDeniedScreen(reason){resolveInitialAuthGate();document.getElementById('mainApp')?.classList.add('hidden');document.getElementById('loginScreen')?.classList.add('hidden');document.getElementById('accessDeniedScreen')?.classList.remove('hidden');const node=document.getElementById('accessDeniedReason');if(node){node.textContent=reason||'A tua sessão está ativa, mas sem acesso a esta app.';}}
function getSystemTheme(){return window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';}function initTheme(){applyTheme(localStorage.getItem(CONFIG.themeKey)||'dark');window.matchMedia('(prefers-color-scheme: light)').addEventListener('change',function(){if(localStorage.getItem(CONFIG.themeKey)==='auto')applyTheme('auto');});}
function onToggleTheme(){var curr=localStorage.getItem(CONFIG.themeKey)||'dark';var next=curr==='dark'?'light':curr==='light'?'auto':'dark';applyTheme(next);}function applyTheme(t){var resolved=t==='auto'?getSystemTheme():t;if(resolved==='light')document.documentElement.setAttribute('data-theme','light');else document.documentElement.removeAttribute('data-theme');localStorage.setItem(CONFIG.themeKey,t);document.querySelectorAll('.theme-btn').forEach(function(btn){btn.setAttribute('data-theme-mode',t);btn.setAttribute('title',t==='auto'?'Tema: Auto (sistema)':t==='light'?'Tema: Claro':'Tema: Escuro');});}
function loadTriggerHistory(){try{const raw=localStorage.getItem(CONFIG.triggerKey);let items=raw?JSON.parse(raw):[];const cutoff=Date.now()-7*86400000;items=items.filter((r)=>{const t=dateValue(r.createdAt||r.requested_at||r.requestedAt);return !t||t>=cutoff;}).slice(0,50);state.triggerHistory=items.map((r)=>normalizeOrchestratorRow(r));localStorage.setItem(CONFIG.triggerKey,JSON.stringify(items));}catch{state.triggerHistory=[];}return state.triggerHistory;}
function pushLocalTrigger(trigger){loadTriggerHistory();const rec=normalizeOrchestratorRow({...trigger,runId:trigger.trigger_id,pipelineId:trigger.pipeline_id,createdAt:trigger.requested_at,updated_at:new Date().toISOString()});state.triggerHistory.unshift(rec);localStorage.setItem(CONFIG.triggerKey,JSON.stringify(state.triggerHistory.slice(0,200)));}
function loadInflight(){try{const raw=localStorage.getItem(CONFIG.inflightKey);return raw?JSON.parse(raw):[];}catch{return [];}}
function saveInflight(items){try{localStorage.setItem(CONFIG.inflightKey,JSON.stringify((items||[]).slice(0,50)));}catch{}}
function addInflight(pipelineId,triggerId){const items=loadInflight();items.unshift({pipelineId,triggerId,startedAt:Date.now()});saveInflight(items);}
function pruneInflight(dbRuns){const items=loadInflight();const now=Date.now();const TIMEOUT_MS=30*60*1000;const kept=[];for(const entry of items){if(now-entry.startedAt>TIMEOUT_MS)continue;const matched=dbRuns.find((r)=>{const rPid=r.pipelineId||r.pipeline_id||'';const rDate=dateValue(r.createdAt||r.created_at||r.started_at);const rStatus=normalizeOrchestratorStatus(r.status);const isTerminal=rStatus==='consumed'||rStatus==='failed'||r.status==='success'||r.status==='warning';return rPid===entry.pipelineId&&rDate>=entry.startedAt&&isTerminal;});if(!matched)kept.push(entry);}saveInflight(kept);return kept;}
async function copyText(t){try{await navigator.clipboard.writeText(t);}catch{}}
async function writeRunNowTrigger(trigger){try{return await apiPost('trigger_enqueue',{pipeline_id:trigger?.pipeline_id,trigger_id:trigger?.trigger_id,runner_host:trigger?.runner_host||'any',notes:trigger?.notes||''});}catch(e){if(handleAuthApiError(e))return null;console.error('writeRunNowTrigger error:',e);showToast(e?.message||'Erro no trigger','error');return null;}}
function newTriggerId(){if(window.crypto?.randomUUID)return window.crypto.randomUUID();return `trg-${Date.now()}-${Math.floor(Math.random()*1000000)}`;}function normalizeTriggerAsRun(trigger){return normalizeOrchestratorRow({runId:trigger.triggerId||trigger.trigger_id||trigger.triggerLocalId||trigger.trigger_local_id,pipelineId:trigger.pipelineId||trigger.pipeline_id,status:trigger.status,source:trigger.source||'trigger_db',createdAt:trigger.requestedAt||trigger.requested_at,requested_at:trigger.requestedAt||trigger.requested_at,delivery:'delivered'});}function normalizeOrchestratorRow(row){const copy={...(row||{})};copy.runId=copy.runId||copy.triggerId||copy.trigger_id||copy.triggerLocalId||copy.trigger_local_id||'-';copy.pipelineId=copy.pipelineId||copy.pipeline_id||'-';copy.status=normalizeOrchestratorStatus(copy.status);copy.createdAt=copy.createdAt||copy.requestedAt||copy.requested_at||null;copy.source=copy.source||copy.triggerSource||copy.triggerType||'frontend';copy.delivery=copy.delivery||null;return copy;}function normalizeOrchestratorStatus(value){const raw=String(value||'queued').toLowerCase();if(raw.includes('fail')||raw.includes('error'))return 'failed';if(raw.includes('success')||raw.includes('consume'))return 'consumed';if(raw.includes('run')||raw.includes('claim'))return 'running';if(raw.includes('queue')||raw.includes('pend'))return 'queued';return raw;}function orchestratorStatusClass(status){if(status==='failed')return 'status-nok';if(status==='consumed')return 'status-ok';if(status==='running')return 'status-running';return 'status-warning';}
function bucketBy(rows,g){const out={};for(const r of rows){if(!r.startDate)continue;const d=new Date(r.startDate);if(Number.isNaN(d.getTime()))continue;let k;if(g==='hour')k=d.toISOString().slice(0,13);else if(g==='week')k=`${d.getUTCFullYear()}-W${weekOfYear(d)}`;else if(g==='month')k=d.toISOString().slice(0,7);else k=d.toISOString().slice(0,10);out[k]=(out[k]||0)+1;}return out;}
function weekOfYear(date){const d=new Date(Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate()));d.setUTCDate(d.getUTCDate()+4-(d.getUTCDay()||7));const ys=new Date(Date.UTC(d.getUTCFullYear(),0,1));return Math.ceil((((d-ys)/86400000)+1)/7);} 
function groupByPipeline(runs){const g={};for(const run of runs){const key=run.pipelineId||'pipeline-sem-nome';if(!g[key])g[key]=[];g[key].push(run);}for(const key of Object.keys(g)){g[key].sort((a,b)=>dateValue(b.startDate)-dateValue(a.startDate));}return g;}
function card(title,value,hint){return `<article class="stat-card"><h4>${esc(title)}</h4><strong>${esc(value)}</strong><p>${esc(hint)}</p></article>`;}
function listItems(items,cls,tag){if(!items||!items.length)return '<article class="priority-item"><div class="top"><span class="name">Sem dados</span><span class="status-pill status-ok">OK</span></div><div class="meta">Nada a reportar nesta janela.</div></article>';return items.slice(0,8).map((i)=>`<article class="priority-item"><div class="top"><span class="name">${esc(i.name||i.pipelineId||'-')}</span><span class="status-pill ${cls}">${esc(tag)}</span></div><div class="meta">${esc(i.reason||'')}${i.run_id_pipeline?` | ${esc(i.run_id_pipeline)}`:''}</div></article>`).join('');}
function formatDuration(seconds){const s=Math.max(0,Math.floor(Number(seconds||0)));const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;if(h>0)return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;}
function stripAnsi(v){return String(v||'').replace(/\x1B\[[0-?]*[ -/]*[@-~]/g,'');}
function percentile(values,p){if(!values.length)return 0;const arr=[...values].sort((a,b)=>a-b);const i=Math.max(0,Math.min(arr.length-1,Math.ceil(arr.length*p)-1));return arr[i];}
function avg(values){if(!values.length)return 0;return values.reduce((sum,v)=>sum+Number(v||0),0)/values.length;}
function dateValue(v){if(!v)return 0;const t=new Date(v).getTime();return Number.isNaN(t)?0:t;}
function fmt(v){if(!v)return '-';const d=new Date(v);if(Number.isNaN(d.getTime()))return String(v);return d.toLocaleString('pt-PT');}
function setText(id,val){const el=document.getElementById(id);if(el)el.textContent=String(val??'-');}
function setHtml(id,html){const el=document.getElementById(id);if(el)el.innerHTML=html;}
function showLoginError(t){const el=document.getElementById('loginError');if(!el)return;el.textContent=t;el.classList.add('show');}
function clearLoginError(){const el=document.getElementById('loginError');if(!el)return;el.textContent='';el.classList.remove('show');}
function esc(v){return String(v??'-').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;');}
function showToast(msg,type){const t=document.getElementById('toast');if(!t)return;t.textContent=msg;t.className=`toast show ${type||'info'}`;setTimeout(()=>{t.className='toast';},2400);}
function initMotion(){if(!window.MaiatronMotion||typeof window.MaiatronMotion.init!=='function')return;window.MaiatronMotion.init({preset:'premium',configUrl:CONFIG.authConfigUrl});}
function revealOverseerSurface(){if(!window.MaiatronMotion||typeof window.MaiatronMotion.reveal!=='function')return;const root=document.getElementById('mainApp')&&!document.getElementById('mainApp')?.classList.contains('hidden')?document.getElementById('mainApp'):document;window.MaiatronMotion.reveal(root,'.signal-card,.chart-card,.list-card,.view.active > *, .metric-card, .run-row, .pipeline-row, .detail-modal-content, .drawer-card');}

function getUserRole(pipelineId){const perms=state.pipelinePermissions?.[pipelineId];if(!perms||!perms.length)return 'viewer';const me=state.user?.username;if(!me)return 'viewer';const grant=perms.find((p)=>p.username===me);return grant?String(grant.role||'viewer').toLowerCase():'viewer';}
function canUserRunPipeline(pipelineId){const appRole=(state.payload?.authz?.app_role||'viewer').toLowerCase();if(appRole==='admin')return true;const role=getUserRole(pipelineId);return role==='owner'||role==='executor';}
function isValidCron(expr){if(!expr)return false;const s=expr.trim().toLowerCase();if(s==='manual'||s==='paused')return true;return /^[\d\*\/\-\,\?LW#]+(\s+[\d\*\/\-\,\?LW#]+){4}$/.test(s);}
async function handleConfigChange(pipelineId,newSchedule,newOwner,newCriticality){if(!isValidCron(newSchedule)){showToast(t('schedInvalidMsg'),'error');return;} if(newOwner===undefined||newOwner===null)newOwner=state.orchestratorPipelines.find(p=>p.pipeline_id===pipelineId||p.pipelineId===pipelineId)?.owner; if(newCriticality===undefined||newCriticality===null)newCriticality=state.orchestratorPipelines.find(p=>p.pipeline_id===pipelineId||p.pipelineId===pipelineId)?.criticality;const by=state.user?.username||'frontend';const trigger={trigger_id:`sched-${newTriggerId()}`,type:'schedule_change',pipeline_id:pipelineId,new_schedule:newSchedule,new_owner:newOwner,new_criticality:newCriticality,requested_by:by,requested_at:new Date().toISOString()};let delivered=false;try{delivered=await writeScheduleTrigger(trigger);}catch{}const cmd=`python orchestrator.py schedule set ${pipelineId} "${newSchedule}"`;if(delivered){showToast(`Schedule de ${pipelineId} ${t('schedChanged')}`,'success');}else{await copyText(cmd);showToast(t('schedFail'),'warning');}const cat=state.orchestratorPipelines.find((p)=>(p.pipeline_id||p.pipelineId)===pipelineId);if(cat)cat.schedule=newSchedule; cat.owner=newOwner; cat.criticality=newCriticality;state.pendingScheduleMutations[pipelineId]={schedule:newSchedule,prev_schedule:cat?.prev_schedule||null,ts:Date.now()};}
async function handlePauseToggle(pipelineId,action){const cat=state.orchestratorPipelines.find((p)=>(p.pipeline_id||p.pipelineId)===pipelineId);if(!cat)return;if(action==='pause'){const currentSchedule=cat.schedule||'manual';if(currentSchedule.toLowerCase()==='manual'||currentSchedule.toLowerCase()==='paused')return;cat.prev_schedule=currentSchedule;const cc = state.orchestratorPipelines.find(p=>(p.pipeline_id||p.pipelineId)===pipelineId); await handleConfigChange(pipelineId,'paused',cc?.owner,cc?.criticality);cat.schedule='paused';cat.prev_schedule=currentSchedule;state.pendingScheduleMutations[pipelineId]={schedule:'paused',prev_schedule:currentSchedule,ts:Date.now()};renderOrchestratorSchedules();}else if(action==='resume'){const prev=cat.prev_schedule||cat.prevSchedule||'manual';const cc2 = state.orchestratorPipelines.find(p=>(p.pipeline_id||p.pipelineId)===pipelineId); await handleConfigChange(pipelineId,prev,cc2?.owner,cc2?.criticality);cat.schedule=prev;cat.prev_schedule=null;cat.prevSchedule=null;state.pendingScheduleMutations[pipelineId]={schedule:prev,prev_schedule:null,ts:Date.now()};renderOrchestratorSchedules();}}
async function writeScheduleTrigger(trigger){try{const action=(trigger?.type==='pipeline_meta_update')?'pipeline_meta_update':'schedule_update';const data=await apiPost(action,trigger);return data?.status==='ok'||data?.ok===true;}catch(e){if(handleAuthApiError(e))return false;console.error('writeScheduleTrigger error:',e);showToast(e?.message||'Erro na atualização de schedule','error');return false;}}
function rehydratePendingScheduleMutations(){const TTL=3*60*1000;const now=Date.now();for(const pid of Object.keys(state.pendingScheduleMutations)){const m=state.pendingScheduleMutations[pid];if(now-m.ts>TTL){delete state.pendingScheduleMutations[pid];continue;}const cat=state.orchestratorPipelines.find((p)=>(p.pipeline_id||p.pipelineId)===pid);if(!cat)continue;const backendSchedule=(cat.schedule||'').toLowerCase();const mutationSchedule=(m.schedule||'').toLowerCase();if(backendSchedule===mutationSchedule){delete state.pendingScheduleMutations[pid];continue;}cat.schedule=m.schedule;if(m.prev_schedule)cat.prev_schedule=m.prev_schedule;}}

function getLineagePipelineIds(){const ids=new Set();Object.keys(state.pipelineScripts||{}).forEach((id)=>ids.add(String(id)));Object.keys(state.moduleLineage||{}).forEach((id)=>ids.add(String(id)));(state.pipelinesAll||[]).forEach((p)=>{if(p?.pipelineId)ids.add(String(p.pipelineId));});return [...ids].sort();}
function pipelineNameById(id){const pid=String(id||'');const fromP=(state.pipelinesAll||[]).find((p)=>String(p.pipelineId)===pid);if(fromP?.name)return fromP.name;const fromC=(state.orchestratorPipelines||[]).find((p)=>String(p.pipeline_id||p.pipelineId)===pid);return fromC?.name||fromC?.pipeline_id||pid;}
function hashPipelineHue(id){const text=String(id||'overseer');let h=0;for(let i=0;i<text.length;i+=1){h=((h<<5)-h)+text.charCodeAt(i);h|=0;}return Math.abs(h)%360;}

/* lineage helpers */
function lineageEventLevel(script){
  const raw=String(script?.lastEventLevel||'').toLowerCase();
  if(raw==='error'||raw==='warning'||raw==='ok')return raw;
  if(Number(script?.errorCount||0)>0)return 'error';
  if(Number(script?.warningCount||0)>0)return 'warning';
  const st=normalizeRunStatus(script?.lastStatus);
  if(st==='FAILED')return 'error';
  if(st==='WARNING')return 'warning';
  if(st==='OK')return 'ok';
  if(!script?.executed)return 'inventory';
  return 'unknown';
}
function lineagePipelineSummary(pid){
  const pipelineId=String(pid||'');
  const scripts=Array.isArray(state.pipelineScripts?.[pipelineId])?state.pipelineScripts[pipelineId]:[];
  const graph=state.moduleLineage?.[pipelineId]||{};
  const nodes=Array.isArray(graph.nodes)?graph.nodes:[];
  const edges=Array.isArray(graph.edges)?graph.edges:[];
  const executed=scripts.filter((s)=>!!s.executed).length;
  const errorScripts=scripts.filter((s)=>lineageEventLevel(s)==='error').length;
  const warningScripts=scripts.filter((s)=>lineageEventLevel(s)==='warning').length;
  const okScripts=scripts.filter((s)=>lineageEventLevel(s)==='ok').length;
  const inventoryScripts=scripts.filter((s)=>lineageEventLevel(s)==='inventory').length;
  const unknownScripts=Math.max(scripts.length-errorScripts-warningScripts-okScripts-inventoryScripts,0);
  const lastIssue=Math.max(...scripts.map((s)=>dateValue(s.lastErrorAt)),...scripts.map((s)=>dateValue(s.lastWarningAt)),0);
  const latest=Math.max(...scripts.map((s)=>dateValue(s.lastSeenAt)),...nodes.map((n)=>dateValue(n.lastSeenAt||n.lastSeen)),0);
  return {
    pipelineId, name:pipelineNameById(pipelineId), hue:hashPipelineHue(pipelineId),
    scripts, nodes, edges, executed,
    errorScripts, warningScripts, okScripts, inventoryScripts, unknownScripts,
    lastIssueAt:lastIssue?new Date(lastIssue).toISOString():null,
    lastSeenAt:latest?new Date(latest).toISOString():null,
  };
}
function lineageStateClass(summary){if(summary.errorScripts>0)return 'status-nok';if(summary.warningScripts>0)return 'status-warning';if(summary.okScripts>0&&summary.unknownScripts===0)return 'status-ok';return 'status-muted';}
function lineageStateLabel(summary){if(summary.errorScripts>0)return 'ERRO';if(summary.warningScripts>0)return 'WARNING';if(summary.okScripts>0&&summary.unknownScripts===0)return 'OK';if(summary.scripts.length>0&&summary.executed===0)return 'SEM EXECUÇÃO';if(summary.inventoryScripts>0)return 'SEM EXECUÇÃO';return 'SEM DADOS';}
function ensureLineageLogModal(){
  let modal=document.getElementById('lineageLogModal');
  if(modal)return modal;
  const host=document.createElement('div');
  host.className='modal'; host.id='lineageLogModal'; host.setAttribute('aria-hidden','true');
  host.innerHTML='<div class="modal-overlay" id="lineageLogOverlay"></div><div class="modal-content" role="dialog" aria-modal="true" aria-labelledby="lineageLogTitle"><div class="modal-header"><h2 id="lineageLogTitle">Log do Script</h2><button class="modal-close" id="lineageLogCloseBtn" aria-label="Fechar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button></div><div class="modal-body"><div class="lineage-log-meta" id="lineageLogMeta">-</div><div class="lineage-log-actions"><button class="btn-detail" id="lineageLogExportBtn">Exportar .txt</button></div><pre class="error-log" id="lineageLogText"></pre></div></div>';
  document.body.appendChild(host);
  host.querySelector('#lineageLogCloseBtn')?.addEventListener('click',closeLineageLogModal);
  host.querySelector('#lineageLogOverlay')?.addEventListener('click',closeLineageLogModal);
  document.addEventListener('keydown',(ev)=>{if(ev.key==='Escape')closeLineageLogModal();});
  return host;
}
function closeLineageLogModal(){const m=document.getElementById('lineageLogModal');m?.classList.remove('active');m?.setAttribute('aria-hidden','true');}
function openLineageLogModal(payload){
  const modal=ensureLineageLogModal();
  const title=modal.querySelector('#lineageLogTitle');
  const meta=modal.querySelector('#lineageLogMeta');
  const textEl=modal.querySelector('#lineageLogText');
  const exportBtn=modal.querySelector('#lineageLogExportBtn');
  const script=String(payload?.script||'-');
  const pipeline=String(payload?.pipeline||'-');
  const runId=payload?.runId!=null?String(payload.runId):'-';
  const when=payload?.when?fmt(payload.when):'-';
  const logText=stripAnsi(String(payload?.log||''));
  if(title)title.textContent=`Log: ${script}`;
  if(meta)meta.textContent=`Pipeline: ${pipeline} | Run #${runId} | ${when}`;
  if(textEl)textEl.textContent=logText||'Sem log disponível.';
  if(exportBtn){
    exportBtn.onclick=()=>{
      const blob=new Blob([logText||'Sem log disponível.'],{type:'text/plain;charset=utf-8'});
      const a=document.createElement('a');
      const safeScript=(script||'script').replace(/[^a-zA-Z0-9_.-]/g,'_');
      a.href=URL.createObjectURL(blob); a.download=`${safeScript}_run_${runId}.txt`;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(()=>URL.revokeObjectURL(a.href),1500);
    };
  }
  modal.classList.add('active'); modal.setAttribute('aria-hidden','false');
}

/* lineage v5: script file logs + robust modal mapping */
function resolvePipelineRunLog(pipelineId, preferredRunId){
  const pref = preferredRunId!=null ? String(preferredRunId) : '';
  if(pref){
    const d = state.details?.[pref] || state.details?.[Number(pref)] || null;
    if(d && String(d.logMessage||d.errorMessage||'').trim()) return {runId: pref, detail: d};
  }
  const latest = (state.runsAll||[])
    .filter((r)=>String(r.pipelineId||'')===String(pipelineId||''))
    .sort((a,b)=>dateValue(b.startDate)-dateValue(a.startDate))[0];
  if(!latest) return null;
  const d = state.details?.[String(latest.id)] || state.details?.[latest.id] || null;
  if(!d || !String(d.logMessage||d.errorMessage||'').trim()) return null;
  return {runId: String(latest.id), detail: d, run: latest};
}
function getScriptLogPayload(script,pipelineId){
  if(!script) return null;
  const scriptPath=String(script.path||'-');
  const fileLog=String(script.scriptLogMessage||'').trim();
  if(fileLog){
    return {
      script: scriptPath,
      pipeline: String(pipelineId||'-'),
      runId: script.lastRunId!=null?String(script.lastRunId):'-',
      when: script.scriptLogUpdatedAt || script.lastSeenAt || script.lastErrorAt || script.lastWarningAt || null,
      log: fileLog,
      source: script.scriptLogSource || 'log-file',
    };
  }
  const isMain = scriptPath.toLowerCase().endsWith('/main.py') || scriptPath.toLowerCase()==='main.py';
  if(!isMain) return null;
  const runLog = resolvePipelineRunLog(pipelineId, script.lastRunId);
  if(!runLog) return null;
  const d=runLog.detail||{};
  const log=String(d.logMessage||d.errorMessage||'').trim();
  if(!log) return null;
  return {
    script: scriptPath,
    pipeline: String(pipelineId||'-'),
    runId: String(runLog.runId||'-'),
    when: script.lastSeenAt || runLog.run?.startDate || null,
    log,
    source: 'run-detail',
  };
}

/* ── DAG SVG builder for dependency edges ──────────── */
function buildDagSvg(edges) {
  if (!edges || !edges.length) return '';
  const nodeSet = new Set();
  edges.forEach(function (e) { nodeSet.add(String(e.source)); nodeSet.add(String(e.target)); });
  const nodeIds = Array.from(nodeSet).sort();

  /* topological layer assignment (longest-path) */
  const adj = {};
  const inDeg = {};
  nodeIds.forEach(function (id) { adj[id] = []; inDeg[id] = 0; });
  edges.forEach(function (e) {
    var s = String(e.source), t = String(e.target);
    if (adj[s]) adj[s].push(t);
    inDeg[t] = (inDeg[t] || 0) + 1;
  });
  var layer = {};
  var queue = nodeIds.filter(function (id) { return (inDeg[id] || 0) === 0; });
  queue.forEach(function (id) { layer[id] = 0; });
  var maxLayer = 0;
  while (queue.length) {
    var cur = queue.shift();
    (adj[cur] || []).forEach(function (t) {
      var nl = (layer[cur] || 0) + 1;
      if (nl > (layer[t] || 0)) layer[t] = nl;
      if (nl > maxLayer) maxLayer = nl;
      inDeg[t] = (inDeg[t] || 0) - 1;
      if (inDeg[t] <= 0) queue.push(t);
    });
  }
  /* fallback for cycles: assign remaining nodes */
  nodeIds.forEach(function (id) { if (layer[id] === undefined) { maxLayer++; layer[id] = maxLayer; } });

  /* group nodes by layer */
  var layers = {};
  nodeIds.forEach(function (id) {
    var l = layer[id] || 0;
    if (!layers[l]) layers[l] = [];
    layers[l].push(id);
  });

  /* layout */
  var nodeW = 120, nodeH = 28, gapX = 60, gapY = 16, padX = 20, padY = 16;
  var maxPerLayer = 0;
  Object.values(layers).forEach(function (arr) { if (arr.length > maxPerLayer) maxPerLayer = arr.length; });
  var svgW = (maxLayer + 1) * (nodeW + gapX) + padX * 2;
  var svgH = maxPerLayer * (nodeH + gapY) + padY * 2;

  var pos = {};
  for (var l = 0; l <= maxLayer; l++) {
    var col = layers[l] || [];
    var totalH = col.length * nodeH + (col.length - 1) * gapY;
    var startY = (svgH - totalH) / 2;
    for (var i = 0; i < col.length; i++) {
      pos[col[i]] = {
        x: padX + l * (nodeW + gapX),
        y: startY + i * (nodeH + gapY)
      };
    }
  }

  /* render */
  var edgesHtml = edges.map(function (e) {
    var s = pos[String(e.source)], t = pos[String(e.target)];
    if (!s || !t) return '';
    var sx = s.x + nodeW, sy = s.y + nodeH / 2;
    var tx = t.x, ty = t.y + nodeH / 2;
    var midX = (sx + tx) / 2;
    return '<path class="lineage-dag-edge" d="M' + sx + ' ' + sy + ' C' + midX + ' ' + sy + ' ' + midX + ' ' + ty + ' ' + tx + ' ' + ty + '" />' +
      '<polygon class="lineage-dag-arrowhead" points="' + tx + ',' + (ty - 4) + ' ' + (tx + 7) + ',' + ty + ' ' + tx + ',' + (ty + 4) + '" />';
  }).join('');

  var nodesHtml = nodeIds.map(function (id) {
    var p = pos[id]; if (!p) return '';
    var label = id.length > 16 ? id.slice(0, 14) + '…' : id;
    return '<g class="lineage-dag-node" transform="translate(' + p.x + ',' + p.y + ')">' +
      '<rect class="lineage-dag-node-rect" width="' + nodeW + '" height="' + nodeH + '"></rect>' +
      '<text class="lineage-dag-node-label" x="' + (nodeW / 2) + '" y="' + (nodeH / 2) + '">' + esc(label) + '</text></g>';
  }).join('');

  return '<div class="lineage-dag-container"><svg class="lineage-dag-svg" width="' + svgW + '" height="' + svgH + '" viewBox="0 0 ' + svgW + ' ' + svgH + '" xmlns="http://www.w3.org/2000/svg">' + edgesHtml + nodesHtml + '</svg></div>';
}

/* ── mini sparkline for period comparison ──────────── */
function buildCompareSparkline(valuesArr) {
  if (!valuesArr || valuesArr.length < 2) return '';
  var w = 56, h = 24, pad = 2;
  var vals = valuesArr.slice(-6);
  var max = Math.max.apply(null, vals);
  var min = Math.min.apply(null, vals);
  var range = max - min || 1;
  var step = (w - pad * 2) / (vals.length - 1);
  var pts = vals.map(function (v, i) {
    var x = pad + i * step;
    var y = h - pad - ((v - min) / range) * (h - pad * 2);
    return x.toFixed(1) + ',' + y.toFixed(1);
  });
  var polyline = pts.join(' ');
  var area = pts.join(' ') + ' ' + (pad + (vals.length - 1) * step).toFixed(1) + ',' + (h - pad) + ' ' + pad.toFixed(1) + ',' + (h - pad);
  return '<svg class="period-compare-sparkline" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">' +
    '<polygon class="period-compare-spark-area" points="' + area + '" />' +
    '<polyline class="period-compare-spark-line" points="' + polyline + '" />' +
    '</svg>';
}

function renderLineage(){
  const c=document.getElementById('lineageGrid');
  if(!c)return;
  const pipelineIds=getLineagePipelineIds();
  if(!pipelineIds.length){
    c.innerHTML='<article class="lineage-item"><h4>Sem dados</h4><p class="muted">Sem pipeline selecionado.</p></article>';
    return;
  }
  const allSummaries=pipelineIds.map((pid)=>lineagePipelineSummary(pid));
  const query=String(state.lineagePipelineQuery||'').trim().toLowerCase();
  const summaries=query?allSummaries.filter((s)=>`${s.pipelineId} ${s.name}`.toLowerCase().includes(query)):allSummaries;
  const availableIds=summaries.map((s)=>s.pipelineId);
  if(!state.lineageSelectedPipelineId||!availableIds.includes(state.lineageSelectedPipelineId))state.lineageSelectedPipelineId=availableIds[0]||allSummaries[0].pipelineId;
  const selected=summaries.find((s)=>s.pipelineId===String(state.lineageSelectedPipelineId))||allSummaries.find((s)=>s.pipelineId===String(state.lineageSelectedPipelineId))||allSummaries[0];
  state.lineageSelectedPipelineId=selected.pipelineId;
  const pMeta=state.pipelinesAll.find((p)=>String(p.pipelineId)===String(selected.pipelineId))||{};

  const filterRow=`<div class="lineage-filter-row"><input id="lineagePipelineFilterInput" class="lineage-search" type="search" placeholder="Filtrar pipeline..." value="${esc(state.lineagePipelineQuery||'')}" /><button id="lineagePipelineFilterClear" class="lineage-filter-clear">Limpar</button><span class="muted">${summaries.length}/${allSummaries.length}</span></div>`;

  const tileCards=summaries.map((s)=>{
    const active=s.pipelineId===state.lineageSelectedPipelineId;
    const pillClass=lineageStateClass(s);
    return `<button class="lineage-pipeline-tile ${active?'active':''}" data-lineage-pipeline="${esc(s.pipelineId)}" style="--pipeline-hue:${s.hue};"><div class="lineage-pipeline-head"><strong>${esc(s.name)}</strong><span class="status-pill ${pillClass}">${lineageStateLabel(s)}</span></div><div class="lineage-pipeline-metrics"><span>${s.scripts.length} scripts</span><span>${s.executed} executados</span><span>${s.nodes.length} módulos</span></div><div class="lineage-pipeline-metrics"><span>Erros: ${s.errorScripts}</span><span>Warnings: ${s.warningScripts}</span></div><div class="lineage-pipeline-last muted">Última atividade: ${esc(fmt(s.lastSeenAt))}</div></button>`;
  }).join('');

  const scriptCards=selected.scripts.map((s)=>{
    const level=lineageEventLevel(s);
    const pillClass=level==='error'?'status-nok':level==='warning'?'status-warning':level==='ok'?'status-ok':'status-muted';
    const label=level==='error'?'ERRO':level==='warning'?'WARNING':level==='ok'?'OK':level==='inventory'?'SEM EXECUÇÃO':'DESCONHECIDO';
    const mode=s.executed?'executado':'inventário';
    const cls=s.executed?'executed':'inventory';
    const when=s.lastErrorAt||s.lastWarningAt||s.lastSeenAt||s.scriptLogUpdatedAt||null;
    const counts=`W:${Number(s.warningCount||0)} | E:${Number(s.errorCount||0)}`;
    const meta=[`Fonte: ${s.source||'src'}`,`Modo: ${mode}`,s.lastRunId?`Run #${s.lastRunId}`:'',when?`Último evento: ${fmt(when)}`:'',s.scriptLogSource?`Log: ${s.scriptLogSource}`:'',counts].filter(Boolean).join(' | ');
    const description=String(s.description||'').trim();
    const message=String(s.lastMessage||'').trim();
    const logPayload=getScriptLogPayload(s,selected.pipelineId);
    const logBtn=logPayload?`<div class="lineage-log-actions"><button class="btn-detail lineage-log-btn" data-lineage-log-path="${esc(s.path||'')}">Ver logs</button></div>`:'';
    return `<article class="lineage-item lineage-script ${cls}" style="--pipeline-hue:${selected.hue};"><h4>${esc(s.path||'-')}</h4><p class="meta"><span class="status-pill ${pillClass}">${label}</span></p>${description?`<p class="lineage-script-description">${esc(description)}</p>`:''}<p class="muted">${esc(meta)}</p>${message?`<p class="lineage-message">${esc(message)}</p>`:''}${logBtn}</article>`;
  }).join('');

  const moduleCards=selected.nodes.map((n)=>{
    const st=normalizeRunStatus(n.status||'UNKNOWN');
    const lvl=String(n.lastEventLevel||'').toLowerCase();
    const pillClass=lvl==='error'||st==='FAILED'?'status-nok':lvl==='warning'||st==='WARNING'?'status-warning':st==='OK'?'status-ok':'status-muted';
    const label=lvl==='error'||st==='FAILED'?'ERRO':lvl==='warning'||st==='WARNING'?'WARNING':st==='OK'?'OK':'DESCONHECIDO';
    const when=n.lastSeenAt||n.lastSeen||null;
    const msg=n.lastMessage||n.lastError||'';
    const description=String(n.description||'').trim();
    const modulePath=String(n.script||n.label||'');
    const scriptRef=selected.scripts.find((s)=>String(s.path||'')===modulePath) || selected.scripts.find((s)=>String(s.path||'').toLowerCase()===modulePath.toLowerCase());
    const logPayload=getScriptLogPayload(scriptRef, selected.pipelineId);
    const logBtn=logPayload?`<div class="lineage-log-actions"><button class="btn-detail lineage-log-btn" data-lineage-module-log-path="${esc(modulePath)}">Ver logs</button></div>`:'';
    return `<article class="lineage-item lineage-module" style="--pipeline-hue:${selected.hue};"><h4>${esc(n.label||n.id||'-')}${n.critical===false?' <span class="badge badge-muted">non-critical</span>':''}</h4><p class="meta"><span class="status-pill ${pillClass}">${label}</span></p>${description?`<p class="lineage-script-description">${esc(description)}</p>`:''}<p class="muted">Último evento: ${esc(fmt(when))}</p>${msg?`<p class="lineage-message">${esc(msg)}</p>`:''}${logBtn}</article>`;
  }).join('');

  const deps=selected.edges.map((e)=>`<span class="lineage-dep-chip">${esc(e.source)} -> ${esc(e.target)}</span>`).join('');
  const dagSvg=buildDagSvg(selected.edges);

  c.innerHTML=`<div class="lineage-shell"><div class="lineage-tiles">${filterRow}${tileCards||'<article class="lineage-item"><h4>Sem correspondências</h4><p class="muted">Ajusta o filtro de pipeline.</p></article>'}</div><div class="lineage-selected"><article class="lineage-hero" style="--pipeline-hue:${selected.hue};"><div><h4>${esc(selected.name)}</h4><p class="muted">Pipeline: ${esc(selected.pipelineId)} | Owner: ${esc(pMeta.owner||'unknown')} | Criticidade: ${esc(pMeta.criticality||'medium')}</p></div><div class="lineage-hero-kpis"><span><strong>${selected.scripts.length}</strong> scripts</span><span><strong>${selected.executed}</strong> executados</span><span><strong>${selected.nodes.length}</strong> módulos</span><span><strong>${selected.errorScripts}</strong> erros</span><span><strong>${selected.warningScripts}</strong> warnings</span></div></article><section class="lineage-section"><h4 class="lineage-section-title">Scripts</h4><div class="lineage-grid lineage-grid-enhanced">${scriptCards||'<article class="lineage-item"><h4>Sem scripts</h4><p class="muted">Não há inventário para este pipeline.</p></article>'}</div></section><section class="lineage-section"><h4 class="lineage-section-title">Módulos observados</h4><div class="lineage-grid lineage-grid-enhanced">${moduleCards||'<article class="lineage-item"><h4>Sem módulos</h4><p class="muted">Ainda sem eventos de módulo para este pipeline.</p></article>'}</div></section><section class="lineage-section"><h4 class="lineage-section-title">Dependências</h4>${dagSvg||''}<div class="lineage-dependency-list">${deps||'<span class="muted">Sem dependências declaradas.</span>'}</div></section></div></div>`;

  c.querySelectorAll('button[data-lineage-pipeline]').forEach((btn)=>btn.addEventListener('click',()=>{state.lineageSelectedPipelineId=btn.dataset.lineagePipeline||'';renderLineage();}));
  const input=c.querySelector('#lineagePipelineFilterInput');
  if(input){input.addEventListener('input',(ev)=>{state.lineagePipelineQuery=ev.target?.value||'';renderLineage();});}
  const clearBtn=c.querySelector('#lineagePipelineFilterClear');
  if(clearBtn){clearBtn.addEventListener('click',()=>{state.lineagePipelineQuery='';renderLineage();});}
  c.querySelectorAll('button[data-lineage-log-path]').forEach((btn)=>btn.addEventListener('click',()=>{
    const path = btn.getAttribute('data-lineage-log-path')||'';
    const script = selected.scripts.find((s)=>String(s.path||'')===String(path));
    const payload = getScriptLogPayload(script, selected.pipelineId);
    if(!payload){showToast('Sem logs disponíveis para este script','info');return;}
    openLineageLogModal(payload);
  }));
  c.querySelectorAll('button[data-lineage-module-log-path]').forEach((btn)=>btn.addEventListener('click',()=>{
    const path = btn.getAttribute('data-lineage-module-log-path')||'';
    const script = selected.scripts.find((s)=>String(s.path||'')===String(path)) || selected.scripts.find((s)=>String(s.path||'').toLowerCase()===String(path).toLowerCase());
    const payload = getScriptLogPayload(script, selected.pipelineId);
    if(!payload){showToast('Sem logs disponíveis para este módulo','info');return;}
    openLineageLogModal(payload);
  }));
}

/* =======================================================================
   OVERSEER v3.1.3 core — hybrid refresh, SSO auth gate and API authz UX
   ======================================================================= */

Object.assign(CONFIG, {
  refreshMs: 10000,
  fastRefreshMs: 10000,
  heavyRefreshMs: 60000,
  staleFullMs: 300000,
  dataStaleMs: 180000,
  updatedToastCooldownMs: 45000,
});

Object.assign(state, {
  activeView: 'dashboardView',
  _kpiAnimatedByView: {},
  _currentRunLogRaw: '',
  _currentRunLogSource: '-',
  _lastFullRefreshAt: 0,
  _lastUpdateToastAt: 0,
  _lastToastGeneratedAt: '',
});

let fastRefreshTimer = null;
let heavyRefreshTimer = null;
let uiRefreshTimer = null;
let refreshInFlight = false;
let pollInFlight = false;
let refreshSeq = 0;
let nextFastRefreshAt = 0;
let refreshAbortController = null;
let pollAbortController = null;
let refreshingSurfaceTimer = null;

function animateOverviewCountersOnce() {
  const targets = [
    { id: 'signalAtRisk', value: Number(state.overview?.operationalSignals?.atRisk || 0) },
    { id: 'signalStale', value: Number(state.overview?.operationalSignals?.stale || 0) },
    { id: 'signalRegressions', value: Number(state.overview?.operationalSignals?.regressions || 0) },
  ];
  targets.forEach((item) => animateCounter(item.id, item.value));
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const safeTarget = Number.isFinite(target) ? target : 0;
  el.textContent = String(Math.round(safeTarget));
}

function bindRunLogToolbar() {
  const search = document.getElementById('modalLogSearch');
  const copyBtn = document.getElementById('modalLogCopyBtn');
  const downloadBtn = document.getElementById('modalLogDownloadBtn');
  if (search && !search.dataset.bound) {
    search.dataset.bound = '1';
    search.addEventListener('input', () => {
      renderModalRunLog(search.value || '');
    });
  }
  if (copyBtn && !copyBtn.dataset.bound) {
    copyBtn.dataset.bound = '1';
    copyBtn.addEventListener('click', async () => {
      const raw = state._currentRunLogRaw || '';
      if (!raw) return;
      await copyText(raw);
      showToast('Log copiado', 'success');
    });
  }
  if (downloadBtn && !downloadBtn.dataset.bound) {
    downloadBtn.dataset.bound = '1';
    downloadBtn.addEventListener('click', () => {
      const raw = state._currentRunLogRaw || '';
      if (!raw) return;
      const runId = String(document.getElementById('modalRunId')?.textContent || 'run').replace(/[^\dA-Za-z_-]/g, '');
      const blob = new Blob([raw], { type: 'text/plain;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `run_${runId || 'detail'}.log`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 1500);
    });
  }
}

function setRefreshingSurface(hard = false) {
  const host = document.getElementById('mainApp');
  if (!host) return;
  host.classList.add('refreshing-surface');
  host.classList.toggle('refreshing-hard', !!hard);
  if (refreshingSurfaceTimer) clearTimeout(refreshingSurfaceTimer);
}

function clearRefreshingSurface() {
  const host = document.getElementById('mainApp');
  if (!host) return;
  if (refreshingSurfaceTimer) clearTimeout(refreshingSurfaceTimer);
  refreshingSurfaceTimer = setTimeout(() => {
    host.classList.remove('refreshing-surface', 'refreshing-hard');
  }, 180);
}

function notifyDataUpdated(generatedAt, options = {}) {
  const force = !!options.force;
  const parsed = dateValue(generatedAt);
  if (!parsed) return;
  const key = new Date(parsed).toISOString();
  const now = Date.now();
  const cooldownMs = Number(CONFIG.updatedToastCooldownMs || 45000);
  if (!force) {
    if (state._lastToastGeneratedAt === key) return;
    if ((now - Number(state._lastUpdateToastAt || 0)) < cooldownMs) return;
  }
  state._lastToastGeneratedAt = key;
  state._lastUpdateToastAt = now;
  showToast(t('dataUpdated'), 'success');
}

class OverseerApiError extends Error {
  constructor(action, status, message, payload) {
    super(message || `API ${action} falhou (${status})`);
    this.name = 'OverseerApiError';
    this.action = action;
    this.status = status;
    this.payload = payload || null;
  }
}

function normalizeApiError(action, response, payload) {
  const status = Number(response?.status || 0);
  const message = String(payload?.error || `API ${action} falhou (${status})`);
  return new OverseerApiError(action, status, message, payload || null);
}

function handleAuthApiError(error) {
  const status = Number(error?.status || 0);
  if (status === 401) {
    stopAutoRefresh();
    state.user = null;
    window.MaiatronAuthUI?.setSession(null);
    showLoginScreen();
    showToast('Sessão expirada. Inicie sessão novamente.', 'warning');
    return true;
  }
  if (status === 403) {
    stopAutoRefresh();
    const reason = String(error?.payload?.error || 'A tua sessão está ativa, mas sem acesso a esta app.');
    showAccessDeniedScreen(reason);
    showToast('Sem permissão para aceder ao Overseer.', 'error');
    return true;
  }
  return false;
}

async function apiGet(action, options = {}) {
  const params = new URLSearchParams({ action: String(action || '') });
  if (!options.noTimestamp) params.set('t', String(Date.now()));
  const response = await fetch(`${apiBaseUrl()}?${params.toString()}`, {
    cache: 'no-store',
    signal: options.signal,
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch (_) {
    payload = null;
  }
  if (!response.ok) {
    throw normalizeApiError(action, response, payload);
  }
  return payload || {};
}

async function apiPost(action, payload) {
  const response = await fetch(`${apiBaseUrl()}?action=${encodeURIComponent(action)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {}),
    cache: 'no-store',
  });
  let parsed = null;
  try {
    parsed = await response.json();
  } catch (_) {
    parsed = null;
  }
  if (!response.ok) {
    throw normalizeApiError(action, response, parsed);
  }
  return parsed || {};
}

async function loadPayload(signal) {
  return await apiGet('full', { signal });
}

async function loadDetails(signal) {
  try {
    return await apiGet('details', { signal });
  } catch {
    return {};
  }
}

async function loadFast(signal) {
  return await apiGet('ops_fast', { signal });
}

async function loadHeavy(signal) {
  return await apiGet('ops_heavy', { signal });
}

async function loadHealth(signal) {
  try {
    return await apiGet('health', { signal, noTimestamp: true });
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    if (Number(error?.status || 0) === 401 || Number(error?.status || 0) === 403) throw error;
    console.warn('health refresh falhou:', error);
    return null;
  }
}

async function refreshAllData(options = {}) {
  const showSuccessToast = !!options.showSuccessToast;
  const hardRefresh = !!options.hardRefresh;
  const force = !!options.force;
  if (refreshInFlight && !force) return false;
  refreshInFlight = true;
  const seq = ++refreshSeq;
  if (refreshAbortController) refreshAbortController.abort();
  refreshAbortController = new AbortController();
  setRefreshingSurface(hardRefresh);
  try {
    const [payload, details, health] = await Promise.all([
      loadPayload(refreshAbortController.signal),
      loadDetails(refreshAbortController.signal),
      loadHealth(refreshAbortController.signal),
    ]);
    if (seq !== refreshSeq) return false;
    if (!payload || !Array.isArray(payload.fields) || !Array.isArray(payload.rows)) {
      console.warn('Payload inválido recebido, mantendo dados atuais');
      showToast(t('invalidPayload'), 'warning');
      return false;
    }
    const prevGeneratedTs = dateValue(state.payload?.generated_at || state.overview?.generatedAt || null);
    const nextGeneratedTs = dateValue(payload.generated_at || payload.overview?.generatedAt || null);
    const prevRowsCount = Array.isArray(state.payload?.rows) ? state.payload.rows.length : 0;
    const nextRowsCount = Array.isArray(payload.rows) ? payload.rows.length : 0;
    const likelyPartialSnapshot = prevRowsCount > 0 && nextRowsCount === 0 && (!nextGeneratedTs || nextGeneratedTs <= prevGeneratedTs);
    if (likelyPartialSnapshot) {
      console.warn('Snapshot parcial detetado no full refresh; dados anteriores mantidos.');
      if (health && typeof health === 'object') state.healthStatus = health;
      updateFooter();
      renderDataFeedStatus();
      return false;
    }
    state.payload = payload;
    state.details = details || {};
    if (health && typeof health === 'object') state.healthStatus = health;
    buildModelFromPayload();
    renderAll();
    state._lastFullRefreshAt = Date.now();
    if (showSuccessToast) notifyDataUpdated(payload.generated_at || payload.overview?.generatedAt, { force: true });
    return true;
  } catch (error) {
    if (error?.name === 'AbortError') return false;
    if (handleAuthApiError(error)) return false;
    console.error('refreshAllData error:', error);
    showToast(t('dataFail'), 'error');
    return false;
  } finally {
    refreshInFlight = false;
    clearRefreshingSurface();
  }
}

async function manualRefresh() {
  const btn = document.getElementById('refreshBtn');
  btn?.classList.add('loading');
  stopAutoRefresh();
  if (pollAbortController) {
    pollAbortController.abort();
    pollAbortController = null;
  }
  pollInFlight = false;
  try {
    await refreshAllData({ showSuccessToast: true, hardRefresh: true, force: true });
  } finally {
    btn?.classList.remove('loading');
    if (state.user) startAutoRefresh();
  }
}

async function runFastRefreshCycle() {
  if (refreshInFlight || pollInFlight) return;
  pollInFlight = true;
  const seq = ++refreshSeq;
  if (pollAbortController) pollAbortController.abort();
  pollAbortController = new AbortController();
  try {
    const fast = await loadFast(pollAbortController.signal);
    if (seq !== refreshSeq) return;
    const currentGeneratedTs = dateValue(state.payload?.generated_at || state.overview?.generatedAt || null);
    const incomingGeneratedTs = dateValue(fast?.generated_at || fast?.overview?.generatedAt || null);
    if (incomingGeneratedTs && currentGeneratedTs && incomingGeneratedTs < currentGeneratedTs) return;
    const hasNewSnapshot = incomingGeneratedTs > currentGeneratedTs;
    applyFastSnapshot(fast);
    if (hasNewSnapshot) notifyDataUpdated(fast?.generated_at || fast?.overview?.generatedAt);
    renderDataFeedStatus();
  } catch (error) {
    if (error?.name !== 'AbortError') {
      if (handleAuthApiError(error)) return;
      console.warn('fast refresh falhou:', error);
    }
  } finally {
    pollInFlight = false;
  }
}

async function runHeavyRefreshCycle() {
  if (refreshInFlight || pollInFlight) return;
  pollInFlight = true;
  const seq = ++refreshSeq;
  if (pollAbortController) pollAbortController.abort();
  pollAbortController = new AbortController();
  try {
    const [heavy, health] = await Promise.all([
      loadHeavy(pollAbortController.signal),
      loadHealth(pollAbortController.signal),
    ]);
    if (seq !== refreshSeq) return;
    const currentGeneratedTs = dateValue(state.payload?.generated_at || state.overview?.generatedAt || null);
    const incomingGeneratedTs = dateValue(heavy?.generated_at || heavy?.overview?.generatedAt || null);
    if (incomingGeneratedTs && currentGeneratedTs && incomingGeneratedTs < currentGeneratedTs) return;
    const hasNewSnapshot = incomingGeneratedTs > currentGeneratedTs;
    if (health && typeof health === 'object') state.healthStatus = health;
    const previousGenerated = state.payload?.generated_at || null;
    const nextGenerated = heavy?.generated_at || null;
    const heavyChanged = !!nextGenerated && nextGenerated !== previousGenerated;
    applyHeavySnapshot(heavy);
    if (hasNewSnapshot) notifyDataUpdated(heavy?.generated_at || heavy?.overview?.generatedAt);
    const staleFull = !state._lastFullRefreshAt || (Date.now() - state._lastFullRefreshAt >= Number(CONFIG.staleFullMs || 300000));
    if (heavyChanged || staleFull) {
      await refreshAllData({ showSuccessToast: false });
    }
  } catch (error) {
    if (error?.name !== 'AbortError') {
      if (handleAuthApiError(error)) return;
      console.warn('heavy refresh falhou:', error);
    }
  } finally {
    pollInFlight = false;
  }
}

function hasStableOverviewPayload(overview) {
  if (!overview || typeof overview !== 'object') return false;
  const signals = overview.operationalSignals;
  if (!signals || typeof signals !== 'object') return false;
  return Number.isFinite(Number(signals.pipelineCount));
}

function mergeStableOverview(incoming, fallback) {
  if (!incoming || typeof incoming !== 'object') {
    return fallback && typeof fallback === 'object' ? { ...fallback } : null;
  }
  const previous = fallback && typeof fallback === 'object' ? fallback : {};
  const merged = { ...previous, ...incoming };
  const prevSignals = previous.operationalSignals && typeof previous.operationalSignals === 'object'
    ? previous.operationalSignals
    : {};
  const nextSignals = incoming.operationalSignals && typeof incoming.operationalSignals === 'object'
    ? incoming.operationalSignals
    : null;
  const signals = { ...prevSignals, ...(nextSignals || {}) };
  const prevCount = Number(prevSignals.pipelineCount);
  const nextCount = Number(nextSignals?.pipelineCount);
  if ((!Number.isFinite(nextCount) || nextCount <= 0) && Number.isFinite(prevCount) && prevCount > 0) {
    signals.pipelineCount = prevCount;
  }
  merged.operationalSignals = signals;
  if (!merged.globalKpis || typeof merged.globalKpis !== 'object') merged.globalKpis = previous.globalKpis || {};
  if (!merged.topAlerts || typeof merged.topAlerts !== 'object') merged.topAlerts = previous.topAlerts || {};
  if (!merged.generatedAt) merged.generatedAt = incoming.generatedAt || previous.generatedAt || null;
  return merged;
}

function applyFastSnapshot(fast) {
  if (!fast || typeof fast !== 'object') return;
  if (!state.payload || typeof state.payload !== 'object') state.payload = {};
  if (fast.generated_at) state.payload.generated_at = fast.generated_at;
  if (fast.summary && typeof fast.summary === 'object') state.payload.summary = { ...(state.payload.summary || {}), ...fast.summary };
  const previousOverview = state.payload?.overview || state.overview || null;
  if (hasStableOverviewPayload(fast.overview)) {
    state.payload.overview = mergeStableOverview(fast.overview, previousOverview);
    state.overview = state.payload.overview || previousOverview || deriveOverview(state.runsAll || [], state.payload?.summary || {});
    renderOverview();
    renderQualitySection();
  } else if (!state.overview && previousOverview) {
    state.overview = previousOverview;
  }
  updateFooter();
  updateSearchCounter();
}

function applyHeavySnapshot(heavy) {
  if (!heavy || typeof heavy !== 'object') return;
  if (!state.payload || typeof state.payload !== 'object') state.payload = {};
  if (heavy.generated_at) state.payload.generated_at = heavy.generated_at;
  const previousOverview = state.payload?.overview || state.overview || null;
  if (hasStableOverviewPayload(heavy.overview)) {
    state.payload.overview = mergeStableOverview(heavy.overview, previousOverview);
  } else if (previousOverview) {
    state.payload.overview = previousOverview;
  }
  if (Array.isArray(heavy.pipelines)) state.payload.pipelines = heavy.pipelines;
  if (Array.isArray(heavy.pipeline_catalog)) state.payload.pipeline_catalog = heavy.pipeline_catalog;
  if (Array.isArray(heavy.orchestrator_runs)) state.payload.orchestrator_runs = heavy.orchestrator_runs;
  if (Array.isArray(heavy.orchestrator_triggers)) state.payload.orchestrator_triggers = heavy.orchestrator_triggers;
  buildModelFromPayload();
  renderOverview();
  renderPipelineAssetCards();
  renderQualitySection();
  renderPipelines();
  renderLineage();
  renderInsights();
  renderOrchestratorSchedules();
  renderOrchestratorRuns();
  renderCharts();
  updateFooter();
  updateSearchCounter();
}

function startAutoRefresh() {
  stopAutoRefresh();
  nextFastRefreshAt = Date.now() + Number(CONFIG.fastRefreshMs || 10000);
  setText('refreshCountdown', `${Math.max(1, Math.ceil((nextFastRefreshAt - Date.now()) / 1000))}s`);
  fastRefreshTimer = setInterval(async () => {
    nextFastRefreshAt = Date.now() + Number(CONFIG.fastRefreshMs || 10000);
    await runFastRefreshCycle();
  }, Number(CONFIG.fastRefreshMs || 10000));
  heavyRefreshTimer = setInterval(async () => {
    await runHeavyRefreshCycle();
  }, Number(CONFIG.heavyRefreshMs || 60000));
  uiRefreshTimer = setInterval(() => {
    const seconds = Math.max(0, Math.ceil((nextFastRefreshAt - Date.now()) / 1000));
    setText('refreshCountdown', `${seconds}s`);
  }, 1000);
}

function stopAutoRefresh() {
  if (fastRefreshTimer) clearInterval(fastRefreshTimer);
  if (heavyRefreshTimer) clearInterval(heavyRefreshTimer);
  if (uiRefreshTimer) clearInterval(uiRefreshTimer);
  fastRefreshTimer = null;
  heavyRefreshTimer = null;
  uiRefreshTimer = null;
}

function toNum(value) {
  if (typeof value === 'number') return value;
  if (value == null) return 0;
  const text = String(value).trim();
  if (!text) return 0;
  const timeMatch = text.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
  if (timeMatch) {
    const h = Number(timeMatch[1] || 0);
    const m = Number(timeMatch[2] || 0);
    const s = Number(timeMatch[3] || 0);
    return (h * 3600) + (m * 60) + s;
  }
  const normalized = text.includes(',') ? text.replace(/\./g, '').replace(',', '.') : text;
  const n = Number(normalized);
  return Number.isFinite(n) ? n : 0;
}

function buildModelFromPayload() {
  const fields = Array.isArray(state.payload?.fields) ? state.payload.fields : [];
  const rows = Array.isArray(state.payload?.rows) ? state.payload.rows : [];
  const mapped = rows.map((row) => rowToObj(fields, row)).filter((x) => x && x.id != null);
  const enriched = mapped.map((r) => enrichRun(r)).filter((r) => !isTechnicalStepRunRow(r));
  state.runsAll = dedupeRuns(enriched).sort((a, b) => dateValue(b.startDate) - dateValue(a.startDate));
  state.moduleLineage = state.payload?.module_lineage || {};
  state.pipelineScripts = state.payload?.pipeline_scripts || {};
  state.orchestratorPipelines = Array.isArray(state.payload?.pipeline_catalog) ? state.payload.pipeline_catalog : [];
  state.overview = state.payload?.overview || deriveOverview(state.runsAll, state.payload?.summary || {});
  state.pipelinesAll = buildCanonicalPipelines();
  state.lineageNodes = state.payload?.lineage?.nodes || deriveLineage(state.pipelinesAll);
  state.orchestratorTriggers = Array.isArray(state.payload?.orchestrator_triggers) ? state.payload.orchestrator_triggers : [];
  state.pipelinePermissions = state.payload?.pipeline_permissions || {};
  const dbRuns = Array.isArray(state.payload?.orchestrator_runs) ? state.payload.orchestrator_runs : [];
  const inflight = pruneInflight(dbRuns);
  const inflightRows = inflight.map((e) => normalizeOrchestratorRow({
    runId: e.triggerId,
    pipelineId: e.pipelineId,
    status: 'running',
    source: 'frontend',
    createdAt: new Date(e.startedAt).toISOString(),
  }));
  const allOrch = [...dbRuns, ...inflightRows].map((r) => normalizeOrchestratorRow(r));
  const seen = new Set();
  state.orchRuns = [];
  for (const row of allOrch) {
    const key = row.runId || JSON.stringify(row);
    if (!seen.has(key)) {
      seen.add(key);
      state.orchRuns.push(row);
    }
  }
  state.orchRuns.sort((a, b) => dateValue(b.createdAt || b.requested_at) - dateValue(a.createdAt || a.requested_at));
  state.runningPipelines = new Set();
  for (const row of dbRuns) {
    if (String(row.status || '').toLowerCase() === 'running' && (row.pipelineId || row.pipeline_id)) {
      state.runningPipelines.add(row.pipelineId || row.pipeline_id);
    }
  }
  for (const row of inflight) state.runningPipelines.add(row.pipelineId);
  rehydratePendingScheduleMutations();
  applyRunFilters();
  applyPipelineFilters();
}

function buildCanonicalPipelines() {
  const map = new Map();
  const grouped = groupByPipeline(state.runsAll || []);
  const addOrMerge = (pipelineId, patch = {}) => {
    const pid = String(pipelineId || '').trim();
    if (!pid) return;
    const current = map.get(pid) || {
      pipelineId: pid,
      name: pid,
      owner: 'unknown',
      criticality: 'medium',
      schedule: 'manual',
      active: true,
      lastRun: null,
      lastStatus: 'NO_RUN',
      successRate7d: 0,
      regressionDelta: 0,
      staleHours: null,
      riskScore: 0,
      riskLevel: 'low',
      placeholder: true,
    };
    map.set(pid, { ...current, ...patch, pipelineId: pid });
  };

  (state.orchestratorPipelines || []).forEach((p) => {
    const pid = p?.pipeline_id || p?.pipelineId;
    if (!pid) return;
    addOrMerge(pid, {
      name: p?.name || pid,
      owner: p?.owner || 'unknown',
      criticality: String(p?.criticality || 'medium').toLowerCase(),
      schedule: p?.schedule || 'manual',
      active: p?.active === 0 ? false : true,
    });
  });

  (state.payload?.pipelines || []).forEach((p) => {
    const pid = p?.pipelineId || p?.pipeline_id;
    if (!pid) return;
    addOrMerge(pid, {
      name: p?.name || p?.scriptName || pid,
      owner: p?.owner || 'unknown',
      criticality: String(p?.criticality || 'medium').toLowerCase(),
    });
  });

  Object.keys(state.moduleLineage || {}).forEach((pid) => addOrMerge(pid, {}));
  Object.keys(state.pipelineScripts || {}).forEach((pid) => addOrMerge(pid, {}));
  Object.keys(grouped).forEach((pid) => addOrMerge(pid, {}));

  const now = Date.now();
  for (const [pid, base] of map.entries()) {
    const runs = grouped[pid] || [];
    if (!runs.length) {
      const status = base.active === false ? 'INACTIVE' : 'NO_RUN';
      map.set(pid, { ...base, lastStatus: status, placeholder: true, staleHours: null, successRate7d: 0, riskScore: 0, riskLevel: 'low' });
      continue;
    }
    const latest = runs[0];
    const recent = runs.slice(0, 7);
    const failedRecent = recent.filter((r) => isFailedStatus(r.status)).length;
    const successRate7d = recent.length ? ((recent.length - failedRecent) / recent.length) * 100 : 100;
    const staleHours = latest.startDate ? Math.floor((now - dateValue(latest.startDate)) / 3600000) : null;
    const riskScore = Math.max(0, Math.min(100,
      (isFailedStatus(latest.status) ? 45 : isWarningStatus(latest.status) ? 20 : 0) +
      ((staleHours ?? 999) > 24 ? 25 : 0) +
      ((failedRecent / Math.max(1, recent.length)) > 0.2 ? 20 : 0),
    ));
    const riskLevel = riskScore >= 80 ? 'critical' : riskScore >= 55 ? 'high' : riskScore >= 30 ? 'medium' : 'low';
    map.set(pid, {
      ...base,
      name: base.name || latest.scriptName || pid,
      owner: base.owner || latest.owner || 'unknown',
      criticality: base.criticality || latest.criticality || 'medium',
      lastRun: latest.startDate || null,
      lastStatus: normalizeRunStatus(latest.status) || 'UNKNOWN',
      successRate7d,
      staleHours,
      riskScore,
      riskLevel,
      placeholder: false,
    });
  }

  return [...map.values()].sort((a, b) =>
    Number(b.riskScore || 0) - Number(a.riskScore || 0) ||
    dateValue(b.lastRun) - dateValue(a.lastRun) ||
    String(a.pipelineId).localeCompare(String(b.pipelineId), 'pt-PT'));
}

function statusPillClass(status) {
  const normalized = normalizeRunStatus(status);
  if (normalized === 'OK') return 'status-ok';
  if (normalized === 'WARNING') return 'status-warning';
  if (normalized === 'NO_RUN' || normalized === 'INACTIVE' || normalized === 'UNKNOWN') return 'status-muted';
  return 'status-nok';
}

function renderPipelines() {
  const head = document.getElementById('pipelinesTableHead');
  const body = document.getElementById('pipelinesTableBody');
  if (!head || !body) return;
  head.innerHTML = `<tr><th>${t('colPipeline')}</th><th>${t('colOwner')}</th><th>${t('colCriticality')}</th><th>${t('colStatus')}</th><th>${t('colSuccess7d')}</th><th>${t('colRegression')}</th><th>${t('colStale')}</th><th>${t('colRisk')}</th></tr>`;
  const page = state.pipelinesView.slice(state.pipelinesOffset, state.pipelinesOffset + state.pipelinesLimit);
  body.innerHTML = page.map((p) => {
    const staleText = p.staleHours == null ? '-' : String(p.staleHours);
    const success = p.placeholder ? '-' : `${Number(p.successRate7d || 0).toFixed(1)}%`;
    const riskText = p.placeholder ? '-' : `${esc(p.riskScore)}`;
    const riskPill = p.placeholder ? '<span class="risk-pill risk-low">low</span>' : `<span class="risk-pill risk-${esc(p.riskLevel)}">${esc(p.riskLevel)}</span>`;
    return `<tr data-pipeline="${esc(p.pipelineId)}" class="${p.placeholder ? 'pipeline-placeholder-row' : ''}"><td data-label="Pipeline">${esc(p.name || p.pipelineId)}</td><td data-label="Owner">${esc(p.owner || 'unknown')}</td><td data-label="Criticidade">${esc(p.criticality || 'medium')}</td><td data-label="Estado"><span class="status-pill ${statusPillClass(p.lastStatus)}">${esc(p.lastStatus || 'UNKNOWN')}</span></td><td data-label="Sucesso 7d">${success}</td><td data-label="Regressão">${Number(p.regressionDelta || 0).toFixed(1)}pp</td><td data-label="Stale(h)">${staleText}</td><td data-label="Risk">${riskPill} ${riskText}</td></tr>`;
  }).join('');
  body.querySelectorAll('tr[data-pipeline]').forEach((row) => {
    row.addEventListener('click', () => {
      state.selectedPipelineId = row.dataset.pipeline;
      state.runsOffset = 0;
      applyRunFilters();
      renderRuns();
      renderLineage();
      switchView('runsView');
    });
  });
  setText('pipelinesPageInfo', page.length ? `${state.pipelinesOffset + 1}-${state.pipelinesOffset + page.length} de ${state.pipelinesView.length}` : 'Sem registos');
  const prev = document.getElementById('pipelinesPrevPage');
  const next = document.getElementById('pipelinesNextPage');
  if (prev) prev.disabled = state.pipelinesOffset <= 0;
  if (next) next.disabled = state.pipelinesOffset + state.pipelinesLimit >= state.pipelinesView.length;
}

function runCell(key, run) {
  if (key === 'status') {
    return `<span class="status-pill ${statusPillClass(run.status)}">${esc(run.status)}</span>`;
  }
  if (key === 'startDate' || key === 'endDate') return esc(fmt(run[key]));
  if (key === 'details') return `<button class="btn-detail" data-run="${run.id}">${t('colDetails')}</button>`;
  return esc(run[key] ?? '-');
}

function resolveRunLogFallback(run) {
  const details = state.details?.[String(run.id)] || state.details?.[run.id] || {};
  if (String(details.logMessage || '').trim()) {
    return { text: String(details.logMessage), source: 'details.logMessage' };
  }
  if (String(details.errorMessage || '').trim()) {
    return { text: String(details.errorMessage), source: 'details.errorMessage' };
  }
  const scripts = Array.isArray(state.pipelineScripts?.[run.pipelineId]) ? state.pipelineScripts[run.pipelineId] : [];
  const byRun = scripts.find((s) => Number(s.lastRunId || 0) === Number(run.id) && String(s.scriptLogMessage || '').trim());
  if (byRun) {
    return { text: String(byRun.scriptLogMessage), source: `pipeline_scripts:${byRun.path || 'script'}` };
  }
  const latestScript = [...scripts]
    .filter((s) => String(s.scriptLogMessage || '').trim())
    .sort((a, b) => dateValue(b.scriptLogUpdatedAt || b.lastSeenAt) - dateValue(a.scriptLogUpdatedAt || a.lastSeenAt))[0];
  if (latestScript) {
    return { text: String(latestScript.scriptLogMessage), source: `pipeline_scripts:${latestScript.path || 'script'}` };
  }
  if (String(run.errorPreview || '').trim()) {
    return { text: String(run.errorPreview), source: 'run.errorPreview' };
  }
  return { text: '', source: 'none' };
}

function renderModalRunLog(query = '') {
  const pre = document.getElementById('modalErrorLog');
  if (!pre) return;
  const raw = String(state._currentRunLogRaw || '');
  const needle = String(query || '').trim();
  if (!needle) {
    pre.textContent = raw;
    return;
  }
  const rx = new RegExp(`(${escapeRegex(needle)})`, 'ig');
  pre.innerHTML = esc(raw).replace(rx, '<mark class="log-hit">$1</mark>');
}

function escapeRegex(text) {
  return String(text || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function openRun(id) {
  const run = state.runsAll.find((r) => Number(r.id) === Number(id));
  if (!run) return;
  const runDetail = state.details?.[String(run.id)] || state.details?.[run.id] || {};
  setText('modalRunId', `#${run.id}`);
  setText('modalStatusText', run.status);
  const banner = document.getElementById('modalStatusBanner');
  if (banner) {
    banner.classList.remove('error', 'warning');
    const normalized = String(run.status || '').toUpperCase();
    if (normalized === 'WARNING') banner.classList.add('warning');
    else if (normalized !== 'OK') banner.classList.add('error');
  }
  const grid = document.getElementById('modalMetricsGrid');
  if (grid) {
    grid.innerHTML = [
      ['Pipeline', run.pipelineId],
      ['Requested by (actor)', run.requestedByActor || run.requestedBy],
      ['Requested by (SSO)', run.requestedBySSO || run.requestedByActor || run.requestedBy],
      ['Runner target', run.runnerHost],
      ['Host executado', run.hostname],
      ['SO', [run.osName, run.osRelease].filter(Boolean).join(' ') || run.osName],
      ['OS Platform', run.osPlatform],
      ['Início', fmt(run.startDate)],
      ['Fim', fmt(run.endDate)],
      ['Duração', run.durationLabel],
      ['CPU', run.cpuLabel],
      ['Memória', run.memLabel],
      ['Owner', run.owner],
      ['Criticidade', run.criticality],
    ].map(([k, v]) => `<div class="metric-card"><span class="metric-label">${esc(k)}</span><strong class="metric-value">${esc(v || '-')}</strong></div>`).join('');
  }
  renderRunSteps(runDetail);

  const resolved = resolveRunLogFallback(run);
  state._currentRunLogRaw = stripAnsi(resolved.text || '');
  state._currentRunLogSource = resolved.source || '-';
  const meta = document.getElementById('modalLogMeta');
  if (meta) meta.textContent = `Fonte: ${state._currentRunLogSource}`;
  const section = document.getElementById('modalErrorSection');
  if (section) section.style.display = state._currentRunLogRaw ? 'block' : 'none';
  const search = document.getElementById('modalLogSearch');
  if (search) search.value = '';
  renderModalRunLog('');

  const modal = document.getElementById('runDetailModal');
  if(window.MaiatronMotion&&typeof window.MaiatronMotion.toggleOverlay==='function'&&modal){
    void window.MaiatronMotion.toggleOverlay(modal,true,{openClass:'active'});
  }else{
    modal?.classList.add('active');
    modal?.setAttribute('aria-hidden','false');
  }
  revealOverseerSurface();
}

function renderRunSteps(detail) {
  const host = document.getElementById('modalStepsList');
  const section = document.getElementById('modalStepsSection');
  if (!host || !section) return;
  const steps = Array.isArray(detail?.steps) ? detail.steps : [];
  if (!steps.length) {
    section.style.display = 'none';
    host.innerHTML = '';
    return;
  }
  section.style.display = 'block';
  host.innerHTML = steps.map((step) => {
    const sid = String(step?.step_id || '-');
    const status = String(step?.status || 'UNKNOWN').toUpperCase();
    const cls = status === 'OK' ? 'status-ok' : status === 'WARNING' ? 'status-warning' : 'status-nok';
    const meta = [
      step?.description || '',
      step?.attempt ? `Tentativa ${step.attempt}` : '',
      step?.duration_sec ? `${Number(step.duration_sec).toFixed(2)}s` : '',
      `W:${Number(step?.warning_count || 0)} E:${Number(step?.error_count || 0)}`,
    ].filter(Boolean).join(' | ');
    const logText = String(step?.log_tail || step?.stderr_tail || step?.stdout_tail || step?.error_message || '').trim();
    return `<article class=\"run-step-item\">
      <div class=\"run-step-head\">
        <h5 class=\"run-step-title\">${esc(sid)}</h5>
        <span class=\"status-pill ${cls}\">${esc(status)}</span>
      </div>
      <p class=\"run-step-meta\">${esc(meta || '-')}</p>
      ${logText ? `<pre class=\"run-step-log\">${esc(stripAnsi(logText))}</pre>` : ''}
    </article>`;
  }).join('');
}

function closeModal() {
  const modal = document.getElementById('runDetailModal');
  if(window.MaiatronMotion&&typeof window.MaiatronMotion.toggleOverlay==='function'&&modal){
    void window.MaiatronMotion.toggleOverlay(modal,false,{openClass:'active'});
  }else{
    modal?.classList.remove('active');
    modal?.setAttribute('aria-hidden','true');
  }
}

state.compareWindow = localStorage.getItem('overseer_compare_window_v518') || '7d';
state.routeHydrated = false;
state.routeSyncSuspended = false;
state.focusLogAfterOpen = false;

function compareWindowMs(windowKey) {
  if (windowKey === '24h') return 24 * 60 * 60 * 1000;
  if (windowKey === '30d') return 30 * 24 * 60 * 60 * 1000;
  return 7 * 24 * 60 * 60 * 1000;
}

function severityLabel(level) {
  const normalized = String(level || '').toLowerCase();
  if (normalized === 'critical') return 'Crítica';
  if (normalized === 'high') return 'Alta';
  if (normalized === 'medium') return 'Atenção';
  return 'Controlada';
}

function pipelineSeverityMeta(pipeline) {
  const riskLevel = String(pipeline?.riskLevel || '').toLowerCase();
  const lastStatus = normalizeRunStatus(pipeline?.lastStatus || '');
  const staleHours = Number(pipeline?.staleHours ?? -1);
  if (riskLevel === 'critical' || lastStatus === 'FAILED') {
    return { level: 'critical', label: severityLabel('critical') };
  }
  if (riskLevel === 'high' || lastStatus === 'WARNING' || staleHours > 48) {
    return { level: 'high', label: severityLabel('high') };
  }
  if (riskLevel === 'medium' || staleHours > 24) {
    return { level: 'medium', label: severityLabel('medium') };
  }
  return { level: 'low', label: severityLabel('low') };
}

function runSeverityMeta(run) {
  const status = normalizeRunStatus(run?.status || '');
  const cpu = Number(run?.usageCPU || 0);
  const mem = Number(run?.usageMemoria || 0);
  if (status === 'FAILED') {
    return { level: 'critical', label: severityLabel('critical') };
  }
  if (status === 'WARNING' || cpu >= 85 || mem >= 85) {
    return { level: 'high', label: severityLabel('high') };
  }
  if (cpu >= 70 || mem >= 70) {
    return { level: 'medium', label: severityLabel('medium') };
  }
  return { level: 'low', label: severityLabel('low') };
}

function severityPillHtml(meta) {
  const info = meta && typeof meta === 'object' ? meta : { level: 'low', label: severityLabel('low') };
  return `<span class="severity-pill severity-pill--${esc(info.level)}">${esc(info.label)}</span>`;
}

function routeViewToUrl(viewId) {
  if (viewId === 'pipelinesView') return 'pipelines';
  if (viewId === 'runsView') return 'runs';
  if (viewId === 'lineageView') return 'lineage';
  if (viewId === 'insightsView') return 'insights';
  if (viewId === 'orchestratorView') return 'orchestrator';
  return 'dashboard';
}

function urlViewToRoute(viewName) {
  if (viewName === 'pipelines') return 'pipelinesView';
  if (viewName === 'runs') return 'runsView';
  if (viewName === 'lineage') return 'lineageView';
  if (viewName === 'insights') return 'insightsView';
  if (viewName === 'orchestrator') return 'orchestratorView';
  return 'dashboardView';
}

function buildOverseerDeepLink(overrides = {}) {
  const params = new URLSearchParams();
  const view = Object.prototype.hasOwnProperty.call(overrides, 'view')
    ? String(overrides.view || '')
    : routeViewToUrl(state.activeView || 'dashboardView');
  const pipeline = Object.prototype.hasOwnProperty.call(overrides, 'pipelineId')
    ? String(overrides.pipelineId || '')
    : String(state.selectedPipelineId || '');
  const runId = Object.prototype.hasOwnProperty.call(overrides, 'runId')
    ? String(overrides.runId || '')
    : '';
  const period = Object.prototype.hasOwnProperty.call(overrides, 'period')
    ? String(overrides.period || '')
    : String(state.runsTimeFilter || '');

  if (view) params.set('view', view);
  if (pipeline) params.set('pipeline', pipeline);
  if (runId) params.set('run', runId);
  if (period && period !== 'all') params.set('period', period);
  if (state.compareWindow) params.set('compare', state.compareWindow);

  const query = params.toString();
  return `${window.location.pathname}${query ? `?${query}` : ''}`;
}

function syncOverseerUrl(overrides = {}) {
  if (state.routeSyncSuspended) return;
  const nextUrl = buildOverseerDeepLink(overrides);
  window.history.replaceState(null, '', nextUrl);
}

function ensurePeriodComparisonCard() {
  if (document.getElementById('periodCompareCard')) return;
  const host = document.querySelector('.dash-col-right');
  if (!host) return;
  const card = document.createElement('article');
  card.id = 'periodCompareCard';
  card.className = 'chart-card period-compare-card';
  card.innerHTML = `
    <header class="chart-header">
      <h3>Comparação temporal</h3>
      <select id="periodCompareRange" class="chart-granularity" aria-label="Janela de comparação">
        <option value="24h">24 horas</option>
        <option value="7d">7 dias</option>
        <option value="30d">30 dias</option>
      </select>
    </header>
    <div id="periodCompareBody" class="period-compare-grid"></div>
  `;
  host.appendChild(card);
  const select = card.querySelector('#periodCompareRange');
  if (select) {
    select.value = state.compareWindow || '7d';
    select.addEventListener('change', () => {
      state.compareWindow = String(select.value || '7d');
      localStorage.setItem('overseer_compare_window_v518', state.compareWindow);
      renderPeriodComparison();
      syncOverseerUrl();
    });
  }
}

function periodRunsBetween(startTs, endTs) {
  return (state.runsAll || []).filter((run) => {
    const value = dateValue(run.startDate);
    return value >= startTs && value < endTs;
  });
}

function uniquePipelineCount(runs, predicate) {
  return new Set(
    (Array.isArray(runs) ? runs : [])
      .filter((run) => (typeof predicate === 'function' ? predicate(run) : true))
      .map((run) => String(run.pipelineId || '').trim())
      .filter(Boolean)
  ).size;
}

function periodDelta(current, previous, lowerIsBetter = false, suffix = '') {
  const diff = Number(current || 0) - Number(previous || 0);
  const positive = lowerIsBetter ? diff <= 0 : diff >= 0;
  const sign = diff > 0 ? '+' : '';
  return {
    text: `${sign}${Number.isFinite(diff) ? diff.toFixed(Math.abs(diff) >= 10 ? 0 : 1) : '0'}${suffix}`,
    className: positive ? 'is-positive' : 'is-negative'
  };
}

function renderPeriodComparison() {
  ensurePeriodComparisonCard();
  const host = document.getElementById('periodCompareBody');
  const select = document.getElementById('periodCompareRange');
  if (!host) return;
  if (select && select.value !== state.compareWindow) {
    select.value = state.compareWindow || '7d';
  }
  if (!Array.isArray(state.runsAll) || !state.runsAll.length) {
    host.innerHTML = '<div class="period-compare-empty">Sem runs suficientes para comparar períodos.</div>';
    return;
  }

  const now = Date.now();
  const windowMs = compareWindowMs(state.compareWindow || '7d');
  const currentRuns = periodRunsBetween(now - windowMs, now);
  const previousRuns = periodRunsBetween(now - (2 * windowMs), now - windowMs);
  const currentAvgDuration = avg(currentRuns.map((run) => Number(run.execTime || 0)));
  const previousAvgDuration = avg(previousRuns.map((run) => Number(run.execTime || 0)));
  const currentFailed = currentRuns.filter((run) => isFailedStatus(run.status)).length;
  const previousFailed = previousRuns.filter((run) => isFailedStatus(run.status)).length;
  const currentAttention = uniquePipelineCount(currentRuns, (run) => !isOkStatus(run.status));
  const previousAttention = uniquePipelineCount(previousRuns, (run) => !isOkStatus(run.status));

  /* sparkline buckets: split current window into 6 sub-periods */
  const bucketCount = 6;
  const bucketMs = windowMs / bucketCount;
  const sparkRuns = []; const sparkFails = []; const sparkDurations = []; const sparkAttention = [];
  for (var bi = 0; bi < bucketCount; bi++) {
    var bStart = now - windowMs + bi * bucketMs;
    var bEnd = bStart + bucketMs;
    var bRuns = periodRunsBetween(bStart, bEnd);
    sparkRuns.push(bRuns.length);
    sparkFails.push(bRuns.filter(function (r) { return isFailedStatus(r.status); }).length);
    sparkDurations.push(avg(bRuns.map(function (r) { return Number(r.execTime || 0); })));
    sparkAttention.push(uniquePipelineCount(bRuns, function (r) { return !isOkStatus(r.status); }));
  }

  const cards = [
    {
      label: 'Runs',
      value: currentRuns.length,
      delta: periodDelta(currentRuns.length, previousRuns.length, false, ''),
      spark: sparkRuns
    },
    {
      label: 'Falhas',
      value: currentFailed,
      delta: periodDelta(currentFailed, previousFailed, true, ''),
      spark: sparkFails
    },
    {
      label: 'Duração média',
      value: `${currentAvgDuration.toFixed(1)}s`,
      delta: periodDelta(currentAvgDuration, previousAvgDuration, true, 's'),
      spark: sparkDurations
    },
    {
      label: 'Pipelines com atenção',
      value: currentAttention,
      delta: periodDelta(currentAttention, previousAttention, true, ''),
      spark: sparkAttention
    }
  ];

  host.innerHTML = cards.map((card) => `
    <article class="period-compare-metric">
      <span class="period-compare-label">${esc(card.label)}</span>
      <strong class="period-compare-value">${esc(card.value)}</strong>
      <span class="period-compare-delta ${esc(card.delta.className)}">vs período anterior ${esc(card.delta.text)}</span>
      ${buildCompareSparkline(card.spark)}
    </article>
  `).join('');
}

function goToPipelineContext(pipelineId, viewId = 'runsView') {
  state.selectedPipelineId = String(pipelineId || '').trim();
  state.lineageSelectedPipelineId = state.selectedPipelineId;
  state.runsOffset = 0;
  applyRunFilters();
  applyPipelineFilters();
  renderRuns();
  renderPipelines();
  renderLineage();
  switchView(viewId);
}

async function openRunLog(runId) {
  state.focusLogAfterOpen = true;
  await openRun(runId);
}

function decoratePipelineTable() {
  const headRow = document.querySelector('#pipelinesTableHead tr');
  const rows = Array.from(document.querySelectorAll('#pipelinesTableBody tr[data-pipeline]'));
  if (!headRow || !rows.length) return;

  if (!headRow.querySelector('th[data-col="severity"]')) {
    const th = document.createElement('th');
    th.dataset.col = 'severity';
    th.textContent = 'Severidade';
    headRow.insertBefore(th, headRow.children[4] || null);
  }
  if (!headRow.querySelector('th[data-col="actions"]')) {
    const th = document.createElement('th');
    th.dataset.col = 'actions';
    th.textContent = 'Ações rápidas';
    headRow.appendChild(th);
  }

  const page = state.pipelinesView.slice(state.pipelinesOffset, state.pipelinesOffset + state.pipelinesLimit);
  rows.forEach((row, index) => {
    const pipeline = page[index];
    if (!pipeline) return;
    let severityCell = row.querySelector('.pipeline-severity-cell');
    if (!severityCell) {
      severityCell = document.createElement('td');
      severityCell.className = 'pipeline-severity-cell';
      severityCell.setAttribute('data-label', 'Severidade');
      row.insertBefore(severityCell, row.children[4] || null);
    }
    severityCell.innerHTML = severityPillHtml(pipelineSeverityMeta(pipeline));

    let actionsCell = row.querySelector('.pipeline-actions-cell');
    if (!actionsCell) {
      actionsCell = document.createElement('td');
      actionsCell.className = 'pipeline-actions-cell';
      actionsCell.setAttribute('data-label', 'Ações rápidas');
      row.appendChild(actionsCell);
    }
    actionsCell.innerHTML = `
      <div class="table-action-group">
        <button type="button" class="btn-detail" data-act="pipeline-runs">Runs</button>
        <button type="button" class="btn-detail" data-act="pipeline-lineage">Lineage</button>
        <a href="${esc(buildOverseerDeepLink({ view: 'runs', pipelineId: pipeline.pipelineId }))}" class="btn-detail btn-detail-link">Link</a>
      </div>
    `;
    actionsCell.querySelector('[data-act="pipeline-runs"]')?.addEventListener('click', (event) => {
      event.stopPropagation();
      goToPipelineContext(pipeline.pipelineId, 'runsView');
    });
    actionsCell.querySelector('[data-act="pipeline-lineage"]')?.addEventListener('click', (event) => {
      event.stopPropagation();
      goToPipelineContext(pipeline.pipelineId, 'lineageView');
    });
  });
}

function decorateRunsTable() {
  const headRow = document.querySelector('#tableHead tr');
  const rows = Array.from(document.querySelectorAll('#tableBody tr[data-run]'));
  if (!headRow || !rows.length) return;

  if (!headRow.querySelector('th[data-col="severity"]')) {
    const th = document.createElement('th');
    th.dataset.col = 'severity';
    th.textContent = 'Severidade';
    headRow.insertBefore(th, headRow.lastElementChild);
  }
  const lastHeader = headRow.lastElementChild;
  if (lastHeader) lastHeader.textContent = 'Ações rápidas';

  const page = state.runsView.slice(state.runsOffset, state.runsOffset + state.runsLimit);
  rows.forEach((row, index) => {
    const run = page[index];
    if (!run) return;
    const detailsCell = row.lastElementChild;
    if (!detailsCell) return;

    let severityCell = row.querySelector('.run-severity-cell');
    if (!severityCell) {
      severityCell = document.createElement('td');
      severityCell.className = 'run-severity-cell';
      severityCell.setAttribute('data-label', 'Severidade');
      row.insertBefore(severityCell, detailsCell);
    }
    severityCell.innerHTML = severityPillHtml(runSeverityMeta(run));

    detailsCell.classList.add('run-actions-cell');
    detailsCell.innerHTML = `
      <div class="table-action-group">
        <button type="button" class="btn-detail" data-act="run-detail">Detalhe</button>
        <button type="button" class="btn-detail" data-act="run-log">Logs</button>
        <button type="button" class="btn-detail" data-act="run-pipeline">Pipeline</button>
      </div>
    `;
    detailsCell.querySelector('[data-act="run-detail"]')?.addEventListener('click', async (event) => {
      event.stopPropagation();
      await openRun(run.id);
    });
    detailsCell.querySelector('[data-act="run-log"]')?.addEventListener('click', async (event) => {
      event.stopPropagation();
      await openRunLog(run.id);
    });
    detailsCell.querySelector('[data-act="run-pipeline"]')?.addEventListener('click', (event) => {
      event.stopPropagation();
      goToPipelineContext(run.pipelineId, 'runsView');
    });
  });
}

function decoratePipelineAssetCards() {
  const cards = Array.from(document.querySelectorAll('#pipelineAssetCards .pipeline-asset-card'));
  if (!cards.length) return;
  const pipelines = [...(state.pipelinesAll || [])].sort((a, b) => {
    const left = a.lastRun ? dateValue(a.lastRun) : 0;
    const right = b.lastRun ? dateValue(b.lastRun) : 0;
    return right - left;
  }).slice(0, cards.length);

  cards.forEach((card, index) => {
    const pipeline = pipelines[index];
    if (!pipeline) return;
    if (!card.querySelector('.pipeline-card-actions')) {
      const actions = document.createElement('div');
      actions.className = 'pipeline-card-actions';
      actions.innerHTML = `
        <button type="button" class="btn-detail" data-act="card-runs">Runs</button>
        <button type="button" class="btn-detail" data-act="card-lineage">Lineage</button>
      `;
      card.appendChild(actions);
      actions.querySelector('[data-act="card-runs"]')?.addEventListener('click', (event) => {
        event.stopPropagation();
        goToPipelineContext(pipeline.pipelineId, 'runsView');
      });
      actions.querySelector('[data-act="card-lineage"]')?.addEventListener('click', (event) => {
        event.stopPropagation();
        goToPipelineContext(pipeline.pipelineId, 'lineageView');
      });
    }
    let severity = card.querySelector('.pipeline-card-severity');
    if (!severity) {
      severity = document.createElement('div');
      severity.className = 'pipeline-card-severity';
      const header = card.querySelector('.pac-header');
      header?.appendChild(severity);
    }
    severity.innerHTML = severityPillHtml(pipelineSeverityMeta(pipeline));
  });
}

function decorateOverseerSurfaces() {
  decoratePipelineTable();
  decorateRunsTable();
  decoratePipelineAssetCards();
}

function applyOverseerRoute(force = false) {
  if (state.routeHydrated && !force) return;
  const params = new URLSearchParams(window.location.search);
  const requestedView = urlViewToRoute(String(params.get('view') || ''));
  const pipelineId = String(params.get('pipeline') || '').trim();
  const runId = Number(params.get('run') || 0);
  const period = String(params.get('period') || '').trim();
  const compare = String(params.get('compare') || '').trim();

  state.routeSyncSuspended = true;
  try {
    if (period) {
      state.runsTimeFilter = period;
      const timeFilter = document.getElementById('timeFilter');
      if (timeFilter) timeFilter.value = period;
    }
    if (compare) {
      state.compareWindow = compare;
      localStorage.setItem('overseer_compare_window_v518', state.compareWindow);
      const compareSelect = document.getElementById('periodCompareRange');
      if (compareSelect) compareSelect.value = compare;
    }
    if (pipelineId) {
      state.selectedPipelineId = pipelineId;
      state.lineageSelectedPipelineId = pipelineId;
    }
    applyRunFilters();
    applyPipelineFilters();
    renderRuns();
    renderPipelines();
    renderLineage();
    if (requestedView) {
      switchView(requestedView);
    }
    if (runId > 0) {
      void openRun(runId);
    }
  } finally {
    state.routeHydrated = true;
    state.routeSyncSuspended = false;
  }
}

const baseRenderAll = renderAll;
renderAll = function renderAllWithV518() {
  baseRenderAll();
  ensurePeriodComparisonCard();
  renderPeriodComparison();
  decorateOverseerSurfaces();
  applyOverseerRoute();
};

const baseSwitchView = switchView;
switchView = function switchViewWithDeepLink(viewId) {
  baseSwitchView(viewId);
  syncOverseerUrl();
};

const baseOpenRun = openRun;
openRun = async function openRunWithDeepLink(id) {
  await baseOpenRun(id);
  const run = (state.runsAll || []).find((item) => Number(item.id) === Number(id));
  if (run?.pipelineId) {
    state.selectedPipelineId = run.pipelineId;
  }
  syncOverseerUrl({ view: 'runs', pipelineId: run?.pipelineId || state.selectedPipelineId, runId: id });
  if (state.focusLogAfterOpen) {
    state.focusLogAfterOpen = false;
    document.getElementById('modalErrorSection')?.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }
};

const baseCloseModal = closeModal;
closeModal = function closeModalWithDeepLink() {
  baseCloseModal();
  syncOverseerUrl({ runId: '' });
};

/* ===== v5.5 Feature Additions ===== */

/* -- CSV Export -- */
document.getElementById('btnCsvExport')?.addEventListener('click', () => {
  const runs = state.runsView || [];
  if (!runs.length) { showToast('Sem dados para exportar', 'error'); return; }
  const cols = ['id', 'pipelineId', 'status', 'startDate', 'endDate', 'durationLabel', 'cpuLabel', 'memLabel', 'owner', 'criticality', 'requestedByActor', 'hostname', 'runnerHost'];
  const header = cols.join(';');
  const rows = runs.map(r => cols.map(c => {
    const val = String(r[c] ?? '').replace(/"/g, '""');
    return val.includes(';') || val.includes('"') || val.includes('\n') ? `"${val}"` : val;
  }).join(';'));
  const bom = '\uFEFF';
  const blob = new Blob([bom + header + '\n' + rows.join('\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `overseer-runs-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast(`Exportadas ${runs.length} runs`, 'success');
});

/* -- Advanced Filters (date range, owner, criticality) -- */
function populateOwnerFilter() {
  const sel = document.getElementById('filterOwner');
  if (!sel) return;
  const owners = new Set((state.runsAll || []).map(r => r.owner).filter(Boolean));
  const current = sel.value;
  const opts = ['<option value="">Todos</option>'];
  [...owners].sort().forEach(o => { opts.push(`<option value="${esc(o)}">${esc(o)}</option>`); });
  sel.innerHTML = opts.join('');
  if (current) sel.value = current;
}

const baseApplyRunFilters = applyRunFilters;
applyRunFilters = function applyRunFiltersAdvanced() {
  baseApplyRunFilters();
  let runs = state.runsView;
  const dateFrom = document.getElementById('filterDateFrom')?.value;
  const dateTo = document.getElementById('filterDateTo')?.value;
  const owner = document.getElementById('filterOwner')?.value;
  const criticality = document.getElementById('filterCriticality')?.value;
  if (dateFrom) {
    const from = new Date(dateFrom).getTime();
    if (Number.isFinite(from)) runs = runs.filter(r => dateValue(r.startDate) >= from);
  }
  if (dateTo) {
    const to = new Date(dateTo).getTime() + 86400000;
    if (Number.isFinite(to)) runs = runs.filter(r => dateValue(r.startDate) < to);
  }
  if (owner) runs = runs.filter(r => r.owner === owner);
  if (criticality) runs = runs.filter(r => r.criticality === criticality);
  state.runsView = runs;
};

['filterDateFrom', 'filterDateTo', 'filterOwner', 'filterCriticality'].forEach(id => {
  document.getElementById(id)?.addEventListener('change', () => {
    state.runsOffset = 0;
    applyRunFilters();
    renderRuns();
  });
});

document.getElementById('btnClearFilters')?.addEventListener('click', () => {
  state.q = '';
  state.runsStatus = '';
  state.runsTimeFilter = 'all';
  state.selectedPipelineId = '';
  const q = document.getElementById('q'); if (q) q.value = '';
  const tf = document.getElementById('timeFilter'); if (tf) tf.value = 'all';
  const df = document.getElementById('filterDateFrom'); if (df) df.value = '';
  const dt = document.getElementById('filterDateTo'); if (dt) dt.value = '';
  const fo = document.getElementById('filterOwner'); if (fo) fo.value = '';
  const fc = document.getElementById('filterCriticality'); if (fc) fc.value = '';
  state.runsOffset = 0;
  applyRunFilters();
  applyPipelineFilters();
  renderRuns();
  renderPipelines();
  updateSearchCounter();
});

/* -- Retry Run -- */
let _currentModalRunId = null;

const baseOpenRunForRetry = openRun;
openRun = async function openRunWithRetry(id) {
  _currentModalRunId = id;
  await baseOpenRunForRetry(id);
  const run = (state.runsAll || []).find(r => Number(r.id) === Number(id));
  const retryBtn = document.getElementById('modalRetryRunBtn');
  if (retryBtn) {
    const canRetry = run?.pipelineId && canUserRunPipeline(run.pipelineId);
    retryBtn.style.display = canRetry ? '' : 'none';
  }
};

document.getElementById('modalRetryRunBtn')?.addEventListener('click', async () => {
  const run = (state.runsAll || []).find(r => Number(r.id) === Number(_currentModalRunId));
  if (!run?.pipelineId) { showToast('Pipeline não identificada', 'error'); return; }
  if (!canUserRunPipeline(run.pipelineId)) { showToast('Sem permissão para executar esta pipeline', 'error'); return; }
  if (!confirm(`Re-executar pipeline "${run.pipelineId}"?`)) return;
  try {
    const resp = await fetch(`${apiBaseUrl()}?action=trigger_enqueue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ pipeline_id: run.pipelineId }),
    });
    const data = await resp.json();
    if (data.ok) {
      showToast(`Pipeline "${run.pipelineId}" enqueued para execução`, 'success');
      closeModal();
    } else {
      showToast(data.error || 'Erro ao trigger pipeline', 'error');
    }
  } catch (err) {
    showToast('Erro de rede ao retry', 'error');
  }
});

/* -- Real-time Toast on Status Change -- */
let _previousRunStatuses = new Map();

function checkStatusChanges() {
  const currentStatuses = new Map();
  for (const run of (state.runsAll || []).slice(0, 200)) {
    currentStatuses.set(Number(run.id), run.status);
  }
  if (_previousRunStatuses.size > 0) {
    for (const [id, newStatus] of currentStatuses) {
      const oldStatus = _previousRunStatuses.get(id);
      if (oldStatus && oldStatus !== newStatus) {
        const run = state.runsAll.find(r => Number(r.id) === id);
        const pipeline = run?.pipelineId || 'Unknown';
        const type = newStatus === 'OK' ? 'success' : newStatus === 'WARNING' ? 'warning' : 'error';
        showToast(`${pipeline} #${id}: ${oldStatus} → ${newStatus}`, type);
      }
    }
  }
  _previousRunStatuses = currentStatuses;
}

const baseBuildModelFromPayload = buildModelFromPayload;
buildModelFromPayload = function buildModelWithStatusCheck() {
  baseBuildModelFromPayload();
  checkStatusChanges();
  populateOwnerFilter();
};

/* -- Pipeline Health Check -- */
function renderHealthChecks() {
  const grid = document.getElementById('healthCheckGrid');
  const panel = document.getElementById('healthCheckPanel');
  if (!grid || !panel) return;
  const pipelines = state.pipelinesAll || [];
  if (!pipelines.length) { panel.style.display = 'none'; return; }
  panel.style.display = '';
  grid.innerHTML = pipelines.slice(0, 30).map(p => {
    const staleHrs = p.staleHours ?? null;
    const isStale = staleHrs !== null && staleHrs > 24;
    const isFailed = p.lastStatus === 'NOK' || p.lastStatus === 'FAILED';
    const isOk = p.lastStatus === 'OK';
    const cls = isFailed ? 'health-card--critical' : isStale ? 'health-card--stale' : isOk ? 'health-card--ok' : 'health-card--unknown';
    const lastRunText = p.lastRun ? fmt(p.lastRun) : 'Sem runs';
    return `<div class="health-card ${cls}" data-pipeline="${esc(p.pipelineId)}">
      <div class="health-card-name">${esc(p.name || p.pipelineId)}</div>
      <div class="health-card-status"><span class="status-pill ${statusPillClass(p.lastStatus)}">${esc(p.lastStatus || 'N/A')}</span></div>
      <div class="health-card-meta">${lastRunText}${staleHrs !== null ? ` (${staleHrs}h)` : ''}</div>
      <div class="health-card-rate">${p.placeholder ? '-' : `${Number(p.successRate7d || 0).toFixed(0)}% (7d)`}</div>
    </div>`;
  }).join('');
  grid.querySelectorAll('.health-card[data-pipeline]').forEach(card => {
    card.addEventListener('click', () => {
      goToPipelineContext(card.dataset.pipeline, 'runsView');
    });
  });
}

document.getElementById('healthCheckRefreshBtn')?.addEventListener('click', () => {
  renderHealthChecks();
  showToast('Health check atualizado', 'info');
});

const baseRenderAllV55 = renderAll;
renderAll = function renderAllWithV55Features() {
  baseRenderAllV55();
  renderHealthChecks();
};
