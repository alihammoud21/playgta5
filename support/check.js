'use strict';
const report = { browser: navigator.userAgent, secureContext: isSecureContext,
  crossOriginIsolated, sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
  offscreenCanvas: typeof OffscreenCanvas !== 'undefined', hardwareConcurrency: navigator.hardwareConcurrency,
  deviceMemoryGB: navigator.deviceMemory || 'not reported' };
const output = document.getElementById('report');
async function check() {
  let device;
  try {
    const response = await fetch('/', { cache: 'no-store' });
    report.pageHTTP = response.status;
    const html = await response.text();
    const build = html.match(/\/b\/([a-zA-Z0-9_-]+)\//);
    if (build) {
      const wasm = await fetch(`/b/${build[1]}/game.wasm`, { headers: { Range: 'bytes=0-3' } });
      report.wasmHTTP = wasm.status;
      if (wasm.status === 206) {
        report.wasmSignature = Array.from(new Uint8Array(await wasm.arrayBuffer())).join(',') === '0,97,115,109';
      } else {
        await wasm.body?.cancel();
        report.wasmSignature = false;
      }
    } else report.assetCheck = 'Cannot identify build; run file verification.';
    if (!navigator.gpu) throw new Error('WebGPU unavailable. Check browser updates and graphics acceleration.');
    const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
    if (!adapter) throw new Error('No WebGPU adapter available. Check chrome://gpu or edge://gpu.');
    report.adapter = adapter.info ? { vendor: adapter.info.vendor, architecture: adapter.info.architecture, description: adapter.info.description } : 'not reported';
    report.features = [...adapter.features].sort();
    report.limits = Object.fromEntries(['maxBufferSize', 'maxStorageBufferBindingSize', 'maxTextureDimension2D', 'maxInterStageShaderVariables'].map(k => [k, adapter.limits[k]]));
    device = await adapter.requestDevice();
    report.deviceCreation = 'passed (basic device only; gameplay uses additional features)';
  } catch (error) { report.error = error.message; }
  finally { device?.destroy(); }
  output.textContent = JSON.stringify(report, null, 2);
  const passed = !report.error && report.crossOriginIsolated && report.sharedArrayBuffer && report.offscreenCanvas && report.wasmSignature;
  document.getElementById('status').textContent = passed
    ? 'Basic checks passed. Start with lower memory; gameplay still depends on your GPU and the complete game data.'
    : 'A startup check failed or is incomplete. See the report below before launching.';
}
document.getElementById('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(output.textContent); document.getElementById('copy').textContent = 'Copied'; }
  catch { document.getElementById('copy').textContent = 'Select and copy the report above'; }
});
check();
