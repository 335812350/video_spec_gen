import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertCircle, Archive, ArrowLeft, AudioLines, Check, ChevronDown, ChevronRight,
  CircleDot, Clock3, Clapperboard, Film, FolderOpen, Gauge, HardDrive, Inbox,
  LayoutDashboard, Loader2, MessageSquare, MoreHorizontal, Play, Plus, RefreshCw,
  RotateCcw, Search, Send, Settings2, Sparkles, Square, Terminal, Upload, Video,
  X, Zap,
} from 'lucide-react'
import { api, asArray, mediaUrl } from './lib/api'

const demoProjects = [
  { id: 'annual-meeting-trailer', name: '年会不能停 · Trailer', slug: 'annual-meeting-trailer', status: 'ready', updated_at: '刚刚', duration: '01:03', scenes: 15, cover: '' },
]

const stageMeta = [
  { id: 'brief', label: 'Brief', icon: Sparkles },
  { id: 'analysis', label: '分析素材', icon: Search },
  { id: 'storyboard', label: '分镜设计', icon: Clapperboard },
  { id: 'build', label: '构建工程', icon: Terminal },
  { id: 'render', label: '渲染输出', icon: Film },
  { id: 'qa', label: '质量检查', icon: Check },
]

const statusText = { queued: '排队中', running: '执行中', waiting_for_input: '等待输入', completed: '已完成', failed: '失败', cancelled: '已取消', interrupted: '已中断' }

function App() {
  const [projects, setProjects] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState('projects')

  const loadProjects = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const data = await api.get('/api/projects')
      const list = asArray(data, 'projects')
      setProjects(list)
      if (list.length && !selectedId) setSelectedId(list[0].id || list[0].slug)
    } catch (err) {
      setError(err.message)
      setProjects([])
    } finally { setLoading(false) }
  }, [selectedId])

  useEffect(() => { loadProjects() }, [loadProjects])

  const selected = useMemo(() => projects.find((p) => (p.id || p.slug) === selectedId), [projects, selectedId])
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Film size={17} /></div><span>Frameyard</span><span className="brand-beta">LOCAL</span></div>
        <div className="workspace-label">工作区</div>
        <nav className="side-nav">
          <button className={view === 'projects' ? 'side-link active' : 'side-link'} onClick={() => setView('projects')}><LayoutDashboard size={16} />项目</button>
          <button className="side-link" onClick={() => setView('projects')}><Archive size={16} />素材库</button>
        </nav>
        <div className="sidebar-section"><div className="section-label">最近项目 <span>{projects.length}</span></div>
          {projects.slice(0, 6).map((project) => <button key={project.id || project.slug} className={`project-nav-item ${(project.id || project.slug) === selectedId ? 'selected' : ''}`} onClick={() => { setSelectedId(project.id || project.slug); setView('workspace') }}><span className="status-dot" /><span className="project-nav-name">{project.name || project.title || project.slug}</span></button>)}
          {!projects.length && <div className="side-empty">还没有视频工程</div>}
        </div>
        <div className="sidebar-footer"><button className="side-link"><Settings2 size={16} />设置</button><div className="runtime"><span className="runtime-dot" />Codex Runner <span className="runtime-ok">ready</span></div></div>
      </aside>
      <main className="main-area">
        <header className="topbar"><div className="breadcrumbs"><span>Frameyard</span><ChevronRight size={14} /><strong>{view === 'workspace' ? (selected?.name || '视频工程') : '项目'}</strong></div><div className="top-actions"><button className="icon-button" title="刷新项目" onClick={loadProjects}><RefreshCw size={16} /></button><button className="icon-button" title="更多操作"><MoreHorizontal size={18} /></button><div className="avatar">CY</div></div></header>
        {view === 'workspace' && selectedId ? <Workspace projectId={selectedId} project={selected} onBack={() => setView('projects')} onProjectUpdated={loadProjects} /> : <ProjectsHome projects={projects} loading={loading} error={error} onRefresh={loadProjects} onOpen={(id) => { setSelectedId(id); setView('workspace') }} />}
      </main>
    </div>
  )
}

function ProjectsHome({ projects, loading, error, onRefresh, onOpen }) {
  const [showCreate, setShowCreate] = useState(false)
  return <div className="page page-home"><div className="home-heading"><div><div className="eyebrow">VIDEO WORKSPACE</div><h1>你的项目</h1><p>从素材到渲染输出，所有过程都在一个可恢复的工程里。</p></div><button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={16} />新建工程</button></div>
    {error && <div className="error-banner"><AlertCircle size={17} /><span>{error}</span><button onClick={onRefresh}><RefreshCw size={14} />重试</button></div>}
    {loading ? <div className="loading-block"><Loader2 className="spin" size={22} />正在扫描本地项目…</div> : projects.length ? <div className="project-grid">{projects.map((project) => <ProjectCard key={project.id || project.slug} project={project} onOpen={onOpen} />)}<button className="new-card" onClick={() => setShowCreate(true)}><Plus size={21} /><span>创建新的工程</span><small>以文件夹作为项目边界</small></button></div> : <EmptyProjects onCreate={() => setShowCreate(true)} />}
    {showCreate && <CreateProjectModal onClose={() => setShowCreate(false)} onCreated={(project) => { setShowCreate(false); onRefresh(); onOpen(project.id || project.slug) }} />}
  </div>
}

function ProjectCard({ project, onOpen }) { return <button className="project-card" onClick={() => onOpen(project.id || project.slug)}><div className="card-cover">{project.cover ? <img src={mediaUrl(project.cover)} alt="" /> : <div className="cover-fallback"><Video size={32} /><span>{project.slug || 'LOCAL PROJECT'}</span></div>}<span className="cover-status"><span className="status-dot" />{project.status === 'running' ? '处理中' : '就绪'}</span></div><div className="card-content"><div className="card-title-row"><h3>{project.name || project.title || project.slug}</h3><MoreHorizontal size={17} /></div><p>{project.description || '本地视频工程'}</p><div className="card-meta"><span><Clock3 size={13} />{project.duration || '—'}</span><span><Clapperboard size={13} />{project.scenes || project.scene_count || '—'} 镜头</span><span>{project.updated_at || '刚刚'}</span></div></div></button> }
function EmptyProjects({ onCreate }) { return <div className="empty-state"><div className="empty-icon"><FolderOpen size={24} /></div><h2>开始你的第一个视频工程</h2><p>选择一个项目文件夹，Codex 会在里面分析素材、生成分镜并完成渲染。</p><button className="primary-button" onClick={onCreate}><Plus size={16} />新建工程</button></div> }

function CreateProjectModal({ onClose, onCreated }) {
  const [name, setName] = useState(''); const [slug, setSlug] = useState(''); const [busy, setBusy] = useState(false); const [err, setErr] = useState('')
  const submit = async (event) => { event.preventDefault(); setBusy(true); setErr(''); try { const result = await api.post('/api/projects', { name: name.trim(), slug: (slug || name).trim().toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-').replace(/^-|-$/g, '') }); onCreated(result.project || result) } catch (e) { setErr(e.message) } finally { setBusy(false) } }
  return <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}><form className="modal" onSubmit={submit}><div className="modal-header"><div><span className="eyebrow">NEW WORKSPACE</span><h2>创建视频工程</h2></div><button type="button" className="icon-button" onClick={onClose}><X size={18} /></button></div><label>工程名称<input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：品牌发布会 Trailer" required /></label><label>目录标识<input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="brand-launch-trailer" /></label>{err && <div className="field-error"><AlertCircle size={14} />{err}</div>}<div className="modal-actions"><button type="button" className="ghost-button" onClick={onClose}>取消</button><button className="primary-button" disabled={busy}>{busy && <Loader2 size={15} className="spin" />}创建工程</button></div></form></div>
}

function Workspace({ projectId, project: summary, onBack, onProjectUpdated }) {
  const [project, setProject] = useState(summary); const [events, setEvents] = useState([]); const [files, setFiles] = useState([]); const [run, setRun] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [tab, setTab] = useState('storyboard'); const [prompt, setPrompt] = useState(''); const eventRef = useRef(null)
  const load = useCallback(async () => { setLoading(true); setError(''); try { const [p, f, r] = await Promise.all([api.get(`/api/projects/${projectId}`), api.get(`/api/projects/${projectId}/files`), api.get(`/api/projects/${projectId}/runs`)]); setProject(p.project || p); setFiles(asArray(f, 'files')); const runs = asArray(r, 'runs'); if (runs.length) { const current = runs.find((item) => ['running', 'queued', 'waiting_for_input'].includes(item.status)) || runs[0]; setRun(current); const ev = await api.get(`/api/projects/${projectId}/runs/${current.id}/events`); setEvents(asArray(ev, 'events')) } } catch (e) { setError(e.message) } finally { setLoading(false) } }, [projectId])
  useEffect(() => { load() }, [load])
  useEffect(() => { if (!projectId) return undefined; const source = new EventSource(`/api/projects/${projectId}/events`); source.onmessage = (message) => { try { const event = JSON.parse(message.data); setEvents((previous) => previous.some((item) => item.seq === event.seq) ? previous : [...previous, event]); if (event.run) setRun(event.run) } catch { /* ignore keep-alive */ } }; source.onerror = () => source.close(); return () => source.close() }, [projectId])
  useEffect(() => { if (eventRef.current) eventRef.current.scrollTop = eventRef.current.scrollHeight }, [events])
  const startRun = async () => { if (!prompt.trim()) return; try { const result = await api.post(`/api/projects/${projectId}/runs`, { prompt: prompt.trim(), runtime: 'codex' }); setRun(result.run || result); setPrompt(''); setTab('activity'); onProjectUpdated() } catch (e) { setError(e.message) } }
  const cancelRun = async () => { if (!run?.id) return; try { await api.post(`/api/projects/${projectId}/runs/${run.id}/cancel`, {}); await load() } catch (e) { setError(e.message) } }
  const progress = run?.progress ?? project?.progress ?? (run?.status === 'completed' ? 100 : 0)
  const currentStage = run?.stage || project?.current_stage || (run?.status === 'completed' ? 'qa' : 'brief')
  return <div className="workspace-page"><div className="workspace-head"><button className="back-button" onClick={onBack}><ArrowLeft size={16} />所有项目</button><div className="project-heading"><div className="project-heading-title"><span className="live-dot" />{project?.name || summary?.name || projectId}<span className="project-slug">/{project?.slug || projectId}</span></div><div className="project-heading-actions"><button className="ghost-button"><Upload size={15} />注册素材</button><button className="icon-button"><MoreHorizontal size={18} /></button></div></div></div>
    {error && <div className="error-banner compact"><AlertCircle size={16} /><span>{error}</span><button onClick={load}>重试</button></div>}
    <StageStepper current={currentStage} progress={progress} status={run?.status} />
    <div className="workspace-grid"><section className="column left-column"><Panel title="工程文件" icon={<FolderOpen size={15} />} action={<button className="text-button">查看全部</button>}><FileTree files={files} loading={loading} /></Panel><Panel title="素材" icon={<HardDrive size={15} />} action={<button className="icon-button tiny"><Plus size={15} /></button>}><AssetList project={project} /></Panel><Panel title="任务摘要" icon={<Gauge size={15} />}><RunSummary run={run} progress={progress} /></Panel></section><section className="column center-column"><CodexChat prompt={prompt} setPrompt={setPrompt} onSubmit={startRun} running={['running', 'queued'].includes(run?.status)} onCancel={cancelRun} /><Panel title="过程事件" icon={<Terminal size={15} />} action={<span className="live-label"><span className="status-dot" />实时</span>}><EventLog events={events} scrollRef={eventRef} /></Panel></section><section className="column right-column"><PanelTabs tab={tab} setTab={setTab} project={project} files={files} events={events} run={run} /></section></div><OutputDock project={project} run={run} progress={progress} /></div>
}

function StageStepper({ current, progress, status }) { const index = Math.max(0, stageMeta.findIndex((s) => s.id === current)); return <div className="stepper"><div className="stepper-head"><span className="eyebrow">PIPELINE</span><span className="stepper-progress">{statusText[status] || '等待开始'} <strong>{Math.round(progress)}%</strong></span></div><div className="steps">{stageMeta.map((stage, i) => { const Icon = stage.icon; const done = i < index || status === 'completed'; const active = i === index && status !== 'completed'; return <div className={`step ${done ? 'done' : ''} ${active ? 'active' : ''}`} key={stage.id}><div className="step-icon">{done ? <Check size={14} /> : <Icon size={14} />}</div><span>{stage.label}</span>{i < stageMeta.length - 1 && <div className="step-line" />}</div> })}</div><div className="progress-track"><div className="progress-value" style={{ width: `${Math.min(100, progress)}%` }} /></div></div> }

function Panel({ title, icon, action, children, className = '' }) { return <div className={`panel ${className}`}><div className="panel-title"><div className="panel-title-label">{icon}{title}</div>{action}</div>{children}</div> }

function FileTree({ files, loading }) { if (loading) return <div className="skeleton-lines"><i /><i /><i /></div>; if (!files.length) return <div className="panel-empty"><Inbox size={18} /><span>暂无生成文件</span></div>; return <div className="file-tree">{files.slice(0, 9).map((file, i) => { const path = typeof file === 'string' ? file : file.path || file.name; const ext = path.split('.').pop(); return <div className="file-row" key={path || i}><FileIcon ext={ext} /><span>{path}</span><span className="file-size">{file.size || ''}</span></div> })}</div> }
function FileIcon({ ext = '' }) { const tone = ['mp4', 'mov', 'webm'].includes(ext.toLowerCase()) ? 'video' : ['json', 'md'].includes(ext.toLowerCase()) ? 'data' : 'code'; return <span className={`file-icon ${tone}`}>{tone === 'video' ? <Video size={13} /> : tone === 'data' ? <Archive size={13} /> : <Terminal size={13} />}</span> }
function AssetList({ project }) { const assets = project?.assets || []; if (!assets.length) return <div className="asset-empty"><div className="asset-placeholder"><Film size={19} /></div><div><strong>素材目录为空</strong><span>将视频放入 assets/{project?.slug || 'your-project'}</span></div></div>; return <div className="asset-list">{assets.slice(0, 4).map((asset, i) => <div className="asset-row" key={asset.path || i}><div className="asset-thumb"><Video size={16} /></div><div><strong>{asset.name || asset.path}</strong><span>{asset.duration || '媒体素材'} {asset.size ? `· ${asset.size}` : ''}</span></div></div>)}</div> }
function RunSummary({ run, progress }) { return <div className="run-summary"> <div className="summary-main"><span className={`run-status ${run?.status || 'idle'}`}><span />{run ? statusText[run.status] || run.status : '待启动'}</span><strong>{Math.round(progress)}%</strong></div><div className="summary-bar"><span style={{ width: `${progress}%` }} /></div><div className="summary-meta"><span>当前任务</span><span>{run?.stage_label || run?.stage || '等待 Codex 指令'}</span></div>{run?.updated_at && <div className="summary-meta"><span>最近更新</span><span>{run.updated_at}</span></div>}</div> }

function CodexChat({ prompt, setPrompt, onSubmit, running, onCancel }) { const submit = (e) => { e.preventDefault(); onSubmit() }; return <div className="chat-panel"><div className="chat-heading"><div><span className="eyebrow">CODEX SESSION</span><h2>视频工程助手</h2></div><span className="session-pill"><span className="status-dot" />{running ? 'working' : 'ready'}</span></div><div className="chat-welcome"><div className="codex-avatar"><Zap size={18} /></div><div><strong>从这里开始编辑你的工程</strong><p>告诉我你想分析素材、调整分镜、重做某个镜头，或渲染一个新版本。</p><div className="suggestions"><button onClick={() => setPrompt('分析全部素材并给出第一版分镜')}>分析素材</button><button onClick={() => setPrompt('检查当前工程并指出需要修改的镜头')}>检查工程</button><button onClick={() => setPrompt('渲染当前版本并进行视觉检查')}>渲染输出</button></div></div></div><form className="chat-input-wrap" onSubmit={submit}><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="描述你想对视频工程做的修改…" rows={3} disabled={running} /><div className="chat-input-footer"><span><Sparkles size={13} />Codex 会在当前工程目录中工作</span><div>{running && <button type="button" className="cancel-button" onClick={onCancel}><Square size={13} />停止</button>}<button className="send-button" disabled={!prompt.trim() || running} title="发送"><Send size={16} /></button></div></div></form></div> }

function EventLog({ events, scrollRef }) { if (!events.length) return <div className="event-empty"><Terminal size={20} /><span>任务启动后，这里会显示 Codex 的实时过程</span></div>; return <div className="event-log" ref={scrollRef}>{events.map((event, i) => <div className="event-item" key={`${event.seq || ''}-${i}`}><div className={`event-marker ${event.level || 'info'}`} /> <div className="event-body"><div className="event-head"><strong>{event.title || event.type || '过程事件'}</strong><time>{event.created_at || event.timestamp || ''}</time></div><p>{event.message || event.detail || ''}</p>{event.path && <code>{event.path}</code>}</div></div>)}</div> }

function PanelTabs({ tab, setTab, project, files, events, run }) { const tabs = [['storyboard', '分镜', Clapperboard], ['artifacts', '产物', Archive], ['activity', '运行记录', CircleDot]]; return <Panel className="tabs-panel"><div className="tabs">{tabs.map(([id, label, Icon]) => <button key={id} className={tab === id ? 'tab active' : 'tab'} onClick={() => setTab(id)}><Icon size={14} />{label}{id === 'activity' && run ? <span className="tab-count">1</span> : null}</button>)}</div>{tab === 'storyboard' && <Storyboard project={project} />}{tab === 'artifacts' && <Artifacts files={files} project={project} />}{tab === 'activity' && <RunHistory project={project} events={events} run={run} />}</Panel> }
function Storyboard({ project }) { const shots = project?.storyboard?.shots || project?.storyboard || project?.frames || []; if (!shots.length) return <div className="tab-empty"><div className="storyboard-placeholder"><Clapperboard size={22} /></div><strong>等待分镜生成</strong><span>Codex 分析素材后，镜头会出现在这里。</span></div>; return <div className="storyboard-list">{shots.slice(0, 12).map((shot, i) => <div className="shot-row" key={shot.id || i}><div className="shot-index">{String(i + 1).padStart(2, '0')}</div><div className="shot-thumb">{shot.thumbnail || shot.preview ? <img src={mediaUrl(shot.thumbnail || shot.preview)} alt="" /> : <Clapperboard size={16} />}</div><div className="shot-copy"><strong>{shot.title || shot.name || `镜头 ${i + 1}`}</strong><span>{shot.description || shot.action || '未填写镜头描述'}</span></div><span className="shot-duration">{shot.duration || '—'}</span></div>)}</div> }
function Artifacts({ files, project }) { const generated = files.filter((file) => typeof file !== 'string' && ['generated', 'artifact', 'output'].includes(file.kind)); const list = generated.length ? generated : files.slice(0, 7); return <div className="artifact-list">{list.length ? list.map((file, i) => { const path = typeof file === 'string' ? file : file.path || file.name; return <div className="artifact-row" key={path || i}><FileIcon ext={path.split('.').pop()} /><div><strong>{path.split('/').pop()}</strong><span>{path}</span></div><ChevronRight size={14} /></div> }) : <div className="tab-empty"><Archive size={21} /><strong>还没有产物</strong><span>生成的 spec、工程和渲染文件会出现在这里。</span></div>}</div> }
function RunHistory({ run, events }) { return <div className="run-history">{run ? <><div className="history-card"><div className={`history-status ${run.status}`}><span />{statusText[run.status] || run.status}</div><strong>{run.title || run.prompt || 'Codex 视频任务'}</strong><span>{run.created_at || '本次运行'} · {events.length} 个事件</span></div><div className="history-actions">{['completed', 'failed', 'interrupted', 'cancelled'].includes(run.status) && <button className="ghost-button"><RotateCcw size={14} />恢复任务</button>}<button className="text-button">查看完整日志</button></div></> : <div className="tab-empty"><CircleDot size={21} /><strong>暂无运行记录</strong><span>提交一次 Codex 任务后，运行历史会保存在工程目录里。</span></div>}</div> }

function OutputDock({ project, run, progress }) { const output = project?.outputs?.[0] || project?.latest_output; return <div className="output-dock"><div className="output-preview"><div className="preview-screen">{output?.preview || output?.path ? <video controls src={mediaUrl(output.preview || output.path)} /> : <div className="preview-empty"><Play size={22} /><span>预览窗口</span><small>完成渲染后可在此播放</small></div>}<div className="preview-overlay"><span>PREVIEW</span><span>{output?.duration || '1920 × 1080'}</span></div></div></div><div className="output-info"><div className="output-heading"><div><span className="eyebrow">LATEST OUTPUT</span><h3>{output?.name || '尚未渲染视频'}</h3></div><button className="ghost-button" disabled={!output}><Archive size={14} />打开文件</button></div><div className="output-progress"><div className="output-progress-head"><span>渲染进度</span><strong>{Math.round(progress)}%</strong></div><div className="progress-track"><div className="progress-value" style={{ width: `${progress}%` }} /></div><div className="output-meta"><span>{run ? statusText[run.status] || run.status : '等待任务'}</span><span>{output?.size || 'MP4 · 25fps'}</span></div></div></div></div> }

export default App
