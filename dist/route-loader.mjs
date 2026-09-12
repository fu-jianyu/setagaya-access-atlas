// Relative module URLs work at localhost, at a repository subpath, and on Pages.
let manifestPromise;
async function get(url) {
  const response = await fetch(url);
  if (!response.ok) throw Error(`Could not load route data (${response.status}). Download the complete repository.`);
  return response;
}
export async function loadRouteBuffer(category, progress = () => {}) {
  manifestPromise ??= get(new URL('data/route-manifest.json', import.meta.url)).then(r => r.json());
  const manifest = await manifestPromise;
  const entry = manifest.categories[category];
  if (!entry || manifest.version !== 1) throw Error('Unsupported or missing route-table manifest.');
  if (typeof DecompressionStream === 'undefined') throw Error('Please use a current browser with gzip stream support.');
  let index = 0;
  const compressed = new ReadableStream({
    async pull(controller) {
      try {
        if (index === entry.parts.length) { controller.close(); return; }
        const part = entry.parts[index];
        progress(index + 1, entry.parts.length);
        const bytes = await (await get(new URL(part.url, import.meta.url))).arrayBuffer();
        if (bytes.byteLength !== part.bytes) throw Error('Incomplete route chunk. Download or copy the complete project.');
        const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(b => b.toString(16).padStart(2, '0')).join('');
        if (hash !== part.sha256) throw Error('Route chunk integrity check failed. Download a fresh copy.');
        controller.enqueue(new Uint8Array(bytes));
        index++;
      } catch (error) { controller.error(error); }
    }
  });
  const buffer = await new Response(compressed.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  if (buffer.byteLength !== entry.uncompressedBytes) throw Error('Route table dimensions do not match its manifest.');
  return buffer;
}
