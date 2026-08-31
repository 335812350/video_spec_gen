import { EventEmitter } from 'node:events';
import { spawn } from 'node:child_process';
import path from 'node:path';
import fsp from 'node:fs/promises';

export class CodexRunner extends EventEmitter {
  constructor({ runStore, projects, command = process.env.CODEX_BIN || (process.platform === 'win32' ? 'codex.cmd' : 'codex'), mode = process.env.CODEX_RUNNER_MODE || 'real' } = {}) {
    super();
    this.runStore = runStore;
    this.projects = projects;
    this.command = command;
    this.mode = mode;
    this.children = new Map();
    this.cancelled = new Set();
  }

  async start(projectId, runId, { input = '', resume = false } = {}) {
    const projectDir = this.projects.projectPath(projectId);
    const runDir = this.runStore.runRoot(projectId, runId);
    const run = await this.runStore.getRun(projectId, runId);
    if (run.status === 'cancelled') return { cancelled: true };
    await this.runStore.acquireLock(projectId, runId);
    if (this.cancelled.has(`${projectId}/${runId}`)) { await this.runStore.releaseLock(projectId, runId); return { cancelled: true }; }
    await this.runStore.updateRun(projectId, runId, { status: 'running', pid: null }, { type: 'run.started', message: resume ? 'Resuming Codex run' : 'Starting Codex run' });
    const prompt = this.buildPrompt(projectId, run, input, resume);
    if (this.mode === 'mock') return this.runMock(projectId, runId, runDir);
    let child;
    try {
      const args = ['exec', '--json'];
      if (process.env.CODEX_SKIP_GIT_CHECK !== 'false') args.push('--skip-git-repo-check');
      args.push(prompt);
      child = spawn(this.command, args, { cwd: projectDir, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
    } catch (error) {
      return this.fail(projectId, runId, error);
    }
    this.children.set(`${projectId}/${runId}`, child);
    await this.runStore.updateRun(projectId, runId, { pid: child.pid }, null);
    const rawLog = fsp.open(path.join(runDir, 'logs', 'codex.log'), 'a');
    const logHandle = await rawLog;
    let buffer = '';
    const onChunk = async (chunk, stream = 'stdout') => {
      const text = chunk.toString();
      await logHandle.write(text);
      if (stream === 'stderr') await this.runStore.appendEvent(projectId, runId, { type: 'log', level: 'error', message: text.trim() });
      else {
        buffer += text;
        const lines = buffer.split(/\r?\n/);
        buffer = lines.pop() || '';
        for (const line of lines) await this.handleJsonLine(projectId, runId, line);
      }
    };
    let settled = false;
    child.stdout.on('data', (chunk) => { onChunk(chunk).catch((error) => this.emit('error', error)); });
    child.stderr.on('data', (chunk) => { onChunk(chunk, 'stderr').catch((error) => this.emit('error', error)); });
    child.on('error', (error) => {
      if (settled || child.cancelled) return;
      settled = true;
      this.fail(projectId, runId, error).catch((e) => this.emit('error', e));
    });
    child.on('close', (code, signal) => {
      this.children.delete(`${projectId}/${runId}`);
      logHandle.close().catch(() => {});
      if (settled) return;
      settled = true;
      const done = code === 0 ? this.complete(projectId, runId) : this.fail(projectId, runId, new Error(`Codex exited with code ${code}${signal ? ` (${signal})` : ''}`));
      done.catch((error) => this.emit('error', error));
    });
    return { pid: child.pid, prompt };
  }

  buildPrompt(projectId, run, input, resume) {
    return [`You are operating the Video Project Console project ${projectId}.`, `Work only inside the project workspace and approved repository roots.`, `Read the configured skills under .agents/skills, especially video-spec-builder-personal and hyperframes.`, `Project manifest: ${path.join(this.projects.projectPath(projectId), 'project.json')}.`, `Run directory: ${this.runStore.runRoot(projectId, run.id)}.`, resume ? `Resume from checkpoint: ${JSON.stringify(run.checkpoint || run.resume_from || {})}` : '', `User request:\n${input || run.input || 'Continue the video engineering workflow.'}`, 'Emit concise progress and artifact information as JSONL when possible.'].filter(Boolean).join('\n\n');
  }

  async handleJsonLine(projectId, runId, line) {
    const text = line.trim();
    if (!text) return;
    let data;
    try { data = JSON.parse(text); } catch { return this.runStore.appendEvent(projectId, runId, { type: 'log', message: text }); }
    const sessionId = data.session_id || data.thread_id || data.conversation_id;
    if (sessionId) {
      await this.runStore.updateRun(projectId, runId, { codex_session_id: sessionId }, null);
      await fsp.writeFile(path.join(this.projects.projectPath(projectId), 'codex-session.json'), `${JSON.stringify({ run_id: runId, session_id: sessionId, updated_at: new Date().toISOString() }, null, 2)}\n`, 'utf8');
    }
    const type = data.type || data.event || data.kind;
    if (type === 'progress' || data.percent != null) {
      const event = await this.runStore.appendEvent(projectId, runId, { type: 'progress', stage: data.stage, percent: Number(data.percent), message: data.message || data.text || '' });
      await this.runStore.updateRun(projectId, runId, { active_stage: data.stage || null, progress: Number(data.percent) }, null);
      return event;
    }
    if (type === 'artifact.created' || data.artifact?.path) return this.runStore.addArtifact(projectId, runId, data.artifact || data);
    if (type === 'user.input_required' || type === 'input_required') return this.runStore.updateRun(projectId, runId, { status: 'waiting_for_input' }, { type: 'user.input_required', message: data.message || data.prompt });
    if (type === 'stage.started' || type === 'stage.completed' || type === 'stage.failed') {
      const event = await this.runStore.appendEvent(projectId, runId, { type, stage: data.stage, message: data.message || data.text || '' });
      if (data.stage) await this.runStore.updateRun(projectId, runId, { active_stage: data.stage }, null);
      return event;
    }
    return this.runStore.appendEvent(projectId, runId, { type: 'log', message: data.message || data.text || text, data });
  }

  async runMock(projectId, runId, runDir) {
    const key = `${projectId}/${runId}`;
    if (this.cancelled.has(key)) { this.cancelled.delete(key); this.children.delete(key); return; }
    const steps = [['analysis', 20], ['storyboard', 40], ['spec', 60], ['composition', 80], ['inspect', 100]];
    for (const [stage, percent] of steps) {
      if (!this.children.has(key)) this.children.set(key, { mock: true, killed: false });
      const child = this.children.get(key);
      if (child?.killed || this.cancelled.has(key)) { this.cancelled.delete(key); this.children.delete(key); return; }
      await this.runStore.appendEvent(projectId, runId, { type: 'stage.started', stage, message: `Mock ${stage}` });
      await new Promise((resolve) => setTimeout(resolve, 15));
      await this.runStore.appendEvent(projectId, runId, { type: 'progress', stage, percent, message: `${stage} ${percent}%` });
      await this.runStore.updateRun(projectId, runId, { active_stage: stage, progress: percent }, null);
      await this.runStore.appendEvent(projectId, runId, { type: 'stage.completed', stage, message: `Completed ${stage}` });
      await this.runStore.saveCheckpoint(projectId, runId, { stage, percent });
    }
    await fsp.writeFile(path.join(runDir, 'logs', 'codex.log'), 'mock runner completed\n', { flag: 'a' });
    await this.complete(projectId, runId);
    this.children.delete(`${projectId}/${runId}`);
  }

  async complete(projectId, runId) {
    await this.runStore.updateRun(projectId, runId, { status: 'completed', pid: null }, { type: 'run.completed', message: 'Run completed' });
    await this.runStore.releaseLock(projectId, runId);
  }

  async fail(projectId, runId, error) {
    await this.runStore.updateRun(projectId, runId, { status: 'failed', pid: null, error: error.message }, { type: 'run.failed', message: error.message });
    await this.runStore.releaseLock(projectId, runId);
  }

  async cancel(projectId, runId) {
    const key = `${projectId}/${runId}`;
    const current = await this.runStore.getRun(projectId, runId);
    if (['completed', 'failed', 'cancelled', 'interrupted'].includes(current.status)) return current;
    const child = this.children.get(key);
    this.cancelled.add(key);
    if (child?.mock) child.killed = true;
    else if (child) { child.cancelled = true; child.kill('SIGTERM'); }
    await this.runStore.updateRun(projectId, runId, { status: 'cancelled', pid: null }, { type: 'run.cancelled', message: 'Run cancelled by user' });
    await this.runStore.releaseLock(projectId, runId);
    if (!child?.mock) this.children.delete(key);
  }
}
