import fs from 'node:fs/promises';
import path from 'node:path';

export async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

export async function atomicWriteJson(filePath, value) {
  await ensureDir(path.dirname(filePath));
  const temp = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(temp, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  await fs.rename(temp, filePath);
}

export async function readJson(filePath, fallback = null) {
  try {
    return JSON.parse(await fs.readFile(filePath, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return fallback;
    throw error;
  }
}

export async function listFilesRecursive(root, current = root) {
  const entries = await fs.readdir(current, { withFileTypes: true }).catch((error) => {
    if (error.code === 'ENOENT') return [];
    throw error;
  });
  const result = [];
  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.gitkeep') continue;
    const full = path.join(current, entry.name);
    if (entry.isDirectory()) result.push(...await listFilesRecursive(root, full));
    else if (entry.isFile()) {
      const stat = await fs.stat(full);
      result.push({ path: path.relative(root, full).split(path.sep).join('/'), size: stat.size, modified_at: stat.mtime.toISOString() });
    }
  }
  return result.sort((a, b) => a.path.localeCompare(b.path));
}

export function mediaType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (['.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'].includes(ext)) return 'video';
  if (['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg'].includes(ext)) return 'audio';
  if (['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'].includes(ext)) return 'image';
  if (['.md', '.txt', '.json', '.html', '.css', '.js'].includes(ext)) return 'text';
  return 'file';
}

