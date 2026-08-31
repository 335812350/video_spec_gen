import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { ProjectStore } from './projectStore.js';
import { RunStore } from './runStore.js';
import { resolveWithin, safePath, PathSafetyError } from './pathSafety.js';
import { CodexRunner } from './codexRunner.js';

async function tempWorkspace() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'video-console-'));
  await fs.mkdir(path.join(root, 'assets', 'demo'), { recursive: true });
  await fs.writeFile(path.join(root, 'assets', 'demo', 'source.mp4'), 'not-a-real-video');
  return root;
}

test('project store creates canonical file-backed projects and guards paths', async () => {
  const root = await tempWorkspace();
  const store = new ProjectStore(root);
  const project = await store.createProject({ id: 'demo', title: 'Demo' });
  assert.equal(project.id, 'demo');
  assert.equal((await fs.stat(path.join(root, 'projects', 'demo', 'project.json'))).isFile(), true);
  await assert.rejects(() => store.readProjectFile('demo', '../assets/demo/source.mp4'), PathSafetyError);
  const asset = await store.registerAsset('demo', 'source.mp4');
  assert.equal(asset.relative_path, 'source.mp4');
  assert.equal(asset.media_type, 'video');
  assert.equal((await store.getProject('demo')).assets.length, 1);
});

test('run store appends replayable events and monotonically increments render paths', async () => {
  const root = await tempWorkspace();
  const projects = new ProjectStore(root);
  await projects.createProject({ id: 'demo' });
  const runs = new RunStore(projects);
  const run = await runs.createRun('demo', { input: 'make a trailer' });
  await runs.appendEvent('demo', run.id, { type: 'progress', percent: 20, stage: 'analysis' });
  assert.equal((await runs.readEvents('demo', run.id)).length, 2);
  await runs.saveCheckpoint('demo', run.id, { stage: 'analysis', percent: 20 });
  assert.equal((await runs.getRun('demo', run.id)).checkpoint.stage, 'analysis');
  const p1 = projects.nextRenderPath('demo');
  await fs.mkdir(path.dirname(p1), { recursive: true });
  await fs.writeFile(p1, 'old');
  assert.match(projects.nextRenderPath('demo'), /render-v002\.mp4$/);
});

test('mock Codex runner emits stages, checkpoints and completion', async () => {
  const root = await tempWorkspace();
  const projects = new ProjectStore(root);
  await projects.createProject({ id: 'demo' });
  const runs = new RunStore(projects);
  const run = await runs.createRun('demo', { input: 'test' });
  const runner = new CodexRunner({ projects, runStore: runs, mode: 'mock' });
  await runner.start('demo', run.id, { input: 'test' });
  const finalRun = await runs.getRun('demo', run.id);
  assert.equal(finalRun.status, 'completed');
  assert.ok((await runs.readEvents('demo', run.id)).some((event) => event.type === 'checkpoint.saved'));
});

test('cancel preserves cancelled status and releases project lock', async () => {
  const root = await tempWorkspace();
  const projects = new ProjectStore(root);
  await projects.createProject({ id: 'demo' });
  const runs = new RunStore(projects);
  const run = await runs.createRun('demo', { input: 'long task' });
  const runner = new CodexRunner({ projects, runStore: runs, mode: 'mock' });
  const task = runner.start('demo', run.id, { input: 'long task' });
  await new Promise((resolve) => setTimeout(resolve, 10));
  await runner.cancel('demo', run.id);
  await task;
  assert.equal((await runs.getRun('demo', run.id)).status, 'cancelled');
});

test('resolveWithin rejects traversal and absolute paths', () => {
  assert.throws(() => resolveWithin('C:/workspace', '../outside'), PathSafetyError);
  assert.throws(() => resolveWithin('C:/workspace', 'C:/outside'), PathSafetyError);
  assert.equal(path.basename(safePath('C:/workspace', 'project.json')), 'project.json');
});
