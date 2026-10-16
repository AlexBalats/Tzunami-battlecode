// Fetch the official engine.wasm from the local cambc map editor into tools/mapgen/.cache/
// (git-ignored). Usage: node tools/mapgen/fetch.mjs   (needs .venv/bin/cambc, or cambc on PATH)
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { HERE, WASM } from './engine.mjs';

const root = path.resolve(HERE, '..', '..');
const bin = fs.existsSync(path.join(root, '.venv/bin/cambc')) ? path.join(root, '.venv/bin/cambc') : 'cambc';
const editor = spawn(bin, ['mapeditor', '--no-browser'], { cwd: root });
const url = await new Promise((res, rej) => {
  let buf = '';
  editor.stdout.on('data', (d) => { buf += d; const m = buf.match(/http:\/\/[^\s/]+/); if (m) res(m[0]); });
  editor.on('exit', (c) => rej(new Error(`map editor exited ${c}`)));
  setTimeout(() => rej(new Error('map editor did not start')), 20000);
});
try {
  const html = await (await fetch(url + '/')).text();
  const js = html.match(/assets\/index-[^"']+\.js/)[0];
  const src = await (await fetch(`${url}/${js}`)).text();
  const wasm = src.match(/v0_0_1-[A-Za-z0-9_-]+\.wasm/)[0];
  const bytes = Buffer.from(await (await fetch(`${url}/assets/${wasm}`)).arrayBuffer());
  fs.mkdirSync(path.dirname(WASM), { recursive: true });
  fs.writeFileSync(WASM, bytes);
  console.log(`saved ${wasm} (${bytes.length} bytes) -> ${WASM}`);
} finally {
  editor.kill();
}
