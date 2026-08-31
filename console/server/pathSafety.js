import fs from 'node:fs';
import path from 'node:path';

export class PathSafetyError extends Error {
  constructor(message, code = 'PATH_NOT_ALLOWED') {
    super(message);
    this.name = 'PathSafetyError';
    this.code = code;
    this.status = 400;
  }
}

export function slugify(value) {
  const slug = String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug;
}

export function assertSlug(value) {
  const raw = String(value ?? '').trim();
  const slug = raw;
  if (!slug || slug.length > 100 || !/^[a-z0-9\u4e00-\u9fff](?:[a-z0-9\u4e00-\u9fff-]*[a-z0-9\u4e00-\u9fff])?$/.test(slug)) {
    throw new PathSafetyError('项目 id 必须是 kebab-case slug', 'INVALID_SLUG');
  }
  return slug;
}

export function rootPaths(workspaceRoot) {
  const root = path.resolve(workspaceRoot);
  return {
    root,
    assets: path.join(root, 'assets'),
    projects: path.join(root, 'projects'),
    outputs: path.join(root, 'outputs'),
  };
}

export function resolveWithin(root, relativePath = '', { allowMissing = true } = {}) {
  const base = path.resolve(root);
  const raw = String(relativePath ?? '');
  if (path.isAbsolute(raw) || raw.includes('\0')) {
    throw new PathSafetyError('不允许使用绝对路径或非法路径');
  }
  const candidate = path.resolve(base, raw);
  if (candidate !== base && !candidate.startsWith(`${base}${path.sep}`)) {
    throw new PathSafetyError('路径超出工作区范围');
  }
  if (!allowMissing && !fs.existsSync(candidate)) {
    throw new PathSafetyError('目标文件不存在', 'NOT_FOUND');
  }
  return candidate;
}

export function assertNoSymlinkEscape(target, root) {
  const base = path.resolve(root);
  let current = path.resolve(target);
  const missing = [];
  while (current !== base && current.startsWith(`${base}${path.sep}`)) {
    if (fs.existsSync(current)) {
      const stat = fs.lstatSync(current);
      if (stat.isSymbolicLink()) {
        const real = fs.realpathSync(current);
        const relative = path.relative(base, real);
        if (relative.startsWith('..') || path.isAbsolute(relative)) {
          throw new PathSafetyError('符号链接指向工作区之外');
        }
      }
    } else {
      missing.push(current);
    }
    current = path.dirname(current);
  }
  if (current !== base) throw new PathSafetyError('路径超出工作区范围');
  return target;
}

export function safePath(root, relativePath, options = {}) {
  const target = resolveWithin(root, relativePath, options);
  return assertNoSymlinkEscape(target, root);
}
