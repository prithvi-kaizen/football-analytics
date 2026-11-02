/* Shared fixture requests stay cached; failures can be retried without a reload. */
(function (root) {
  'use strict';
  function createFixtureLoader({fetchImpl = (...args) => fetch(...args), timeoutMs = 30000} = {}) {
    const cache = new Map();
    return function load(name) {
      if (!/^[a-z0-9_]+$/.test(name)) return Promise.reject(new Error('Unknown example.'));
      if (cache.has(name)) return cache.get(name);
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      const pending = (async () => {
        try {
          const response = await fetchImpl(`data/${name}.json`, {signal: controller.signal});
          if (!response.ok) throw new Error(`Could not load ${name} (HTTP ${response.status}). Retry this example.`);
          return await response.json();
        } catch (error) {
          if (controller.signal.aborted) throw new Error('This example took too long to load. Check your connection and retry.');
          throw error;
        } finally {
          clearTimeout(timer);
        }
      })();
      cache.set(name, pending);
      pending.catch(() => { if (cache.get(name) === pending) cache.delete(name); });
      return pending;
    };
  }
  const api = {createFixtureLoader};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.PossessionRequests = api;
})(typeof window !== 'undefined' ? window : {});
