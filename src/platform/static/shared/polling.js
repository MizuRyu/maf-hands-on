/**
 * MAF Platform – Polling Utility
 * Workflow execution 用ポーリング (setInterval)
 */

/**
 * Start polling an endpoint at a fixed interval.
 * @param {string} path - API path (without /api prefix)
 * @param {function} callback - Called with response data on each poll
 * @param {object} opts
 * @param {number} opts.interval - Poll interval in ms (default: 3000)
 * @param {function} opts.onError - Error handler
 * @param {function} opts.shouldStop - Return true to stop polling
 * @returns {{ stop: function }} - Call stop() to cancel
 */
function startPolling(path, callback, opts = {}) {
  const interval = opts.interval || 3000;
  const onError = opts.onError || ((e) => console.error("Poll error:", e));
  const shouldStop = opts.shouldStop || (() => false);

  let timer = null;
  let running = false;

  async function poll() {
    if (running) return;
    running = true;
    try {
      const res = await api.get(path);
      callback(res.data || res);
      if (shouldStop(res.data || res)) {
        stop();
      }
    } catch (e) {
      onError(e);
    } finally {
      running = false;
    }
  }

  // Initial poll immediately
  poll();
  timer = setInterval(poll, interval);

  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  return { stop };
}

const TERMINAL_STATUSES = new Set([
  "completed", "failed", "cancelled",
]);

function isTerminalStatus(status) {
  return TERMINAL_STATUSES.has(status);
}
