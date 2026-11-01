/* Runs the unchanged Python research implementations away from the rendering thread. */
const INDEX_URL = new URL('./runtime/', self.location.href).href;
let runtime;
let queue = Promise.resolve();

async function initialize() {
  self.postMessage({type: 'status', message: 'Loading browser Python'});
  importScripts(`${INDEX_URL}pyodide.js`);
  const python = await loadPyodide({indexURL: INDEX_URL});
  self.postMessage({type: 'status', message: 'Loading NumPy and pandas'});
  // Pyodide can resolve loadPackage after a failed wheel request. Check imports
  // explicitly and retry transient static-host failures before declaring ready.
  for (let attempt = 1; attempt <= 3; attempt++) {
    await python.loadPackage(['numpy', 'pandas']);
    try {
      python.runPython('import numpy, pandas');
      break;
    } catch (error) {
      if (attempt === 3) throw new Error('The numerical packages could not be loaded. Check your connection and retry Python.');
      self.postMessage({type: 'status', message: `Retrying numerical package download (${attempt + 1}/3)`});
    }
  }
  const response = await fetch('./research-python.zip');
  if (!response.ok) throw new Error('The research source bundle could not be loaded.');
  python.unpackArchive(await response.arrayBuffer(), 'zip', {extractDir: '/research'});
  python.runPython("import sys\nsys.path.insert(0, '/research')\nfrom possession_lab.explorer_api import run_json");
  self.postMessage({type: 'ready'});
  return python;
}

self.onmessage = ({data}) => {
  queue = queue.then(async () => {
    try {
      runtime ||= initialize();
      const python = await runtime;
      if (data.type === 'initialize') return;
      if (!['scenario', 'observability'].includes(data.mode)) throw new Error('Unsupported research operation.');
      python.globals.set('_explorer_mode', data.mode);
      python.globals.set('_explorer_request', JSON.stringify(data.parameters || {}));
      const result = python.runPython('run_json(_explorer_mode, _explorer_request)');
      self.postMessage({type: 'result', id: data.id, result: JSON.parse(result)});
    } catch (error) {
      self.postMessage({type: 'error', id: data.id, message: String(error.message || error)});
    }
  });
};
