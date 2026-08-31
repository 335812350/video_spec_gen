import path from 'node:path';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import express from 'express';
import { ProjectStore } from './projectStore.js';
import { RunStore } from './runStore.js';
import { CodexRunner } from './codexRunner.js';
import { rootPaths, safePath } from './pathSafety.js';

const moduleDir = path.dirname(fileURLToPath(import.meta.url));

const mime = {
  '.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime', '.m4v': 'video/mp4',
  '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4', '.ogg': 'audio/ogg',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
  '.json': 'application/json; charset=utf-8', '.md': 'text/markdown; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.html': 'text/html; charset=utf-8',
};

export function createApp({ workspaceRoot = process.cwd(), runnerMode, codexCommand } = {}) {
  const projects = new ProjectStore(workspaceRoot);
  const runs = new RunStore(projects);
  const runner = new CodexRunner({ runStore: runs, projects, mode: runnerMode, command: codexCommand });
  const app = express();
  app.locals.console = { projects, runs, runner, paths: rootPaths(workspaceRoot), workspaceRoot };
  app.use(express.json({ limit: '1mb' }));

  const asyncRoute = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
  const ok = (res, data) => res.json(data);

  app.get('/api/health', (req, res) => ok(res, { ok: true, service: 'video-project-console' }));
  app.get('/api/projects', asyncRoute(async (req, res) => ok(res, { projects: await projects.listProjects() })));
  app.post('/api/projects', asyncRoute(async (req, res) => res.status(201).json(await projects.createProject(req.body || {}))));
  app.get('/api/projects/:id', asyncRoute(async (req, res) => {
    const project = await projects.getProject(req.params.id);
    const runsList = await runs.listRuns(req.params.id);
    return ok(res, { ...project, assets: project.assets || [], runs: runsList.slice(0, 10), files: await projects.listProjectFiles(req.params.id), outputs: await projects.listOutputs(req.params.id) });
  }));
  app.patch('/api/projects/:id', asyncRoute(async (req, res) => ok(res, await projects.updateProject(req.params.id, req.body || {}))));

  app.get('/api/projects/:id/assets', asyncRoute(async (req, res) => ok(res, { assets: await projects.listAssets(req.params.id) })));
  app.post('/api/projects/:id/assets/register', asyncRoute(async (req, res) => {
    const asset = await projects.registerAsset(req.params.id, req.body?.path || req.body?.relative_path, req.body?.notes);
    res.status(201).json(asset);
  }));
  app.get('/api/projects/:id/files', asyncRoute(async (req, res) => ok(res, { files: await projects.listProjectFiles(req.params.id) })));
  app.get('/api/projects/:id/files/*', asyncRoute(async (req, res) => {
    const file = await projects.readProjectFile(req.params.id, req.params[0]);
    res.setHeader('Content-Type', mime[path.extname(file.full).toLowerCase()] || 'application/octet-stream');
    res.setHeader('Content-Length', file.stat.size);
    res.send(file.data);
  }));

  app.get('/api/projects/:id/runs', asyncRoute(async (req, res) => ok(res, { runs: await runs.listRuns(req.params.id) })));
  app.post('/api/projects/:id/runs', asyncRoute(async (req, res) => {
    const run = await runs.createRun(req.params.id, { input: req.body?.input || req.body?.message || '' });
    Promise.resolve(runner.start(req.params.id, run.id, { input: run.input })).catch((error) => runner.fail(req.params.id, run.id, error));
    res.status(202).json(run);
  }));
  app.post('/api/projects/:id/actions/:action', asyncRoute(async (req, res) => {
    const allowed = new Set(['check', 'preview', 'render', 'inspect', 'qa']);
    if (!allowed.has(req.params.action)) return res.status(400).json({ error: 'unsupported action' });
    const run = await runs.createRun(req.params.id, { input: `Run HyperFrames action: ${req.params.action}. ${req.body?.input || ''}`.trim() });
    Promise.resolve(runner.start(req.params.id, run.id, { input: run.input })).catch((error) => runner.fail(req.params.id, run.id, error));
    res.status(202).json(run);
  }));
  app.get('/api/projects/:id/runs/:runId', asyncRoute(async (req, res) => {
    const run = await runs.getRun(req.params.id, req.params.runId);
    const events = await runs.readEvents(req.params.id, req.params.runId);
    const artifacts = await fsp.readFile(runs.runRoot(req.params.id, req.params.runId) + path.sep + 'artifacts.json', 'utf8').then(JSON.parse).catch(() => ({ artifacts: [] }));
    ok(res, { run, events, ...artifacts });
  }));
  app.get('/api/projects/:id/runs/:runId/events', asyncRoute(async (req, res) => {
    const runId = req.params.runId;
    await runs.getRun(req.params.id, runId);
    return streamEvents(req, res, runs, req.params.id, runId);
  }));
  app.post('/api/projects/:id/runs/:runId/cancel', asyncRoute(async (req, res) => { await runner.cancel(req.params.id, req.params.runId); ok(res, await runs.getRun(req.params.id, req.params.runId)); }));
  app.post('/api/projects/:id/runs/:runId/resume', asyncRoute(async (req, res) => {
    const previous = await runs.getRun(req.params.id, req.params.runId);
    const checkpoint = await fsp.readFile(runs.runRoot(req.params.id, previous.id) + path.sep + 'checkpoints' + path.sep + 'latest.json', 'utf8').then(JSON.parse).catch(() => previous.checkpoint);
    const run = await runs.createRun(req.params.id, { input: req.body?.input || previous.input, parentRunId: previous.id, resumeFrom: checkpoint });
    Promise.resolve(runner.start(req.params.id, run.id, { input: run.input, resume: true })).catch((error) => runner.fail(req.params.id, run.id, error));
    res.status(202).json(run);
  }));

  app.get('/api/projects/:id/events', asyncRoute(async (req, res) => {
    await projects.getProject(req.params.id);
    const runList = await runs.listRuns(req.params.id);
    const requested = Number(req.query.since_seq || 0);
    setupSse(res);
    for (const run of runList) {
      const events = await runs.readEvents(req.params.id, run.id, requested);
      for (const event of events) sendSse(res, { ...event, run_id: run.id });
    }
    const listener = (projectId, runId, event) => { if (projectId === req.params.id) sendSse(res, { ...event, run_id: runId }); };
    runs.on('event', listener);
    req.on('close', () => runs.off('event', listener));
  }));

  app.get('/api/media/*', asyncRoute(async (req, res) => {
    const raw = req.params[0] || '';
    const roots = rootPaths(workspaceRoot);
    const match = raw.match(/^(assets|projects|outputs)\/(.+)$/);
    if (!match) return res.status(400).json({ error: 'media path must start with assets/, projects/ or outputs/' });
    const full = safePath(roots[match[1]], match[2], { allowMissing: false });
    const stat = await fsp.stat(full);
    if (!stat.isFile()) return res.status(404).end();
    return sendRangeFile(req, res, full, stat.size);
  }));

  const frontendDist = path.join(moduleDir, '..', 'frontend', 'dist');
  if (fs.existsSync(frontendDist)) {
    app.use(express.static(frontendDist));
    app.get('*', (req, res, next) => req.path.startsWith('/api/') ? next() : res.sendFile(path.join(frontendDist, 'index.html')));
  }

  app.use((error, req, res, next) => {
    if (res.headersSent) return next(error);
    const status = error.status || (error.code === 'ENOENT' ? 404 : 500);
    res.status(status).json({ error: error.message || 'Internal server error', code: error.code || 'INTERNAL_ERROR' });
  });
  return { app, projects, runs, runner, workspaceRoot };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  const workspaceRoot = path.resolve(process.env.VIDEO_CONSOLE_WORKSPACE || path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..'));
  const { app, projects, runs } = createApp({ workspaceRoot, runnerMode: process.env.CODEX_RUNNER_MODE });
  await projects.init();
  await runs.recoverStaleRuns();
  const host = process.env.CONSOLE_HOST || '127.0.0.1';
  const port = Number(process.env.CONSOLE_PORT || 3040);
  app.listen(port, host, () => console.log(`Video Project Console: http://${host}:${port}`));
}

function setupSse(res) {
  res.status(200).set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
  res.flushHeaders?.();
}

function sendSse(res, event) {
  if (res.writableEnded) return;
  res.write(`id: ${event.seq || Date.now()}\ndata: ${JSON.stringify(event)}\n\n`);
}

function streamEvents(req, res, runs, projectId, runId) {
  setupSse(res);
  const since = Number(req.query.since_seq || req.headers['last-event-id'] || 0);
  runs.readEvents(projectId, runId, since).then((events) => events.forEach((event) => sendSse(res, event))).catch(() => {});
  const listener = (p, r, event) => { if (p === projectId && r === runId) sendSse(res, event); };
  runs.on('event', listener);
  const keepAlive = setInterval(() => { if (!res.writableEnded) res.write(': keep-alive\n\n'); }, 15000);
  req.on('close', () => { clearInterval(keepAlive); runs.off('event', listener); });
}

async function sendRangeFile(req, res, filePath, size) {
  const contentType = mime[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
  const range = req.headers.range;
  if (!range) {
    res.status(200).set({ 'Content-Type': contentType, 'Content-Length': size, 'Accept-Ranges': 'bytes' });
    return fs.createReadStream(filePath).pipe(res);
  }
  const match = /bytes=(\d*)-(\d*)/.exec(range);
  if (!match) return res.status(416).set('Content-Range', `bytes */${size}`).end();
  const start = match[1] ? Number(match[1]) : Math.max(size - Number(match[2] || 0), 0);
  const end = match[1] && match[2] ? Number(match[2]) : size - 1;
  if (start >= size || start > end) return res.status(416).set('Content-Range', `bytes */${size}`).end();
  const boundedEnd = Math.min(end, size - 1);
  res.status(206).set({ 'Content-Range': `bytes ${start}-${boundedEnd}/${size}`, 'Accept-Ranges': 'bytes', 'Content-Length': boundedEnd - start + 1, 'Content-Type': contentType });
  fs.createReadStream(filePath, { start, end: boundedEnd }).pipe(res);
}
