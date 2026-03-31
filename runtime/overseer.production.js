const CONFIG={themeKey:'overseer_theme',refreshMs:30000,payloadUrl:'overseer_payload.json',detailsUrl:'overseer_details.json',authConfigUrl:'../../config/auth.local.json',triggerKey:'overseer_trigger_history_v1',inflightKey:'overseer_inflight_v1'};

/* ====== i18n — PT-PT / EN ====== */
const LANG={
pt:{
  brandTag:'Monitorização operacional de pipelines',
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
  colId:'#',colPipeline:'Pipeline',colStatus:'Estado',colHost:'Host',colOS:'SO',colStart:'Início',colEnd:'Fim',colDuration:'Duração',colCPU:'CPU',colMem:'Memória',colDetails:'Detalhes',
  colOwner:'Owner',colCriticality:'Criticidade',colSuccess7d:'Sucesso 7d',colRegression:'Regressão',colStale:'Stale(h)',colRisk:'Risco',colSchedule:'Schedule',colPermission:'Permissão',colActions:'Ações',
  pipeTitle:'Pipelines (prioridade operacional)',orchTitle:'Orquestração de Pipelines',orchRunsTitle:'Runs de Orquestração',
  filterAllRisks:'Todos os riscos',filterCritical:'Crítico',filterHigh:'Alto',filterMedium:'Médio',filterLow:'Baixo',
  filterPeriod:'Período de runs',filter24h:'Últimas 24 horas',filter7d:'Últimos 7 dias',filter30d:'Últimos 30 dias',filterAll:'Todos',
  prev:'Anterior',next:'Seguinte',noRecords:'Sem registos',lines:'Linhas',
  alertsRecent:'Alertas recentes (NOK)',pipeFailures:'Pipelines com mais falhas (7 dias)',incidentsTimeline:'Timeline de incidentes',topRegressions:'Top regressões',quickActions:'Ações rápidas',
  btnShowNok:'Ver NOK (7d)',btnOpenNok:'Abrir último NOK',btnResetOverview:'Reset overview',
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
  noNoKFilter:'Sem runs NOK no filtro atual',
  copied:'Comando copiado para terminal',triggerOk:'Run now enviado com sucesso',triggerFail:'Erro ao enviar trigger. Comando CLI copiado.',
  schedInvalidMsg:'Schedule inválido. Use expressão cron (ex: 30 7 * * *) ou "manual".',
  schedChanged:'alterado com sucesso',schedFail:'Erro ao enviar trigger de schedule. Comando CLI copiado.',
  noPerm:'Sem permissão para executar este pipeline',noPermShort:'Sem permissão — contacta o owner',
  running:'A executar agora',
  results:'resultado',resultsPlural:'resultados',
  all:'Todos',manual:'Manual',paused:'Paused',
},
en:{
  brandTag:'Operational pipeline monitoring',
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
  colId:'#',colPipeline:'Pipeline',colStatus:'Status',colHost:'Host',colOS:'OS',colStart:'Start',colEnd:'End',colDuration:'Duration',colCPU:'CPU',colMem:'Memory',colDetails:'Details',
  colOwner:'Owner',colCriticality:'Criticality',colSuccess7d:'Success 7d',colRegression:'Regression',colStale:'Stale(h)',colRisk:'Risk',colSchedule:'Schedule',colPermission:'Permission',colActions:'Actions',
  pipeTitle:'Pipelines (operational priority)',orchTitle:'Pipeline Orchestration',orchRunsTitle:'Orchestration Runs',
  filterAllRisks:'All risks',filterCritical:'Critical',filterHigh:'High',filterMedium:'Medium',filterLow:'Low',
  filterPeriod:'Run period',filter24h:'Last 24 hours',filter7d:'Last 7 days',filter30d:'Last 30 days',filterAll:'All',
  prev:'Previous',next:'Next',noRecords:'No records',lines:'Rows',
  alertsRecent:'Recent alerts (NOK)',pipeFailures:'Pipelines with most failures (7 days)',incidentsTimeline:'Incident timeline',topRegressions:'Top regressions',quickActions:'Quick actions',
  btnShowNok:'Show NOK (7d)',btnOpenNok:'Open latest NOK',btnResetOverview:'Reset overview',
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
  noNoKFilter:'No NOK runs in current filter',
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
async function loadMaiatronUsers() { try { const r = await fetch('get_users.php'); if(r.ok) { const d = await r.json(); if(d.status==='ok') maiatronUsers = d.users; } } catch(e) {} }
const state={user:null,payload:null,details:{},runsAll:[],runsView:[],pipelinesAll:[],pipelinesView:[],overview:null,lineageNodes:[],moduleLineage:{},pipelineScripts:{},orchestratorPipelines:[],orchestratorTriggers:[],orchRuns:[],pipelinePermissions:{},pendingScheduleMutations:{},q:'',runsStatus:'',runsTimeFilter:'all',selectedPipelineId:'',lineageSelectedPipelineId:'',runsLimit:25,runsOffset:0,runsSortKey:'startDate',runsSortDir:'desc',pipelinesLimit:25,pipelinesOffset:0,orchLimit:20,orchOffset:0,historyGranularity:'day',lang:localStorage.getItem('overseer_lang')||'pt'};
let refreshTimer=null,countdownTimer=null,historyChart=null,healthChart=null,execTimeTrendChart=null,searchDebounceTimer=null;
const RUN_COLUMNS=[['id','colId'],['pipelineId','colPipeline'],['status','colStatus'],['hostname','colHost'],['osName','colOS'],['startDate','colStart'],['endDate','colEnd'],['durationLabel','colDuration'],['cpuLabel','colCPU'],['memLabel','colMem'],['details','colDetails']];

document.addEventListener('DOMContentLoaded',async()=>{await loadMaiatronUsers();initTheme();initUi();initAuthUi();window.MaiatronAuthUI?.mount&&window.MaiatronAuthUI.mount({configUrl:CONFIG.authConfigUrl,toast:showToast,onAuthLost:()=>location.reload()});const s=await loadPersistedSession();if(s){state.user={username:s.username,displayName:s.displayName||s.username};showMainApp();await refreshAllData();startAutoRefresh();return;}showLoginScreen();});

function initUi(){setText('currentYear',new Date().getFullYear());document.getElementById('themeToggle')?.addEventListener('click',onToggleTheme);document.getElementById('loginThemeToggle')?.addEventListener('click',onToggleTheme);document.getElementById('refreshBtn')?.addEventListener('click',manualRefresh);document.querySelectorAll('.nav-tab').forEach((b)=>b.addEventListener('click',()=>switchView(b.dataset.view)));
document.getElementById('modalCloseBtn')?.addEventListener('click',closeModal);document.getElementById('runDetailOverlay')?.addEventListener('click',closeModal);
document.addEventListener('keydown',(e)=>{if(e.key==='Escape'){closeModal();closeMetricsDrawer();}});
document.getElementById('q')?.addEventListener('input',(e)=>{const raw=(e.target.value||'').trim();if(searchDebounceTimer)clearTimeout(searchDebounceTimer);searchDebounceTimer=setTimeout(()=>{state.q=raw;state.selectedPipelineId='';state.runsOffset=0;applyRunFilters();applyPipelineFilters();renderRuns();renderPipelines();updateSearchCounter();if(state.q)switchView('runsView');},150);});
document.getElementById('timeFilter')?.addEventListener('change',(e)=>{state.runsTimeFilter=e.target.value||'all';state.runsOffset=0;applyRunFilters();renderRuns();});
document.getElementById('pageSize')?.addEventListener('change',(e)=>{state.runsLimit=Number(e.target.value)||25;state.runsOffset=0;renderRuns();});
document.getElementById('prevPage')?.addEventListener('click',()=>{state.runsOffset=Math.max(0,state.runsOffset-state.runsLimit);renderRuns();});
document.getElementById('nextPage')?.addEventListener('click',()=>{if(state.runsOffset+state.runsLimit>=state.runsView.length)return;state.runsOffset+=state.runsLimit;renderRuns();});
document.getElementById('pipelinesPrevPage')?.addEventListener('click',()=>{state.pipelinesOffset=Math.max(0,state.pipelinesOffset-state.pipelinesLimit);renderPipelines();});
document.getElementById('pipelinesNextPage')?.addEventListener('click',()=>{if(state.pipelinesOffset+state.pipelinesLimit>=state.pipelinesView.length)return;state.pipelinesOffset+=state.pipelinesLimit;renderPipelines();});
document.getElementById('pipelineRiskFilter')?.addEventListener('change',()=>{state.pipelinesOffset=0;applyPipelineFilters();renderPipelines();});
document.getElementById('historyGranularity')?.addEventListener('change',(e)=>{state.historyGranularity=e.target.value;renderCharts();});
document.getElementById('quickFilter')?.addEventListener('change',(e)=>{const v=e.target.value;state.q='';state.runsStatus=(v==='nok_24h'||v==='nok_7d')?'NOK':'';if(v==='nok_24h'){state.runsTimeFilter='24h';}else if(v==='nok_7d'){state.runsTimeFilter='7d';}else{state.runsTimeFilter='all';}const tf=document.getElementById('timeFilter');if(tf)tf.value=state.runsTimeFilter;applyRunFilters();if(v==='high_cpu')state.runsView=state.runsView.filter((r)=>Number(r.usageCPU||0)>80);renderRuns();switchView('runsView');});
document.getElementById('qaShowNok')?.addEventListener('click',()=>{state.runsStatus='NOK';state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');});
document.getElementById('qaOpenLatestNok')?.addEventListener('click',async()=>{const i=state.runsView.find((r)=>String(r.status||'').toUpperCase()==='NOK');if(!i){showToast(t('noNoKFilter'),'info');return;}await openRun(i.id);});
document.getElementById('qaResetOverview')?.addEventListener('click',()=>{state.q='';state.runsStatus='';state.selectedPipelineId='';state.lineageSelectedPipelineId='';applyRunFilters();applyPipelineFilters();renderAll();switchView('dashboardView');});
document.getElementById('orchRefreshBtn')?.addEventListener('click',()=>{loadTriggerHistory();renderOrchestratorRuns();showToast(t('orchLocalUpdated'),'success');});
document.getElementById('orchPrevPage')?.addEventListener('click',()=>{state.orchOffset=Math.max(0,state.orchOffset-state.orchLimit);renderOrchestratorRuns();});
document.getElementById('orchNextPage')?.addEventListener('click',()=>{if(state.orchOffset+state.orchLimit>=state.orchRuns.length)return;state.orchOffset+=state.orchLimit;renderOrchestratorRuns();});
document.getElementById('metricsHelpHeaderBtn')?.addEventListener('click',toggleMetricsDrawer);
document.getElementById('metricsDrawerClose')?.addEventListener('click',toggleMetricsDrawer);
document.getElementById('metricsDrawerOverlay')?.addEventListener('click',toggleMetricsDrawer);
document.querySelectorAll('.signal-card').forEach((el)=>el.addEventListener('click',()=>{const sig=el.dataset.signal;if(sig==='atRisk'){state.pipelinesOffset=0;const rf=document.getElementById('pipelineRiskFilter');if(rf)rf.value='critical';applyPipelineFilters();renderPipelines();switchView('pipelinesView');}else if(sig==='stale'){state.runsTimeFilter='24h';state.runsStatus='';state.runsOffset=0;const tf=document.getElementById('timeFilter');if(tf)tf.value='24h';applyRunFilters();renderRuns();switchView('runsView');}else if(sig==='regressions'){state.pipelinesOffset=0;applyPipelineFilters();renderPipelines();switchView('pipelinesView');}else if(sig==='volume'){state.runsTimeFilter='24h';state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');}}));
document.getElementById('healthHighlight')?.addEventListener('click',()=>{switchView('insightsView');});
applyLangToStaticElements();}
function initAuthUi(){const f=document.getElementById('loginForm');f?.addEventListener('submit',async(e)=>{e.preventDefault();const u=(document.getElementById('username')?.value||'').trim();const p=document.getElementById('password')?.value||'';const rememberSession=document.getElementById('rememberSession')?.checked??true;const rememberUsername=document.getElementById('rememberUsername')?.checked??false;const b=f.querySelector('.login-btn');b?.classList.add('loading');try{const result=await window.MaiatronAuth.login(u,p,{configUrl:CONFIG.authConfigUrl,rememberSession});if(!result.ok){showLoginError('Utilizador ou password incorretos');return;}window.MaiatronAuth.saveLoginPreferences({rememberUsername,rememberSession,username:u});state.user={username:result.session.username,displayName:(window.MaiatronAuth?.getDisplayName?window.MaiatronAuth.getDisplayName(result.session):result.session.displayName||result.session.username)};window.MaiatronAuthUI?.setSession(result.session||null);clearLoginError();showMainApp();await refreshAllData();startAutoRefresh();}finally{b?.classList.remove('loading');}});
document.getElementById('logoutBtn')?.addEventListener('click',async()=>{await window.MaiatronAuth.logout({configUrl:CONFIG.authConfigUrl});window.MaiatronAuthUI?.setSession(null);stopAutoRefresh();showLoginScreen();});
document.getElementById('forgotPasswordBtn')?.addEventListener('click',async()=>{if(!window.MaiatronAuth||typeof window.MaiatronAuth.forgotPassword!=='function'){showToast('Funcionalidade indisponível','error');return;}const cu=(document.getElementById('username')?.value||'').trim();const u=cu||window.prompt('Indique o utilizador para reset da password:');if(!u)return;const c=window.confirm('Vai gerar uma nova password temporária para "'+u+'". Continuar?');if(!c)return;const r=await window.MaiatronAuth.forgotPassword(u,{configUrl:CONFIG.authConfigUrl});if(!r.ok){showToast(r.reason==='invalid_user'?'Utilizador inexistente ou inativo.':'Erro ao recuperar password','error');return;}const pi=document.getElementById('password');if(pi){pi.value=r.temporaryPassword||'';pi.focus();pi.select();}showToast('Password temporária gerada. Faça login com a nova password.','success');});
syncLoginPreferencesUi();}
function syncLoginPreferencesUi(){if(!window.MaiatronAuth?.getLoginPreferences)return;const prefs=window.MaiatronAuth.getLoginPreferences();const ru=document.getElementById('rememberUsername');const rs=document.getElementById('rememberSession');const ui=document.getElementById('username');if(ru)ru.checked=prefs.rememberUsername;if(rs)rs.checked=prefs.rememberSession;if(ui&&prefs.username)ui.value=prefs.username;}

async function loadPersistedSession(){const session=await window.MaiatronAuth.getSession({configUrl:CONFIG.authConfigUrl});window.MaiatronAuthUI?.setSession(session||null);if(!session)return null;return {username:session.username,displayName:(window.MaiatronAuth?.getDisplayName?window.MaiatronAuth.getDisplayName(session):session.displayName||session.username)};}

async function refreshAllData(){try{const [payload,details]=await Promise.all([loadPayload(),loadDetails()]);if(!payload||!Array.isArray(payload.fields)||!Array.isArray(payload.rows)){console.warn('Payload inválido recebido, mantendo dados atuais');showToast(t('invalidPayload'),'warning');return;}state.payload=payload;state.details=details;buildModelFromPayload();renderAll();showToast(t('dataUpdated'),'success');}catch(e){console.error('refreshAllData error:',e);showToast(t('dataFail'),'error');}}async function manualRefresh(){const btn=document.getElementById('refreshBtn');btn?.classList.add('loading');stopAutoRefresh();try{await refreshAllData();}finally{btn?.classList.remove('loading');startAutoRefresh();}}
async function loadPayload(){const u=window.OVERSEER_ASSETS?.payloadUrl||CONFIG.payloadUrl;const r=await fetch(`${u}?t=${Date.now()}`,{cache:'no-store'});if(!r.ok)throw new Error(`Falha ao carregar payload (${r.status})`);return await r.json();}
async function loadDetails(){const u=window.OVERSEER_ASSETS?.detailsUrl||CONFIG.detailsUrl;try{const r=await fetch(`${u}?t=${Date.now()}`,{cache:'no-store'});if(!r.ok)return {};return await r.json();}catch{return {};}}

function buildModelFromPayload(){const fields=Array.isArray(state.payload?.fields)?state.payload.fields:[];const rows=Array.isArray(state.payload?.rows)?state.payload.rows:[];const mapped=rows.map((row)=>rowToObj(fields,row)).filter((x)=>x&&x.id!=null);
state.runsAll=mapped.map((r)=>enrichRun(r)).sort((a,b)=>dateValue(b.startDate)-dateValue(a.startDate));
state.overview=state.payload?.overview||deriveOverview(state.runsAll,state.payload?.summary||{});
state.pipelinesAll=state.payload?.pipelines||derivePipelines(state.runsAll);
state.lineageNodes=state.payload?.lineage?.nodes||deriveLineage(state.pipelinesAll);state.moduleLineage=state.payload?.module_lineage||{};state.pipelineScripts=state.payload?.pipeline_scripts||{};
state.orchestratorPipelines=Array.isArray(state.payload?.pipeline_catalog)?state.payload.pipeline_catalog:[];
state.orchestratorTriggers=Array.isArray(state.payload?.orchestrator_triggers)?state.payload.orchestrator_triggers:[];
state.pipelinePermissions=state.payload?.pipeline_permissions||{};
const dbRuns=Array.isArray(state.payload?.orchestrator_runs)?state.payload.orchestrator_runs:[];
const inflight=pruneInflight(dbRuns);
const inflightRows=inflight.map((e)=>normalizeOrchestratorRow({runId:e.triggerId,pipelineId:e.pipelineId,status:'running',source:'frontend',createdAt:new Date(e.startedAt).toISOString()}));
const allOrch=[...dbRuns,...inflightRows].map((r)=>normalizeOrchestratorRow(r));const orchSeen=new Set();state.orchRuns=[];for(const r of allOrch){const key=r.runId||JSON.stringify(r);if(!orchSeen.has(key)){orchSeen.add(key);state.orchRuns.push(r);}}state.orchRuns.sort((a,b)=>dateValue(b.createdAt||b.requested_at)-dateValue(a.createdAt||a.requested_at));
state.runningPipelines=new Set();for(const r of dbRuns){if(String(r.status||'').toLowerCase()==='running'&&(r.pipelineId||r.pipeline_id))state.runningPipelines.add(r.pipelineId||r.pipeline_id);}
for(const e of inflight){state.runningPipelines.add(e.pipelineId);}
rehydratePendingScheduleMutations();
applyRunFilters();applyPipelineFilters();}

function rowToObj(fields,row){const o={};fields.forEach((f,i)=>{o[f]=row[i];});return o;}
function enrichRun(run){const c={...run};c.id=Number(c.id||0);c.pipelineId=c.pipelineId||c.pipeline_id||c.scriptName||'pipeline-sem-nome';c.status=String(c.status||'UNKNOWN').toUpperCase();c.execTime=toNum(c.execTime);c.usageCPU=toNum(c.usageCPU);c.usageMemoria=toNum(c.usageMemoria);c.durationLabel=c.durationLabel||formatDuration(c.execTime);c.cpuLabel=c.cpuLabel||`${c.usageCPU.toFixed(1)}%`;c.memLabel=c.memLabel||`${c.usageMemoria.toFixed(1)} MB`;c.owner=c.owner||'unknown';c.criticality=c.criticality||'medium';c.errorPreview=c.errorPreview||'';c.run_id_pipeline=c.run_id_pipeline||`${c.pipelineId}#${c.id}`;c.osName=c.osName||'desconhecido';const d=state.details?.[String(c.id)]||state.details?.[c.id]||null;if(d?.errorMessage&&!c.errorMessage)c.errorMessage=d.errorMessage;if(d?.run_id_pipeline)c.run_id_pipeline=d.run_id_pipeline;return c;}
function deriveOverview(runs,summary){const total=runs.length,ok=runs.filter((r)=>r.status==='OK').length,nok=runs.filter((r)=>r.status==='NOK').length;const grouped=groupByPipeline(runs);let atRisk=0,stale=0,failed=0,regressions=0;for(const list of Object.values(grouped)){if(!list.length)continue;const latest=list[0];const staleHours=Math.floor((Date.now()-dateValue(latest.startDate))/3600000);const isStale=!latest.startDate||staleHours>24;const isFailed=latest.status==='NOK';const nokRate=list.slice(0,7).filter((x)=>x.status==='NOK').length/Math.max(1,Math.min(7,list.length));if(isFailed)failed+=1;if(isStale)stale+=1;if(nokRate>0.2)regressions+=1;if(isFailed||isStale||nokRate>0.2)atRisk+=1;}
const immediate=runs.filter((r)=>r.status==='NOK').slice(0,5).map((r)=>({pipelineId:r.pipelineId,name:r.scriptName,runId:r.id,run_id_pipeline:r.run_id_pipeline,reason:'última run NOK',when:r.startDate}));
const incidents=runs.filter((r)=>r.status==='NOK'||!r.startDate||Math.floor((Date.now()-dateValue(r.startDate))/3600000)>24).slice(0,10).map((r)=>({pipelineId:r.pipelineId,name:r.scriptName,runId:r.id,run_id_pipeline:r.run_id_pipeline,reason:r.status==='NOK'?'falha':'stale',when:r.startDate}));
return {generatedAt:summary.generated_at||new Date().toISOString(),globalKpis:{totalRuns:Number(summary.total_runs||total),okRuns:Number(summary.ok_runs||ok),nokRuns:Number(summary.nok_runs||nok),successRate:Number(summary.success_rate||(total?(ok/total)*100:100)),avgExecTime:Number(summary.avg_exec_time||avg(runs.map((r)=>r.execTime))),avgCpu:Number(summary.avg_cpu||avg(runs.map((r)=>r.usageCPU))),avgMem:Number(summary.avg_mem||avg(runs.map((r)=>r.usageMemoria))),p95ExecTime:Number(summary.p95_exec_time||percentile(runs.map((r)=>r.execTime),0.95))},operationalSignals:{pipelineCount:Number(summary.pipeline_count||Object.keys(grouped).length),atRisk:Number(summary.at_risk||atRisk),stale:Number(summary.stale||stale),regressions:Number(summary.regressions||regressions),failed,volume:{status:'good',ratio:1,runs24h:runs.filter((r)=>Date.now()-dateValue(r.startDate)<=86400000).length,baseline:0}},topAlerts:{immediate,incidents}};}
function derivePipelines(runs){const grouped=groupByPipeline(runs),items=[];for(const [pipelineId,list] of Object.entries(grouped)){const latest=list[0],recent=list.slice(0,7),nok=recent.filter((r)=>r.status==='NOK').length,successRate7d=recent.length?((recent.length-nok)/recent.length)*100:100,staleHours=latest.startDate?Math.floor((Date.now()-dateValue(latest.startDate))/3600000):null;const riskScore=Math.max(0,Math.min(100,(latest.status==='NOK'?45:0)+((staleHours??999)>24?25:0)+(nok/Math.max(1,recent.length)>0.2?20:0)));const riskLevel=riskScore>=80?'critical':riskScore>=55?'high':riskScore>=30?'medium':'low';items.push({pipelineId,name:latest.scriptName||pipelineId,owner:latest.owner||'unknown',criticality:latest.criticality||'medium',lastRun:latest.startDate||null,lastStatus:latest.status,successRate7d,regressionDelta:0,staleHours,riskScore,riskLevel});}return items.sort((a,b)=>b.riskScore-a.riskScore||dateValue(b.lastRun)-dateValue(a.lastRun));}
function deriveLineage(pipelines){return pipelines.slice(0,60).map((p)=>({pipelineId:p.pipelineId,name:p.name,status:p.lastStatus}));}
function applyRunFilters(){let runs=[...state.runsAll];if(state.runsTimeFilter&&state.runsTimeFilter!=='all'){const now=Date.now();const ms=state.runsTimeFilter==='24h'?86400000:state.runsTimeFilter==='7d'?604800000:state.runsTimeFilter==='30d'?2592000000:0;if(ms>0)runs=runs.filter((r)=>dateValue(r.startDate)>=now-ms);}if(state.q){const q=state.q.toLowerCase();runs=runs.filter((r)=>[r.id,r.run_id_pipeline,r.pipelineId,r.scriptName,r.hostname,r.errorPreview].map((v)=>String(v||'').toLowerCase()).some((v)=>v.includes(q)));}if(state.runsStatus)runs=runs.filter((r)=>String(r.status||'').toUpperCase()===state.runsStatus.toUpperCase());if(state.selectedPipelineId)runs=runs.filter((r)=>r.pipelineId===state.selectedPipelineId);state.runsView=sortRuns(runs);if(state.runsOffset>=state.runsView.length)state.runsOffset=0;}
function applyPipelineFilters(){let items=[...state.pipelinesAll];const risk=document.getElementById('pipelineRiskFilter')?.value||'';if(risk)items=items.filter((p)=>p.riskLevel===risk);if(state.q){const q=state.q.toLowerCase();items=items.filter((p)=>[p.pipelineId,p.name,p.owner].join(' ').toLowerCase().includes(q));}state.pipelinesView=items;if(state.pipelinesOffset>=items.length)state.pipelinesOffset=0;}
function renderAll(){const _safeCall=(fn)=>{try{fn();}catch(e){console.error('renderAll sub-error in '+fn.name+':',e);}};_safeCall(renderOverview);_safeCall(renderPipelineAssetCards);_safeCall(renderQualitySection);_safeCall(renderPipelines);_safeCall(renderRuns);_safeCall(renderLineage);_safeCall(renderInsights);_safeCall(renderOrchestratorSchedules);_safeCall(renderOrchestratorRuns);_safeCall(renderCharts);_safeCall(renderMetricHelp);_safeCall(updateFooter);_safeCall(updateSearchCounter);}
function renderOverview(){if(!state.overview)return;const stats=document.getElementById('stats');if(stats){stats.innerHTML='';stats.style.display='none';}
const s=state.overview.operationalSignals||{};setText('signalAtRisk',s.atRisk??'-');setText('signalStale',s.stale??'-');setText('signalRegressions',s.regressions??'-');setText('signalVolume',`${Math.round(Number(s.volume?.ratio||1)*100)}%`);setText('signalAtRiskHint',t('hintAtRisk'));setText('signalStaleHint',t('hintStale'));setText('signalRegressionsHint',t('hintRegressions'));setText('signalVolumeHint',t('hintVolume'));
const isCritical=(s.failed||0)>0;const isWarning=(s.atRisk||0)>0&&!(s.failed>0);const hl=document.getElementById('healthHighlight');if(hl){hl.classList.remove('health-ok','health-warning','health-critical');hl.classList.add(isCritical?'health-critical':isWarning?'health-warning':'health-ok');}setText('healthTitle',isCritical?t('healthCrit'):isWarning?t('healthWarn'):t('healthOk'));setText('healthMessage',`${s.pipelineCount||0} pipelines | ${state.overview?.globalKpis?.totalRuns||0} runs | ${t('lastUpdate')} ${fmt(state.overview.generatedAt)}`);
/* Apply signal classes */
document.querySelectorAll('.signal-card').forEach((el)=>{el.classList.remove('signal-good','signal-warning','signal-critical');const sig=el.dataset.signal;const val=Number(sig==='atRisk'?s.atRisk:sig==='stale'?s.stale:sig==='regressions'?s.regressions:0);if(sig==='volume'){const ratio=Number(s.volume?.ratio||1);el.classList.add(ratio<0.5||ratio>2?'signal-critical':ratio<0.7||ratio>1.5?'signal-warning':'signal-good');}else{el.classList.add(val>0?'signal-critical':'signal-good');}});}
function renderPipelines(){const h=document.getElementById('pipelinesTableHead'),b=document.getElementById('pipelinesTableBody');if(!h||!b)return;h.innerHTML=`<tr><th>${t('colPipeline')}</th><th>${t('colOwner')}</th><th>${t('colCriticality')}</th><th>${t('colStatus')}</th><th>${t('colSuccess7d')}</th><th>${t('colRegression')}</th><th>${t('colStale')}</th><th>${t('colRisk')}</th></tr>`;const page=state.pipelinesView.slice(state.pipelinesOffset,state.pipelinesOffset+state.pipelinesLimit);b.innerHTML=page.map((p)=>`<tr data-pipeline="${esc(p.pipelineId)}"><td data-label="Pipeline">${esc(p.name)}</td><td data-label="Owner">${esc(p.owner)}</td><td data-label="Criticidade">${esc(p.criticality)}</td><td data-label="Estado"><span class="status-pill ${p.lastStatus==='OK'?'status-ok':p.lastStatus==='WARNING'?'status-warning':'status-nok'}">${esc(p.lastStatus)}</span></td><td data-label="Sucesso 7d">${Number(p.successRate7d||0).toFixed(1)}%</td><td data-label="Regressão">${Number(p.regressionDelta||0).toFixed(1)}pp</td><td data-label="Stale(h)">${p.staleHours??'-'}</td><td data-label="Risk"><span class="risk-pill risk-${esc(p.riskLevel)}">${esc(p.riskLevel)}</span> ${esc(p.riskScore)}</td></tr>`).join('');b.querySelectorAll('tr[data-pipeline]').forEach((tr)=>tr.addEventListener('click',()=>{state.selectedPipelineId=tr.dataset.pipeline;state.runsOffset=0;applyRunFilters();renderRuns();renderLineage();switchView('runsView');}));setText('pipelinesPageInfo',page.length?`${state.pipelinesOffset+1}-${state.pipelinesOffset+page.length} de ${state.pipelinesView.length}`:'Sem registos');const prev=document.getElementById('pipelinesPrevPage'),next=document.getElementById('pipelinesNextPage');if(prev)prev.disabled=state.pipelinesOffset<=0;if(next)next.disabled=state.pipelinesOffset+state.pipelinesLimit>=state.pipelinesView.length;}
function renderRuns(){const th=document.getElementById('tableHead'),tb=document.getElementById('tableBody');if(!th||!tb)return;th.innerHTML=`<tr>${RUN_COLUMNS.map(([k,lk])=>{const l=t(lk);if(k==='details')return `<th>${l}</th>`;const active=state.runsSortKey===k;const arrow=active?(state.runsSortDir==='asc'?' ↑':' ↓'):'';return `<th data-sort-key="${esc(k)}" class="sortable${active?' sorted':''}" style="cursor:pointer;">${l}${arrow}</th>`;}).join('')}</tr>`;const page=state.runsView.slice(state.runsOffset,state.runsOffset+state.runsLimit);tb.innerHTML=page.map((r)=>`<tr data-run="${r.id}">${RUN_COLUMNS.map(([k,lk])=>`<td data-label="${esc(t(lk))}">${runCell(k,r)}</td>`).join('')}</tr>`).join('');th.querySelectorAll('th[data-sort-key]').forEach((el)=>el.addEventListener('click',()=>toggleRunsSort(el.dataset.sortKey||'')));tb.querySelectorAll('button[data-run]').forEach((btn)=>btn.addEventListener('click',async(e)=>{e.stopPropagation();await openRun(Number(btn.dataset.run));}));setText('pageInfo',page.length?`${state.runsOffset+1}-${state.runsOffset+page.length} de ${state.runsView.length}`:'Sem registos');const prev=document.getElementById('prevPage'),next=document.getElementById('nextPage');if(prev)prev.disabled=state.runsOffset<=0;if(next)next.disabled=state.runsOffset+state.runsLimit>=state.runsView.length;}function runCell(key,r){if(key==='status')return `<span class="status-pill ${(r.status||'').toUpperCase()==='OK'?'status-ok':(r.status||'').toUpperCase()==='WARNING'?'status-warning':'status-nok'}">${esc(r.status)}</span>`;if(key==='startDate'||key==='endDate')return esc(fmt(r[key]));if(key==='details')return `<button class="btn-detail" data-run="${r.id}">${t('colDetails')}</button>`;return esc(r[key]??'-');}
async function openRun(id){const run=state.runsAll.find((r)=>Number(r.id)===Number(id));if(!run)return;setText('modalRunId',`#${run.id}`);setText('modalStatusText',run.status);const grid=document.getElementById('modalMetricsGrid');if(grid){grid.innerHTML=[['Pipeline',run.pipelineId],['Host',run.hostname],['SO',run.osName],['Início',fmt(run.startDate)],['Fim',fmt(run.endDate)],['Duração',run.durationLabel],['CPU',run.cpuLabel],['Memória',run.memLabel],['Owner',run.owner],['Criticidade',run.criticality]].map(([k,v])=>`<div class="metric-card"><span class="metric-label">${esc(k)}</span><strong class="metric-value">${esc(v||'-')}</strong></div>`).join('');}
const d=state.details?.[String(run.id)]||state.details?.[run.id]||{};const log=d.logMessage||d.errorMessage||run.logMessage||run.errorMessage||run.errorPreview||'';const sec=document.getElementById('modalErrorSection'),pre=document.getElementById('modalErrorLog');if(sec&&pre){sec.style.display=log?'block':'none';pre.textContent=stripAnsi(log||'');}const m=document.getElementById('runDetailModal');m?.classList.add('active');m?.setAttribute('aria-hidden','false');}
function closeModal(){const m=document.getElementById('runDetailModal');m?.classList.remove('active');m?.setAttribute('aria-hidden','true');}
function toggleRunsSort(key){if(!key||key==='details')return;if(state.runsSortKey===key){state.runsSortDir=state.runsSortDir==='asc'?'desc':'asc';}else{state.runsSortKey=key;state.runsSortDir='desc';}state.runsOffset=0;applyRunFilters();renderRuns();switchView('runsView');}function sortRuns(runs){const sorted=[...runs];const key=state.runsSortKey||'startDate';const dir=state.runsSortDir==='asc'?1:-1;sorted.sort((a,b)=>{const av=getRunSortValue(a,key);const bv=getRunSortValue(b,key);if(typeof av==='number'&&typeof bv==='number'){if(av===bv)return 0;return av>bv?dir:-dir;}const at=String(av??'').toLowerCase();const bt=String(bv??'').toLowerCase();if(at===bt)return 0;return at>bt?dir:-dir;});return sorted;}function getRunSortValue(run,key){if(key==='id')return Number(run.id||0);if(key==='startDate'||key==='endDate')return dateValue(run[key]);if(key==='durationLabel')return Number(run.execTime||0);if(key==='cpuLabel')return Number(run.usageCPU||0);if(key==='memLabel')return Number(run.usageMemoria||0);if(key==='status')return String(run.status||'');if(key==='pipelineId')return String(run.pipelineId||'');if(key==='hostname')return String(run.hostname||'');if(key==='osName')return String(run.osName||'');return String(run[key]||'');}
function renderInsights(){const o=state.overview;if(!o)return;const immediate=o.topAlerts?.immediate||[],incidents=o.topAlerts?.incidents||[];setHtml('recentFailuresList',listItems(immediate,'status-nok','NOK'));setHtml('failingPipelinesList',listItems(state.pipelinesView.filter((p)=>p.riskLevel==='critical'),'status-nok','Risco'));setHtml('incidentsTimelineList',listItems(incidents,'status-warning','Incidente'));setHtml('topRegressionsList',listItems(state.pipelinesView.filter((p)=>Number(p.regressionDelta||0)>0),'status-warning','Regressão'));}
function renderOrchestratorSchedules(){const h=document.getElementById('orchPipelinesHead'),b=document.getElementById('orchPipelinesBody');if(!h||!b)return;h.innerHTML='<tr><th>Pipeline</th><th>Owner</th><th>Criticidade</th><th>Schedule</th><th>Permissão</th><th>Ações</th></tr>';b.innerHTML=state.orchestratorPipelines.map((p)=>{const pid=p.pipeline_id||p.pipelineId;const role=getUserRole(pid);const canRun=canUserRunPipeline(pid);const canEdit=role==='owner'||role==='open';const isPaused=(p.schedule||'').toLowerCase()==='paused';const isManual=(p.schedule||'').toLowerCase()==='manual';const isRunning=state.runningPipelines&&state.runningPipelines.has(pid);const runDot=isRunning?'<span class="pipeline-running-dot" title="A executar agora"></span>':'';const scheduleDisplay=isPaused?esc(p.prev_schedule||p.prevSchedule||'—'):esc(p.schedule||'manual');const currentVal=isPaused?(p.prev_schedule||p.prevSchedule||''):((p.schedule||'').toLowerCase()==='manual'?'manual':(p.schedule||''));const presets=[{label:'Manual',value:'manual'},{label:'5 min',value:'*/5 * * * *'},{label:'15 min',value:'*/15 * * * *'},{label:'Hourly',value:'0 * * * *'},{label:'Daily 08:00',value:'0 8 * * *'},{label:'Weekdays 08:00',value:'0 8 * * 1-5'},{label:'Custom...',value:'__custom__'}];const currentPreset=presets.find((p)=>p.value===currentVal);const optionsHtml=presets.map((p)=>`<option value="${esc(p.value)}" ${p.value===currentVal?'selected':''}>${esc(p.label)}</option>`).join('');let pauseBtn='';if(canEdit&&!isManual){if(isPaused){pauseBtn=`<button class="btn-detail btn-resume" data-pause-toggle="${esc(pid)}" data-pause-action="resume" title="Retomar schedule">Resume</button>`;}else{pauseBtn=`<button class="btn-detail btn-pause" data-pause-toggle="${esc(pid)}" data-pause-action="pause" title="Pausar schedule">Pause</button>`;}}return `<tr class="${isPaused?'row-paused':''}"><td data-label="Pipeline">${runDot}${esc(pid)}</td><td data-label="Owner">${canEdit ? `<select class="schedule-select" style="min-width:120px" data-owner-pipeline="${esc(pid)}"><option value="unknown" ${!p.owner || p.owner==='unknown'?'selected':''}>unknown</option>${maiatronUsers.map(u => `<option value="${esc(u.username)}" ${p.owner===u.username?'selected':''}>${esc(u.username)}</option>`).join('')}</select>` : esc(p.owner||'unknown')}</td><td data-label="Criticidade">${canEdit ? `<select class="schedule-select" style="min-width:120px" data-crit-pipeline="${esc(pid)}">${['low','medium','high','critical'].map(c => `<option value="${c}" ${(p.criticality||'medium')===c?'selected':''}>${c}</option>`).join('')}</select>` : esc(p.criticality||'medium')}</td><td data-label="Schedule"><div class="schedule-cell">${canEdit&&!isPaused?`<select class="schedule-select${isPaused?' schedule-paused':''}" data-schedule-pipeline="${esc(pid)}">${optionsHtml}</select>`:`<span class="schedule-display">${scheduleDisplay}</span>`}${isPaused?'<span class="schedule-paused-label">PAUSED</span>':''}${canEdit&&!isPaused?`<button class="btn-detail btn-schedule-save" data-schedule-save="${esc(pid)}">Guardar</button>`:''}</div></td><td data-label="Permissão"><span class="role-badge role-${esc(role)}">${esc(role)}</span></td><td data-label="Ações">${pauseBtn} <button class="btn-detail" data-orch-action="trigger" data-pipeline="${esc(pid)}" ${canRun?'':'disabled title="Sem permissão — contacta o owner"'}>Run now</button> <button class="btn-detail" data-orch-action="copy" data-pipeline="${esc(pid)}">Copiar cmd</button></td></tr>`;}).join('');b.querySelectorAll('button[data-orch-action]').forEach((btn)=>btn.addEventListener('click',async()=>{await handleOrchestratorAction(btn.dataset.orchAction,btn.dataset.pipeline);}));b.querySelectorAll('button[data-schedule-save]').forEach((btn)=>btn.addEventListener('click',()=>{const pid=btn.dataset.scheduleSave;const sel=b.querySelector(`select[data-schedule-pipeline="${pid}"]`);if(sel){let val=sel.value;if(val==='__custom__'){val=prompt('Enter cron expression (or leave blank for Manual):','');if(val===null)return;val=val.trim()||'manual';}handleConfigChange(pid,val, b.querySelector(`select[data-owner-pipeline="${pid}"]`)?.value, b.querySelector(`select[data-crit-pipeline="${pid}"]`)?.value);}else{const inp=b.querySelector(`input[data-schedule-pipeline="${pid}"]`);if(inp)handleConfigChange(pid,inp.value.trim(), b.querySelector(`select[data-owner-pipeline="${pid}"]`)?.value, b.querySelector(`select[data-crit-pipeline="${pid}"]`)?.value);}}));b.querySelectorAll('select[data-schedule-pipeline]').forEach((sel)=>sel.addEventListener('change',()=>{let val=sel.value;if(val==='__custom__'){const inp=prompt('Enter cron expression (or leave blank for Manual):','');if(inp===null){sel.value=sel.getAttribute('data-previous-value')||'manual';return;}val=inp.trim()||'manual';}sel.setAttribute('data-previous-value',val);}));b.querySelectorAll('button[data-pause-toggle]').forEach((btn)=>btn.addEventListener('click',()=>{handlePauseToggle(btn.dataset.pauseToggle,btn.dataset.pauseAction);}));}
function renderOrchestratorRuns(){const h=document.getElementById('orchRunsHead'),b=document.getElementById('orchRunsBody');if(!h||!b)return;h.innerHTML='<tr><th>Pipeline</th><th>Status</th><th>Criado em</th><th>Origem</th></tr>';const page=state.orchRuns.slice(state.orchOffset,state.orchOffset+state.orchLimit);b.innerHTML=page.map((item)=>{const r=normalizeOrchestratorRow(item);const status=normalizeOrchestratorStatus(r.status);const source=r.delivery==='copied_cli'?'cli-copy':(r.source||r.triggerType||'frontend');return `<tr><td data-label="Pipeline">${esc(r.pipelineId||r.pipeline_id||'-')}</td><td data-label="Status"><span class="status-pill ${orchestratorStatusClass(status)}">${esc(status)}</span></td><td data-label="Criado em">${esc(fmt(r.createdAt||r.requested_at))}</td><td data-label="Origem">${esc(source)}</td></tr>`;}).join('');setText('orchPageInfo',page.length?`${state.orchOffset+1}-${state.orchOffset+page.length} de ${state.orchRuns.length}`:'Sem registos');const prev=document.getElementById('orchPrevPage'),next=document.getElementById('orchNextPage');if(prev)prev.disabled=state.orchOffset<=0;if(next)next.disabled=state.orchOffset+state.orchLimit>=state.orchRuns.length;}
async function handleOrchestratorAction(action,pipelineId){const by=state.user?.username||'frontend';if(action==='trigger'&&!canUserRunPipeline(pipelineId)){showToast(t('noPerm'),'error');return;}const cmd=`python orchestrator.py trigger enqueue ${pipelineId} --by ${by}`;if(action==='copy'){await copyText(cmd);showToast(t('copied'),'success');return;}if(action==='trigger'){const trigger={trigger_id:newTriggerId(),pipeline_id:pipelineId,requested_by:by,requested_at:new Date().toISOString(),source:'frontend',status:'queued',delivery:'delivered',notes:'Run now solicitado no frontend',command:cmd};let delivered=false;try{delivered=await writeRunNowTrigger(trigger);}catch{}if(delivered){showToast(t('triggerOk'),'success');}else{trigger.delivery='copied_cli';trigger.source='frontend-cli-copy';await copyText(cmd);showToast(t('triggerFail'),'warning');}pushLocalTrigger(trigger);addInflight(pipelineId,trigger.trigger_id);const inflightRow=normalizeOrchestratorRow({runId:trigger.trigger_id,pipelineId,status:'running',source:'frontend',createdAt:trigger.requested_at});state.orchRuns=[inflightRow,...state.orchRuns];if(!state.runningPipelines)state.runningPipelines=new Set();state.runningPipelines.add(pipelineId);renderOrchestratorSchedules();renderOrchestratorRuns();}}
/* === v3.0 New functions: Pipeline asset cards, Quality section, Drawer, Search counter === */
function freshnessLevel(hours){if(hours==null||hours<0)return 'paused';if(hours<1)return 'fresh';if(hours<6)return 'ok';if(hours<24)return 'stale';return 'critical';}
function freshnessLabel(hours){if(hours==null||hours<0)return 'Paused';if(hours<1)return `${Math.round(hours*60)}m`;if(hours<24)return `${Math.round(hours)}h`;return `${Math.round(hours/24)}d`;}
function qualityGateLevel(rate){if(rate>=95)return 'pass';if(rate>=80)return 'warn';return 'fail';}
function qualityGateLabel(rate){if(rate>=95)return 'Pass';if(rate>=80)return 'Warning';return 'Fail';}
function cronToHuman(expr){if(!expr)return 'Manual';const s=expr.trim().toLowerCase();if(s==='paused')return 'Paused';if(s==='manual')return 'Manual';const parts=s.split(/\s+/);if(parts.length<5)return expr;const [min,h,dom,mon,dow]=parts;if(min==='*'&&h==='*')return 'Cada minuto';if(min.startsWith('*/')&&h==='*')return `A cada ${min.slice(2)} min`;if(h==='*'&&dom==='*')return `${min}' de cada hora`;if(dom==='*'&&mon==='*'&&dow==='*')return `${h}:${min.padStart(2,'0')} diário`;return expr;}
function renderPipelineAssetCards(){const c=document.getElementById('pipelineAssetCards');if(!c)return;if(!state.pipelinesAll.length&&!state.orchestratorPipelines.length){c.innerHTML='';return;}
const pipelines=state.pipelinesAll.length?state.pipelinesAll:state.orchestratorPipelines.map((p)=>({pipelineId:p.pipeline_id||p.pipelineId,name:p.name||p.pipeline_id||p.pipelineId,owner:p.owner||'unknown',lastRun:null,lastStatus:'UNKNOWN',successRate7d:100,staleHours:null,riskScore:0,riskLevel:'low'}));
c.innerHTML=pipelines.map((p)=>{const cat=state.orchestratorPipelines.find((cp)=>(cp.pipeline_id||cp.pipelineId)===p.pipelineId);const schedule=cat?.schedule||'manual';const isPaused=schedule.toLowerCase()==='paused';const hrs=p.staleHours!=null?p.staleHours:(p.lastRun?Math.floor((Date.now()-dateValue(p.lastRun))/3600000):null);const fl=isPaused?'paused':freshnessLevel(hrs);const sr=Number(p.successRate7d||100);const qg=qualityGateLevel(sr);const hue=hashPipelineHue(p.pipelineId);
/* Sparkline: last 10 runs for this pipeline */
const pipeRuns=(state.runsAll||[]).filter((r)=>r.pipelineId===p.pipelineId).slice(0,10).reverse();
const sparkHtml=pipeRuns.length?pipeRuns.map((r)=>{const ok=r.status==='OK';return `<div class="spark-bar ${ok?'spark-ok':'spark-nok'}" style="height:${ok?'100':'40'}%"></div>`;}).join(''):'<div class="spark-bar spark-empty" style="height:30%"></div>'.repeat(5);
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
const kpis=state.overview.globalKpis||{};const pipelines=state.pipelinesAll||[];
/* Freshness bars */
const freshRows=pipelines.map((p)=>{const cat=state.orchestratorPipelines.find((cp)=>(cp.pipeline_id||cp.pipelineId)===p.pipelineId);const isPaused=(cat?.schedule||'').toLowerCase()==='paused';const hrs=p.staleHours!=null?p.staleHours:(p.lastRun?Math.floor((Date.now()-dateValue(p.lastRun))/3600000):null);const fl=isPaused?'paused':freshnessLevel(hrs);const pct=isPaused?20:hrs==null?0:Math.min(100,Math.max(5,100-Math.min(hrs/48*100,100)));return `<div class="freshness-bar-item"><span class="freshness-bar-label" title="${esc(p.pipelineId)}">${esc(p.name||p.pipelineId)}</span><div class="freshness-bar-track"><div class="freshness-bar-fill fb-${fl}" style="width:${pct}%"></div></div><span class="freshness-bar-value">${hrs!=null?freshnessLabel(hrs):(isPaused?'Paused':'N/A')}</span></div>`;}).join('');
/* Efficiency */
const avgExec=Number(kpis.avgExecTime||0);const p95Exec=Number(kpis.p95ExecTime||0);const effRatio=p95Exec>0?Math.min(100,Math.round((avgExec/p95Exec)*100)):100;const effPct=Math.min(100,effRatio);
/* Quality gates summary */
const qgPass=pipelines.filter((p)=>qualityGateLevel(Number(p.successRate7d||100))==='pass').length;const qgWarn=pipelines.filter((p)=>qualityGateLevel(Number(p.successRate7d||100))==='warn').length;const qgFail=pipelines.filter((p)=>qualityGateLevel(Number(p.successRate7d||100))==='fail').length;
c.innerHTML=`
<article class="quality-card"><h4>${t('freshness')}</h4><div class="qc-meta">Última execução por pipeline</div><div class="freshness-bar-wrap">${freshRows||'<span class="muted">Sem pipelines</span>'}</div></article>
<article class="quality-card"><h4>${t('qualityGates')}</h4><div class="qc-meta">Checks por threshold de success rate</div><div class="pac-pills" style="margin-top:4px"><span class="qg-pill qg-pass">Pass: ${qgPass}</span><span class="qg-pill qg-warn">Warning: ${qgWarn}</span><span class="qg-pill qg-fail">Fail: ${qgFail}</span></div><div class="qc-meta" style="margin-top:8px">${pipelines.length} pipeline(s) avaliados | Threshold: Pass >= 95%, Warning >= 80%, Fail < 80%</div></article>
<article class="quality-card"><h4>${t('execEfficiency')}</h4><div class="qc-meta">Tempo médio vs P95</div><div class="efficiency-row"><div class="efficiency-ring" style="--eff-pct:${effPct}%"><div class="efficiency-ring-inner">${effRatio}%</div></div><div class="efficiency-metrics"><span>Avg: <strong>${avgExec.toFixed(1)}s</strong></span><span>P95: <strong>${p95Exec.toFixed(1)}s</strong></span><span>Ratio: <strong>${p95Exec>0?(p95Exec/Math.max(avgExec,0.1)).toFixed(1)+'x':'N/A'}</strong></span>${p95Exec>3*avgExec&&avgExec>0?'<span style="color:#f59e0b;font-size:0.72rem">&#9888; P95 elevado — possível lentidão intermitente</span>':''}</div></div></article>`;
}
function toggleMetricsDrawer(){const d=document.getElementById('metricsDrawer');const o=document.getElementById('metricsDrawerOverlay');if(!d)return;const isOpen=d.classList.contains('open');if(isOpen){closeMetricsDrawer();}else{d.classList.add('open');o?.classList.add('open');d.setAttribute('aria-hidden','false');}}
function closeMetricsDrawer(){const d=document.getElementById('metricsDrawer');const o=document.getElementById('metricsDrawerOverlay');d?.classList.remove('open');o?.classList.remove('open');d?.setAttribute('aria-hidden','true');}
function updateSearchCounter(){const el=document.getElementById('searchCounter');if(!el)return;if(!state.q){el.textContent='';el.classList.remove('active');return;}const total=state.runsView.length+state.pipelinesView.length;el.textContent=`${total} resultado${total!==1?'s':''}`;el.classList.add('active');}
function highlightText(text,query){if(!query||!text)return esc(text);const escaped=esc(text);const qEsc=query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');try{return escaped.replace(new RegExp(`(${qEsc})`,'gi'),'<mark class="search-hl">$1</mark>');}catch{return escaped;}}

function renderCharts(){if(typeof Chart==='undefined'||!state.runsAll.length||!state.overview)return;const buckets=bucketBy(state.runsAll,state.historyGranularity),labels=Object.keys(buckets),values=Object.values(buckets);const s=state.overview.operationalSignals,donut=[Math.max((s.pipelineCount||0)-(s.failed||0)-(s.atRisk||0),0),s.atRisk||0,s.failed||0];const cv=document.getElementById('runsHistoryChart');let barBg='rgba(0,212,255,0.55)';if(cv){const gx=cv.getContext('2d');const gr=gx.createLinearGradient(0,0,0,cv.parentElement?.clientHeight||200);gr.addColorStop(0,'rgba(0,212,255,0.7)');gr.addColorStop(1,'rgba(0,212,255,0.10)');barBg=gr;}const histCfg={type:'bar',data:{labels,datasets:[{label:t('chartHistory'),data:values,backgroundColor:barBg,borderColor:'rgba(0,212,255,0.9)',borderWidth:1,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{maxTicksLimit:10,font:{size:10},color:'rgba(200,200,200,0.6)'}},y:{beginAtZero:true,grid:{color:'rgba(255,255,255,0.05)'},ticks:{font:{size:10},color:'rgba(200,200,200,0.6)'}}}}};
const donutCfg={type:'doughnut',data:{labels:[t('healthy'),t('attention'),t('failed')],datasets:[{data:donut,backgroundColor:['rgba(34,197,94,0.85)','rgba(245,158,11,0.85)','rgba(239,68,68,0.9)'],borderWidth:0,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,cutout:'65%',plugins:{legend:{display:false}}}};historyChart=upsertChart(historyChart,'runsHistoryChart',histCfg);healthChart=upsertChart(healthChart,'successRateChart',donutCfg);const sr=Number(state.overview.globalKpis?.successRate||0);const pctEl=document.getElementById('donutPct');if(pctEl)pctEl.textContent=sr.toFixed(1)+'%';const dlbl=document.querySelector('.donut-label');if(dlbl)dlbl.textContent=t('healthLabel');}
function upsertChart(ex,id,cfg){const cv=document.getElementById(id);if(!cv)return ex;if(!ex)return new Chart(cv.getContext('2d'),cfg);ex.data=cfg.data;ex.options=cfg.options;ex.update();return ex;}
function renderMetricHelp(){document.querySelectorAll("[data-signal='atRisk']")?.forEach((el)=>{el.title=t('hintAtRisk');});document.querySelectorAll("[data-signal='stale']")?.forEach((el)=>{el.title=t('hintStale');});document.querySelectorAll("[data-signal='regressions']")?.forEach((el)=>{el.title=t('hintRegressions');});document.querySelectorAll("[data-signal='volume']")?.forEach((el)=>{el.title=t('hintVolume');});}
function updateFooter(){const g=state.payload?.generated_at||state.overview?.generatedAt||null;setText('lastUpdateTime',fmt(g));setText('lastUpdateRuns',`${state.runsAll.length} runs | ${state.runsView.length} filtrados`);setText('headerUpdateTime',fmt(g));}
function switchView(viewId){if(!viewId)return;document.querySelectorAll('.nav-tab').forEach((b)=>b.classList.toggle('active',b.dataset.view===viewId));document.querySelectorAll('.view').forEach((v)=>v.classList.toggle('active',v.id===viewId));document.body.classList.toggle('dash-lock',viewId==='dashboardView');if(viewId==='dashboardView')setTimeout(()=>{historyChart?.resize?.();healthChart?.resize?.();},60);}
function showMainApp(){document.getElementById('loginScreen')?.classList.add('hidden');document.getElementById('mainApp')?.classList.remove('hidden');setText('userName',state.user?.displayName||state.user?.username||'admin');window.MaiatronAuthUI?.syncFromServer({configUrl:CONFIG.authConfigUrl});}
function showLoginScreen(){document.getElementById('mainApp')?.classList.add('hidden');document.getElementById('loginScreen')?.classList.remove('hidden');window.MaiatronAuthUI?.setSession(null);}
function initTheme(){applyTheme(localStorage.getItem(CONFIG.themeKey)||'dark');}
function onToggleTheme(){const curr=document.documentElement.getAttribute('data-theme')==='light'?'light':'dark';const next=curr==='light'?'dark':'light';localStorage.setItem(CONFIG.themeKey,next);applyTheme(next);}function applyTheme(t){if(t==='light')document.documentElement.setAttribute('data-theme','light');else document.documentElement.removeAttribute('data-theme');}
function startAutoRefresh(){stopAutoRefresh();let sec=Math.floor(CONFIG.refreshMs/1000);setText('refreshCountdown',`${sec}s`);refreshTimer=setInterval(async()=>{await refreshAllData();sec=Math.floor(CONFIG.refreshMs/1000);setText('refreshCountdown',`${sec}s`);},CONFIG.refreshMs);countdownTimer=setInterval(()=>{sec-=1;if(sec<0)sec=Math.floor(CONFIG.refreshMs/1000);setText('refreshCountdown',`${sec}s`);},1000);}function stopAutoRefresh(){if(refreshTimer)clearInterval(refreshTimer);if(countdownTimer)clearInterval(countdownTimer);refreshTimer=null;countdownTimer=null;}
function loadTriggerHistory(){try{const raw=localStorage.getItem(CONFIG.triggerKey);let items=raw?JSON.parse(raw):[];const cutoff=Date.now()-7*86400000;items=items.filter((r)=>{const t=dateValue(r.createdAt||r.requested_at||r.requestedAt);return !t||t>=cutoff;}).slice(0,50);state.triggerHistory=items.map((r)=>normalizeOrchestratorRow(r));localStorage.setItem(CONFIG.triggerKey,JSON.stringify(items));}catch{state.triggerHistory=[];}return state.triggerHistory;}
function pushLocalTrigger(trigger){loadTriggerHistory();const rec=normalizeOrchestratorRow({...trigger,runId:trigger.trigger_id,pipelineId:trigger.pipeline_id,createdAt:trigger.requested_at,updated_at:new Date().toISOString()});state.triggerHistory.unshift(rec);localStorage.setItem(CONFIG.triggerKey,JSON.stringify(state.triggerHistory.slice(0,200)));}
function loadInflight(){try{const raw=localStorage.getItem(CONFIG.inflightKey);return raw?JSON.parse(raw):[];}catch{return [];}}
function saveInflight(items){try{localStorage.setItem(CONFIG.inflightKey,JSON.stringify((items||[]).slice(0,50)));}catch{}}
function addInflight(pipelineId,triggerId){const items=loadInflight();items.unshift({pipelineId,triggerId,startedAt:Date.now()});saveInflight(items);}
function pruneInflight(dbRuns){const items=loadInflight();const now=Date.now();const TIMEOUT_MS=30*60*1000;const kept=[];for(const entry of items){if(now-entry.startedAt>TIMEOUT_MS)continue;const matched=dbRuns.find((r)=>{const rPid=r.pipelineId||r.pipeline_id||'';const rDate=dateValue(r.createdAt||r.created_at||r.started_at);const rStatus=normalizeOrchestratorStatus(r.status);const isTerminal=rStatus==='consumed'||rStatus==='failed'||r.status==='success'||r.status==='warning';return rPid===entry.pipelineId&&rDate>=entry.startedAt&&isTerminal;});if(!matched)kept.push(entry);}saveInflight(kept);return kept;}
async function copyText(t){try{await navigator.clipboard.writeText(t);}catch{}}
async function writeRunNowTrigger(trigger){const url=(window.OVERSEER_ASSETS?.triggerUrl)||'/MAIATRON/apps/overseer/trigger.php';try{const resp=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(trigger)});if(!resp.ok)throw new Error(`HTTP ${resp.status}`);const data=await resp.json();return data.status==='ok';}catch(e){console.error('writeRunNowTrigger error:',e);return false;}}
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
function toNum(v){if(typeof v==='number')return v;if(v==null)return 0;const txt=String(v).trim();if(!txt)return 0;const normalized=txt.includes(',')?txt.replace(/\./g,'').replace(',','.'):txt;const n=Number(normalized);return Number.isFinite(n)?n:0;}
function fmt(v){if(!v)return '-';const d=new Date(v);if(Number.isNaN(d.getTime()))return String(v);return d.toLocaleString('pt-PT');}
function setText(id,val){const el=document.getElementById(id);if(el)el.textContent=String(val??'-');}
function setHtml(id,html){const el=document.getElementById(id);if(el)el.innerHTML=html;}
function showLoginError(t){const el=document.getElementById('loginError');if(!el)return;el.textContent=t;el.classList.add('show');}
function clearLoginError(){const el=document.getElementById('loginError');if(!el)return;el.textContent='';el.classList.remove('show');}
function esc(v){return String(v??'-').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;');}
function showToast(msg,type){const t=document.getElementById('toast');if(!t)return;t.textContent=msg;t.className=`toast show ${type||'info'}`;setTimeout(()=>{t.className='toast';},2400);}

function getUserRole(pipelineId){const perms=state.pipelinePermissions?.[pipelineId];if(!perms||!perms.length)return 'open';const me=state.user?.username;if(!me)return 'viewer';const grant=perms.find((p)=>p.username===me);return grant?grant.role:'viewer';}
function canUserRunPipeline(pipelineId){const role=getUserRole(pipelineId);return role==='open'||role==='owner'||role==='executor';}
function isValidCron(expr){if(!expr)return false;const s=expr.trim().toLowerCase();if(s==='manual'||s==='paused')return true;return /^[\d\*\/\-\,\?LW#]+(\s+[\d\*\/\-\,\?LW#]+){4}$/.test(s);}
async function handleConfigChange(pipelineId,newSchedule,newOwner,newCriticality){if(!isValidCron(newSchedule)){showToast(t('schedInvalidMsg'),'error');return;} if(newOwner===undefined||newOwner===null)newOwner=state.orchestratorPipelines.find(p=>p.pipeline_id===pipelineId||p.pipelineId===pipelineId)?.owner; if(newCriticality===undefined||newCriticality===null)newCriticality=state.orchestratorPipelines.find(p=>p.pipeline_id===pipelineId||p.pipelineId===pipelineId)?.criticality;const by=state.user?.username||'frontend';const trigger={trigger_id:`sched-${newTriggerId()}`,type:'schedule_change',pipeline_id:pipelineId,new_schedule:newSchedule,new_owner:newOwner,new_criticality:newCriticality,requested_by:by,requested_at:new Date().toISOString()};let delivered=false;try{delivered=await writeScheduleTrigger(trigger);}catch{}const cmd=`python orchestrator.py schedule set ${pipelineId} "${newSchedule}"`;if(delivered){showToast(`Schedule de ${pipelineId} ${t('schedChanged')}`,'success');}else{await copyText(cmd);showToast(t('schedFail'),'warning');}const cat=state.orchestratorPipelines.find((p)=>(p.pipeline_id||p.pipelineId)===pipelineId);if(cat)cat.schedule=newSchedule; cat.owner=newOwner; cat.criticality=newCriticality;state.pendingScheduleMutations[pipelineId]={schedule:newSchedule,prev_schedule:cat?.prev_schedule||null,ts:Date.now()};}
async function handlePauseToggle(pipelineId,action){const cat=state.orchestratorPipelines.find((p)=>(p.pipeline_id||p.pipelineId)===pipelineId);if(!cat)return;if(action==='pause'){const currentSchedule=cat.schedule||'manual';if(currentSchedule.toLowerCase()==='manual'||currentSchedule.toLowerCase()==='paused')return;cat.prev_schedule=currentSchedule;const cc = state.orchestratorPipelines.find(p=>(p.pipeline_id||p.pipelineId)===pipelineId); await handleConfigChange(pipelineId,'paused',cc?.owner,cc?.criticality);cat.schedule='paused';cat.prev_schedule=currentSchedule;state.pendingScheduleMutations[pipelineId]={schedule:'paused',prev_schedule:currentSchedule,ts:Date.now()};renderOrchestratorSchedules();}else if(action==='resume'){const prev=cat.prev_schedule||cat.prevSchedule||'manual';const cc2 = state.orchestratorPipelines.find(p=>(p.pipeline_id||p.pipelineId)===pipelineId); await handleConfigChange(pipelineId,prev,cc2?.owner,cc2?.criticality);cat.schedule=prev;cat.prev_schedule=null;cat.prevSchedule=null;state.pendingScheduleMutations[pipelineId]={schedule:prev,prev_schedule:null,ts:Date.now()};renderOrchestratorSchedules();}}
async function writeScheduleTrigger(trigger){const url=(window.OVERSEER_ASSETS?.triggerUrl)||'/MAIATRON/apps/overseer/trigger.php';try{const resp=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(trigger)});if(!resp.ok)throw new Error(`HTTP ${resp.status}`);const data=await resp.json();return data.status==='ok';}catch(e){console.error('writeScheduleTrigger error:',e);return false;}}
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
  const st=String(script?.lastStatus||'').toUpperCase();
  if(st==='NOK')return 'error';
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
    const message=String(s.lastMessage||'').trim();
    const logPayload=getScriptLogPayload(s,selected.pipelineId);
    const logBtn=logPayload?`<div class="lineage-log-actions"><button class="btn-detail lineage-log-btn" data-lineage-log-path="${esc(s.path||'')}">Ver logs</button></div>`:'';
    return `<article class="lineage-item lineage-script ${cls}" style="--pipeline-hue:${selected.hue};"><h4>${esc(s.path||'-')}</h4><p class="meta"><span class="status-pill ${pillClass}">${label}</span></p><p class="muted">${esc(meta)}</p>${message?`<p class="lineage-message">${esc(message)}</p>`:''}${logBtn}</article>`;
  }).join('');

  const moduleCards=selected.nodes.map((n)=>{
    const st=String(n.status||'UNKNOWN').toUpperCase();
    const lvl=String(n.lastEventLevel||'').toLowerCase();
    const pillClass=lvl==='error'||st==='NOK'?'status-nok':lvl==='warning'?'status-warning':st==='OK'?'status-ok':'status-muted';
    const label=lvl==='error'||st==='NOK'?'ERRO':lvl==='warning'?'WARNING':st==='OK'?'OK':'DESCONHECIDO';
    const when=n.lastSeenAt||n.lastSeen||null;
    const msg=n.lastMessage||n.lastError||'';
    const modulePath=String(n.script||n.label||'');
    const scriptRef=selected.scripts.find((s)=>String(s.path||'')===modulePath) || selected.scripts.find((s)=>String(s.path||'').toLowerCase()===modulePath.toLowerCase());
    const logPayload=getScriptLogPayload(scriptRef, selected.pipelineId);
    const logBtn=logPayload?`<div class="lineage-log-actions"><button class="btn-detail lineage-log-btn" data-lineage-module-log-path="${esc(modulePath)}">Ver logs</button></div>`:'';
    return `<article class="lineage-item lineage-module" style="--pipeline-hue:${selected.hue};"><h4>${esc(n.label||n.id||'-')}${n.critical===false?' <span class="badge badge-muted">non-critical</span>':''}</h4><p class="meta"><span class="status-pill ${pillClass}">${label}</span></p><p class="muted">Último evento: ${esc(fmt(when))}</p>${msg?`<p class="lineage-message">${esc(msg)}</p>`:''}${logBtn}</article>`;
  }).join('');

  const deps=selected.edges.map((e)=>`<span class="lineage-dep-chip">${esc(e.source)} -> ${esc(e.target)}</span>`).join('');

  c.innerHTML=`<div class="lineage-shell"><div class="lineage-tiles">${filterRow}${tileCards||'<article class="lineage-item"><h4>Sem correspondências</h4><p class="muted">Ajusta o filtro de pipeline.</p></article>'}</div><div class="lineage-selected"><article class="lineage-hero" style="--pipeline-hue:${selected.hue};"><div><h4>${esc(selected.name)}</h4><p class="muted">Pipeline: ${esc(selected.pipelineId)} | Owner: ${esc(pMeta.owner||'unknown')} | Criticidade: ${esc(pMeta.criticality||'medium')}</p></div><div class="lineage-hero-kpis"><span><strong>${selected.scripts.length}</strong> scripts</span><span><strong>${selected.executed}</strong> executados</span><span><strong>${selected.nodes.length}</strong> módulos</span><span><strong>${selected.errorScripts}</strong> erros</span><span><strong>${selected.warningScripts}</strong> warnings</span></div></article><section class="lineage-section"><h4 class="lineage-section-title">Scripts</h4><div class="lineage-grid lineage-grid-enhanced">${scriptCards||'<article class="lineage-item"><h4>Sem scripts</h4><p class="muted">Não há inventário para este pipeline.</p></article>'}</div></section><section class="lineage-section"><h4 class="lineage-section-title">Módulos observados</h4><div class="lineage-grid lineage-grid-enhanced">${moduleCards||'<article class="lineage-item"><h4>Sem módulos</h4><p class="muted">Ainda sem eventos de módulo para este pipeline.</p></article>'}</div></section><section class="lineage-section"><h4 class="lineage-section-title">Dependências</h4><div class="lineage-dependency-list">${deps||'<span class="muted">Sem dependências declaradas.</span>'}</div></section></div></div>`;

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
