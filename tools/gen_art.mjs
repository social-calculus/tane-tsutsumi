// 既定デザインの絵を AI で作る。作り直すときだけ使う。
//   node tools/gen_art.mjs            足りない絵だけ作る
//   node tools/gen_art.mjs kani/top   指定した絵を作り直す
// プロンプトは designs/prompts.json。出力は designs/art/<design>_<slot>.png
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const API = process.env.IMAGE_API_URL; // OpenAI 互換で yuzu_images を返す画像 API
if (!API) throw new Error('IMAGE_API_URL を指定してください');
const { style, art } = JSON.parse(readFileSync(join(ROOT, 'designs/prompts.json'), 'utf8'));
const OUT = join(ROOT, 'designs/art');
mkdirSync(OUT, { recursive: true });

const only = process.argv.slice(2);
const jobs = Object.entries(art).filter(([key]) => (only.length ? only.includes(key) : !existsSync(join(OUT, `${key.replace('/', '_')}.png`))));

async function generate(key, subject) {
  const prompt = `Generate one square image. ${style} Subject: ${subject}`;
  for (const model of ['pro', 'flash']) {
    for (let attempt = 0; attempt < 3; attempt++) {
      const res = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], expect_images: true, priority: 'bulk', slot_timeout: 300 }),
        signal: AbortSignal.timeout(420_000),
      }).catch((e) => ({ ok: false, status: 0, text: async () => String(e) }));
      if (!res.ok) {
        console.log(`  ${key}: ${model} HTTP ${res.status} ${(await res.text()).slice(0, 120)}`);
        await new Promise((r) => setTimeout(r, 15_000));
        continue;
      }
      const data = await res.json();
      const b64 = data.yuzu_images?.find((i) => i.kind === 'generated')?.b64 ?? data.yuzu_images?.[0]?.b64;
      if (b64) {
        writeFileSync(join(OUT, `${key.replace('/', '_')}.png`), Buffer.from(b64, 'base64'));
        console.log(`  ${key}: OK (${model})`);
        return true;
      }
      console.log(`  ${key}: ${model} 画像なし ${JSON.stringify(data.choices?.[0]?.message?.content ?? '').slice(0, 120)}`);
    }
  }
  console.log(`  ${key}: FAILED`);
  return false;
}

const queue = [...jobs];
const results = await Promise.all(
  Array.from({ length: 3 }, async () => {
    let ok = true;
    while (queue.length) {
      const [key, subject] = queue.shift();
      ok = (await generate(key, subject)) && ok;
    }
    return ok;
  }),
);
process.exit(results.every(Boolean) ? 0 : 1);
