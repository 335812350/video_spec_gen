import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import { atomicWriteJson, ensureDir, readJson } from './fileStore.js';
import { assertSlug, safePath } from './pathSafety.js';

const isoNow = () => new Date().toISOString();
const activeStatuses = new Set(['queued', 'running', 'waiting_for_input']);

export class RunStore extends EventEmitter {
  constructor(projectStore) {
    super();
    this.projects = projectStore;
  }

  runsRoot(projectId) { return safePath(this.projects.projectPath(projectId), 'runs'); }
  runRoot(projectId, runId) { return safePath(this.runsRoot(projectId), runId); }
  runFile(projectId, runId) { return safePath(this.runRoot(projectId, runId), 'run.json'); }
  eventsFile(projectId, runId) { return safePath(this.runRoot(projectId, runId), 'events.jsonl'); }

  async createRun(projectId, { input = '', parentRunId = null, resumeFrom = null } = {}) {
    await this.projects.getProject(projectId);
    await ensureDir(this.runsRoot(projectId));
    const runId = `run-${new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14)}-${Math.random().toString(36).slice(2, 7)}`;
    const created = isoNow();
    const run = { schema_version: 1, id: runId, project_id: assertSlug(projectId), status: 'queued', created_at: created, updated_at: created, input, parent_run_id: parentRunId, resume_from: resumeFrom, pid: null, codex_session_id: null, active_stage: null, checkpoint: null, error: null };
    await ensureDir(path.join(this.runsRoot(projectId), runId, 'checkpoints'));
    await ensureDir(path.join(this.runsRoot(projectId), runId, 'logs'));
    await atomicWriteJson(this.runFile(projectId, runId), run);
    await atomicWriteJson(safePath(this.runRoot(projectId, runId), 'artifacts.json'), { artifacts: [] });
    await fsp.writeFile(this.eventsFile(projectId, runId), '', 'utf8');
    await this.appendEvent(projectId, runId, { type: 'run.created', message: 'Run created', input });
    await this.projects.updateProject(projectId, { active_run_id: runId, status: 'running' });
    return run;
  }

  async getRun(projectId, runId) {
    const run = await readJson(this.runFile(projectId, runId));
    if (!run) throw Object.assign(new Error('运行记录不存在'), { status: 404, code: 'RUN_NOT_FOUND' });
    return run;
  }

  async listRuns(projectId) {
    const root = this.runsRoot(projectId);
    const entries = await fsp.readdir(root, { withFileTypes: true }).catch((error) => error.code === 'ENOENT' ? [] : Promise.reject(error));
    const runs = [];
    for (const entry of entries.filter((item) => item.isDirectory())) {
      const run = await readJson(path.join(root, entry.name, 'run.json'));
      if (run) runs.push(run);
    }
    return runs.sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
  }

  async appendEvent(projectId, runId, event) {
    const file = this.eventsFile(projectId, runId);
    const existing = await this.readEvents(projectId, runId);
    const item = { seq: existing.length ? existing[existing.length - 1].seq + 1 : 1, time: isoNow(), ...event };
    await fsp.appendFile(file, `${JSON.stringify(item)}\n`, 'utf8');
    this.emit('event', projectId, runId, item);
    return item;
  }

  async readEvents(projectId, runId, sinceSeq = 0) {
    const text = await fsp.readFile(this.eventsFile(projectId, runId), 'utf8').catch((error) => error.code === 'ENOENT' ? '' : Promise.reject(error));
    return text.split('\n').filter(Boolean).map((line) => JSON.parse(line)).filter((event) => event.seq > Number(sinceSeq || 0));
  }

  async updateRun(projectId, runId, patch, event) {
    const run = await this.getRun(projectId, runId);
    Object.assign(run, patch, { updated_at: isoNow() });
    await atomicWriteJson(this.runFile(projectId, runId), run);
    if (event) await this.appendEvent(projectId, runId, event);
    if (['completed', 'failed', 'cancelled', 'interrupted'].includes(run.status)) {
      const project = await this.projects.getProject(projectId);
      if (project.active_run_id === runId) await this.projects.updateProject(projectId, { active_run_id: null, status: run.status === 'completed' ? 'ready' : run.status });
    }
    return run;
  }

  async saveCheckpoint(projectId, runId, checkpoint) {
    const payload = { ...checkpoint, saved_at: isoNow() };
    await atomicWriteJson(safePath(this.runRoot(projectId, runId), 'checkpoints/latest.json'), payload);
    await this.updateRun(projectId, runId, { checkpoint: payload }, { type: 'checkpoint.saved', stage: payload.stage, message: 'Checkpoint saved' });
    return payload;
  }

  async addArtifact(projectId, runId, artifact) {
    const file = safePath(this.runRoot(projectId, runId), 'artifacts.json');
    const index = await readJson(file, { artifacts: [] });
    index.artifacts = [...(index.artifacts || []).filter((item) => item.path !== artifact.path), { ...artifact, created_at: artifact.created_at || isoNow() }];
    await atomicWriteJson(file, index);
    await this.appendEvent(projectId, runId, { type: 'artifact.created', path: artifact.path, kind: artifact.kind, message: artifact.message || `Artifact: ${artifact.path}` });
    return index;
  }

  async acquireLock(projectId, runId) {
    const lock = safePath(this.runsRoot(projectId), '.active.lock');
    try {
      const handle = await fsp.open(lock, 'wx');
      await handle.writeFile(JSON.stringify({ run_id: runId, pid: process.pid, created_at: isoNow() }));
      await handle.close();
      return lock;
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      const previous = await readJson(lock, null);
      if (previous?.pid && isPidAlive(previous.pid)) throw Object.assign(new Error('项目已有运行中的任务'), { status: 409, code: 'RUN_LOCKED' });
      await fsp.unlink(lock).catch(() => {});
      return this.acquireLock(projectId, runId);
    }
  }

  async releaseLock(projectId, runId) {
    const lock = safePath(this.runsRoot(projectId), '.active.lock');
    const previous = await readJson(lock, null);
    if (!previous || previous.run_id === runId) await fsp.unlink(lock).catch(() => {});
  }

  async recoverStaleRuns() {
    for (const project of await this.projects.listProjects()) {
      for (const run of await this.listRuns(project.id)) {
        if (activeStatuses.has(run.status) && (!run.pid || !isPidAlive(run.pid))) {
          await this.updateRun(project.id, run.id, { status: 'interrupted', pid: null }, { type: 'run.interrupted', message: 'Run was interrupted while the console was offline' });
        }
      }
      await fsp.unlink(safePath(this.runsRoot(project.id), '.active.lock')).catch(() => {});
    }
  }
}

export function isPidAlive(pid) {
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}
