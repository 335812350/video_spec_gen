import express from 'express';
import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ProjectStore } from './projectStore.js';
import { RunStore } from './runStore.js';
import { CodexRunner } from './codexRunner.js';
import { mediaType, readJson } from './fileStore.js';
import { assertSlug, safePath } from './pathSafety.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const workspaceRoot = path.resolve(process.env.VIDEO_CONSOLE_WORKSPACE || path.join(here, '..', '..'));
const port = Number(process.env.CONSOLE_PORT || 3040);
const host = process.env.CONSOLE_HOST || '127.0.0.1';

export async function createConsoleApp({ root = workspaceRoot, runnerMode = process.env.CODEX_RUNNER_MODE || 'real' } = {}) {
  const projects = new ProjectStore(root);
  await projects.init();
  const runs = new RunStore(projects);
  await runs.recoverStaleRuns();
  const runner = new CodexRunner({ runStore: runs, projects, mode: runnerMode });
  const app = express();
  app.use(express.json({ limit: '2mb' }));
  app.use((req, res, next) => {
    res.setHeader('Cache-Control', 'no-store');
    next();
  });

  app.get('/api/health', (_req, res) => res.json({ ok: true, workspace: root }));

  app.get('/api/projects', asyncHandler(async (_req, res) => res.json({ projects: await projects.listProjects() })));
  app.post('/api/projects', asyncHandler(async (req, res) => {
    const project = await projects.createProject(req.body || {});
    res.status(201).json({ project });
  }));
  app.get('/api/projects/:id', asyncHandler(async (req, res) => {
    const project = await projects.getProject(req.params.id);
    const runsList = await runs.listRuns(req.params.id);
    const storyboard = await readJson(safePath(projects.projectPath(req.params.id), project.storyboard_path || 'storyboard.json'), null);
    const outputs = await projects.listOutputs(req.params.id);
    res.json({ project: { ...project, storyboard, outputs, assets: project.assets || [] }, runs: runsList.slice(0, 20) });
  }));
  app.patch('/api/projects/:id', asyncHandler(async (req, res) => res.json({ project: await projects.updateProject(req.params.id, req.body || {}) })));

  app.get('/api/projects/:id/assets', asyncHandler(async (req, res) => res.json({ assets: await projects.listAssets(req.params.id) })));
  app.post('/api/projects/:id/assets/register', asyncHandler(async (req, res) => {
    const asset = await projects.registerAsset(req.params.id, req.body?.path, req.body?.notes || '');
    res.status(201).json({ asset });
  }));

  app.get('/api/projects/:id/files', asyncHandler(async (req, res) => res.json({ files: await projects.listProjectFiles(req.params.id) })));
  app.get('/api/projects/:id/files/*', asyncHandler(async (req, res) => {
    const file = await projects.readProjectFile(req.params.id, req.params[0]);
    res.type(mediaType(file.full)).send(file.data);
  }));

  app.get('/api/projects/:id/runs', asyncHandler(async (req, res) => res.json({ runs: await runs.listRuns(req.params.id) })));
  app.post('/api/projects/:id/runs', asyncHandler(async (req, res) => {
    const run = await runs.createRun(req.params.id, { input: String(req.body?.input || req.body?.prompt || req.body?.message || '') });
    runner.start(req.params.id, run.id, { input: run.input }).catch((error) => runner.fail(req.params.id, run.id, error));
    res.status(202).json({ run });
  }));
  app.get('/api/projects/:id/runs/:runId', asyncHandler(async (req, res) => {
    const run = await runs.getRun(req.params.id, req.params.runId);
    const events = await runs.readEvents(req.params.id, req.params.runId);
    const artifacts = await readArtifacts(runs, req.params.id, req.params.runId);
    res.json({ run, events, artifacts });
  }));
  app.get('/api/projects/:id/runs/:runId/events', asyncHandler(async (req, res) => {
    await runs.getRun(req.params.id, req.params.runId);
    if (!String(req.headers.accept || '').includes('text/event-stream')) {
      return res.json({ events: await runs.readEvents(req.params.id, req.params.runId, Number(req.query.since_seq || 0)) });
    }
    const since = Number(req.query.since_seq || 0);
    res.status(200);
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');
    res.flushHeaders?.();
    const send = (event) => {
      if (event.seq <= since && !req.query.since_seq) return;
      res.write(`id: ${event.seq}\ndata: ${JSON.stringify(event)}\n\n`);
    };
    for (const event of await runs.readEvents(req.params.id, req.params.runId, since)) send(event);
    const listener = (projectId, runId, event) => {
      if (projectId === req.params.id && runId === req.params.runId) send(event);
    };
    runs.on('event', listener);
    const heartbeat = setInterval(() => res.write(': heartbeat\n\n'), 15000);
    req.on('close', () => { clearInterval(heartbeat); runs.off('event', listener); });
  }));
  app.post('/api/projects/:id/runs/:runId/cancel', asyncHandler(async (req, res) => {
    await runner.cancel(req.params.id, req.params.runId);
    res.json({ run: await runs.getRun(req.params.id, req.params.runId) });
  }));
  app.post('/api/projects/:id/runs/:runId/resume', asyncHandler(async (req, res) => {
    const previous = await runs.getRun(req.params.id, req.params.runId);
    const run = await runs.createRun(req.params.id, { input: String(req.body?.input || previous.input || ''), parentRunId: previous.id, resumeFrom: previous.checkpoint });
    runner.start(req.params.id, run.id, { input: run.input, resume: true }).catch((error) => runner.fail(req.params.id, run.id, error));
    res.status(202).json({ run });
  }));

  app.get('/api/projects/:id/events', asyncHandler(async (req, res) => {
    const projectRuns = await runs.listRuns(req.params.id);
    if (String(req.headers.accept || '').includes('text/event-stream')) {
      res.status(200).set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' });
      res.flushHeaders?.();
      const send = (runId, event) => { if (!res.writableEnded) res.write(`id: ${event.seq}\ndata: ${JSON.stringify({ ...event, run_id: runId })}\n\n`); };
      for (const run of projectRuns.slice(0, 10)) for (const event of await runs.readEvents(req.params.id, run.id)) send(run.id, event);
      const listener = (projectId, runId, event) => { if (projectId === req.params.id) send(runId, event); };
      runs.on('event', listener);
      const heartbeat = setInterval(() => { if (!res.writableEnded) res.write(': heartbeat\n\n'); }, 15000);
      req.on('close', () => { clearInterval(heartbeat); runs.off('event', listener); });
      return;
    }
    const all = [];
    for (const run of projectRuns.slice(0, 10)) all.push(...await runs.readEvents(req.params.id, run.id));
    res.json({ events: all.sort((a, b) => String(a.time).localeCompare(String(b.time))) });
  }));

  app.get('/api/media/*', asyncHandler(async (req, res) => {
    const relative = String(req.params[0] || '').replace(/^\/+/, '');
    const rootMatch = relative.match(/^(assets|projects|outputs)\/(.+)$/);
    const roots = rootMatch
      ? [{ base: path.join(root, rootMatch[1]), relative: rootMatch[2] }]
      : ['assets', 'projects', 'outputs'].map((name) => ({ base: path.join(root, name), relative }));
    const target = roots.map(({ base, relative: rel }) => {
      try { return safePath(base, rel); } catch { return null; }
    }).find((candidate) => candidate && fsSync.existsSync(candidate));
    if (!target) return res.status(404).json({ error: '媒体文件不存在' });
    res.sendFile(target);
  }));

  const dist = path.join(here, '..', 'frontend', 'dist');
  if (fsSync.existsSync(dist)) {
    app.use(express.static(dist));
    app.get('*', (req, res, next) => req.path.startsWith('/api/') ? next() : res.sendFile(path.join(dist, 'index.html')));
  }
  app.use((error, _req, res, _next) => {
    const status = Number(error.status) || 500;
    res.status(status).json({ error: error.message || '服务器错误', code: error.code || 'INTERNAL_ERROR' });
  });
  return { app, projects, runs, runner, root };
}

async function readArtifacts(runs, projectId, runId) {
  const file = safePath(runs.runRoot(projectId, runId), 'artifacts.json');
  return (await readJson(file, { artifacts: [] })).artifacts || [];
}

function asyncHandler(handler) {
  return (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  createConsoleApp().then(({ app }) => app.listen(port, host, () => console.log(`Video Project Console: http://${host}:${port}`))).catch((error) => { console.error(error); process.exitCode = 1; });
}
