import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { assertSlug, rootPaths, safePath, slugify } from './pathSafety.js';
import { atomicWriteJson, ensureDir, listFilesRecursive, mediaType, readJson } from './fileStore.js';

const now = () => new Date().toISOString();

export class ProjectStore {
  constructor(workspaceRoot) {
    this.paths = rootPaths(workspaceRoot);
  }

  async init() {
    await Promise.all(Object.values(this.paths).filter((p) => p !== this.paths.root).map(ensureDir));
  }

  projectPath(id) {
    const slug = assertSlug(id);
    return safePath(this.paths.projects, slug);
  }

  manifestPath(id) { return safePath(this.projectPath(id), 'project.json'); }

  async listProjects() {
    await this.init();
    const entries = await fsp.readdir(this.paths.projects, { withFileTypes: true });
    const projects = [];
    for (const entry of entries.filter((e) => e.isDirectory())) {
      const manifest = await readJson(path.join(this.paths.projects, entry.name, 'project.json'));
      if (manifest) projects.push(manifest);
      else projects.push(await this._buildManifest(entry.name));
    }
    return projects.sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
  }

  async _buildManifest(id) {
    const stat = await fsp.stat(this.projectPath(id));
    return { schema_version: 1, id, title: id, created_at: stat.birthtime.toISOString(), updated_at: stat.mtime.toISOString(), status: 'ready', assets: [] };
  }

  async getProject(id) {
    const project = await readJson(this.manifestPath(id));
    if (!project) throw Object.assign(new Error('项目不存在'), { status: 404, code: 'PROJECT_NOT_FOUND' });
    return project;
  }

  async createProject({ id, slug, title, name, skills } = {}) {
    const projectSlug = slugify(id || slug || title || name);
    const normalizedTitle = title || name || projectSlug;
    const slugValue = assertSlug(projectSlug);
    const projectDir = this.projectPath(slugValue);
    await this.init();
    try { await fsp.mkdir(projectDir); } catch (error) {
      if (error.code === 'EEXIST') throw Object.assign(new Error('项目已存在'), { status: 409, code: 'PROJECT_EXISTS' });
      throw error;
    }
    const created = now();
    const manifest = { schema_version: 1, id: slugValue, title: normalizedTitle, name: normalizedTitle, created_at: created, updated_at: created, status: 'ready', active_run_id: null, skills: skills || ['video-spec-director-dev', 'hyperframes'], assets: [], storyboard_path: 'storyboard.json', spec_path: 'video-spec.md', composition_path: 'hyperframes/', latest_output: null };
    await Promise.all(['analysis', 'hyperframes', 'runs'].map((name) => ensureDir(path.join(projectDir, name))));
    await atomicWriteJson(path.join(projectDir, 'project.json'), manifest);
    await Promise.all([
      fsp.writeFile(path.join(projectDir, 'storyboard.json'), '{\n  "schema_version": 1,\n  "scenes": []\n}\n', 'utf8'),
      fsp.writeFile(path.join(projectDir, 'brief.md'), `# ${normalizedTitle}\n\n`, 'utf8'),
      fsp.writeFile(path.join(projectDir, 'edit-plan.md'), '# Edit plan\n\n', 'utf8'),
      fsp.writeFile(path.join(projectDir, 'video-spec.md'), '# Video spec\n\n', 'utf8'),
    ]);
    return manifest;
  }

  async updateProject(id, patch) {
    const current = await this.getProject(id);
    const allowed = ['title', 'status', 'skills', 'storyboard_path', 'spec_path', 'composition_path', 'latest_output', 'active_run_id'];
    for (const key of allowed) if (patch && Object.prototype.hasOwnProperty.call(patch, key)) current[key] = patch[key];
    current.updated_at = now();
    await atomicWriteJson(this.manifestPath(id), current);
    return current;
  }

  async listAssets(id) {
    const project = await this.getProject(id);
    return project.assets || [];
  }

  async registerAsset(id, inputPath, notes = '') {
    const project = await this.getProject(id);
    const slug = assertSlug(id);
    const assetRoot = safePath(this.paths.assets, slug);
    const candidate = safePath(assetRoot, inputPath, { allowMissing: false });
    const stat = await fsp.stat(candidate);
    if (!stat.isFile()) throw Object.assign(new Error('素材必须是文件'), { status: 400, code: 'ASSET_NOT_FILE' });
    const rel = path.relative(this.paths.root, candidate).split(path.sep).join('/');
    const metadata = await probeMedia(candidate);
    const item = { id: `asset-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, path: rel, relative_path: path.relative(assetRoot, candidate).split(path.sep).join('/'), label: path.basename(candidate), media_type: metadata.media_type || mediaType(candidate), size: stat.size, modified_at: stat.mtime.toISOString(), notes: notes || undefined, metadata };
    project.assets = [...(project.assets || []).filter((asset) => asset.path !== rel), item];
    project.updated_at = now();
    await atomicWriteJson(this.manifestPath(id), project);
    return item;
  }

  async listProjectFiles(id) {
    return listFilesRecursive(this.projectPath(id));
  }

  async readProjectFile(id, relativePath) {
    const full = safePath(this.projectPath(id), relativePath, { allowMissing: false });
    const stat = await fsp.stat(full);
    if (!stat.isFile()) throw Object.assign(new Error('不是文件'), { status: 400 });
    return { full, stat, data: await fsp.readFile(full) };
  }

  async listOutputs(id) {
    const root = safePath(this.paths.outputs, assertSlug(id));
    await ensureDir(root);
    return listFilesRecursive(root);
  }

  nextRenderPath(id, extension = 'mp4') {
    const root = safePath(this.paths.outputs, assertSlug(id));
    let n = 1;
    while (fs.existsSync(path.join(root, `render-v${String(n).padStart(3, '0')}.${extension}`))) n += 1;
    return path.join(root, `render-v${String(n).padStart(3, '0')}.${extension}`);
  }
}

export async function probeMedia(filePath, timeoutMs = 8000) {
  const fallback = { media_type: mediaType(filePath) };
  return await new Promise((resolve) => {
    const child = spawn('ffprobe', ['-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filePath], { windowsHide: true });
    let stdout = '';
    const timer = setTimeout(() => { child.kill(); resolve(fallback); }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.on('error', () => { clearTimeout(timer); resolve(fallback); });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) return resolve(fallback);
      try {
        const parsed = JSON.parse(stdout);
        const stream = (parsed.streams || []).find((entry) => ['video', 'audio'].includes(entry.codec_type));
        resolve({ media_type: stream?.codec_type || fallback.media_type, duration: Number(parsed.format?.duration) || undefined, width: stream?.width, height: stream?.height, codec: stream?.codec_name, format: parsed.format?.format_name });
      } catch { resolve(fallback); }
    });
  });
}
