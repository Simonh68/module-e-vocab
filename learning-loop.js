((root, factory) => {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.EFN_LEARNING_LOOP = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, () => {
  const ERROR_GAP = 2;
  const SUCCESS_GAP_MIN = 4;
  const SUCCESS_GAP_MAX = 6;

  function successGap(seed) {
    const span = SUCCESS_GAP_MAX - SUCCESS_GAP_MIN + 1;
    return SUCCESS_GAP_MIN + (Math.abs(Number(seed) || 0) % span);
  }

  function insertAfterGap(rest, entry, gap, makeFiller) {
    const next = [...rest];
    let fillerIndex = 0;
    while (next.length < gap) {
      next.push(makeFiller(fillerIndex));
      fillerIndex += 1;
    }
    next.splice(gap, 0, entry);
    return next;
  }

  function scheduleAfterError(rest, entry, makeFiller) {
    return insertAfterGap(rest, entry, ERROR_GAP, makeFiller);
  }

  function scheduleAfterSuccess(rest, entry, seed, makeFiller) {
    return insertAfterGap(rest, entry, successGap(seed), makeFiller);
  }

  return {
    ERROR_GAP,
    SUCCESS_GAP_MIN,
    SUCCESS_GAP_MAX,
    successGap,
    insertAfterGap,
    scheduleAfterError,
    scheduleAfterSuccess
  };
});

(() => {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  const STORAGE_KEY = 'efn:band3:auto-audio:v1';
  const button = document.getElementById('audioStart');
  if (!button) return;

  const ICON_OFF = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.5 9.5a4 4 0 0 1 0 5"></path></svg>';
  const ICON_ON = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>';

  function readPreference() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) === 'on';
    } catch (_) {
      return false;
    }
  }

  function storeEnabled() {
    try {
      window.localStorage.setItem(STORAGE_KEY, 'on');
    } catch (_) {
      // The current page still works when storage is blocked.
    }
  }

  function applyAudioState(enabled) {
    if (typeof automaticAudioEnabled !== 'undefined') automaticAudioEnabled = enabled;
    if (enabled && typeof hasUserInteracted !== 'undefined') hasUserInteracted = true;

    button.setAttribute('aria-pressed', String(enabled));
    button.setAttribute('aria-label', enabled ? 'Automatic audio is on' : 'Turn on automatic audio');
    button.title = enabled ? 'Automatic audio is on' : 'Turn on automatic audio';
    button.innerHTML = enabled ? ICON_ON : ICON_OFF;
    button.disabled = enabled;
  }

  function resumePersistedAudio() {
    if (!readPreference()) return;
    applyAudioState(true);
    if ('speechSynthesis' in window) window.speechSynthesis.resume();
    if (typeof scheduleWordSpeech === 'function') scheduleWordSpeech();
  }

  const originalEnableAutomaticAudio = window.enableAutomaticAudio;
  if (typeof originalEnableAutomaticAudio === 'function') {
    window.enableAutomaticAudio = function persistedEnableAutomaticAudio(event) {
      const result = originalEnableAutomaticAudio.call(this, event);
      storeEnabled();
      applyAudioState(true);
      return result;
    };
  }

  const originalPlayAudio = window.playAudio;
  if (typeof originalPlayAudio === 'function') {
    window.playAudio = function persistedPlayAudio(event) {
      const result = originalPlayAudio.call(this, event);
      storeEnabled();
      applyAudioState(true);
      return result;
    };
  }

  const enabled = readPreference();
  applyAudioState(enabled);

  if (enabled) {
    window.addEventListener('load', resumePersistedAudio, { once: true });

    const resumeAfterInteraction = () => {
      if ('speechSynthesis' in window) window.speechSynthesis.resume();
      if (
        typeof scheduleWordSpeech === 'function' &&
        (!('speechSynthesis' in window) || (!window.speechSynthesis.speaking && !window.speechSynthesis.pending))
      ) {
        scheduleWordSpeech();
      }
    };

    document.addEventListener('pointerdown', resumeAfterInteraction, { once: true, capture: true });
    document.addEventListener('keydown', resumeAfterInteraction, { once: true, capture: true });
  }
})();

(() => {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  if (new URLSearchParams(window.location.search).get('efn_feedback') !== '1') return;

  const back = document.querySelector('.card-back');
  if (!back || back.querySelector('[data-efn-binary-feedback]')) return;

  const style = document.createElement('style');
  style.textContent = `
    .efn-binary-feedback{display:flex;align-items:center;justify-content:center;gap:10px;margin-top:12px;direction:rtl;position:relative;min-height:46px}
    .efn-binary-feedback button{width:44px;height:44px;border:1px solid #cbd5e1;border-radius:999px;background:#fff;color:#1e293b;font-size:22px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:transform .14s ease,background .14s ease,border-color .14s ease}
    .efn-binary-feedback button:focus-visible{outline:3px solid #b45309;outline-offset:3px}
    .efn-binary-feedback button.efn-pressed{transform:scale(.84);background:#eef2ff;border-color:#818cf8}
    .efn-feedback-ack{position:absolute;inset-inline:0;top:100%;margin-top:2px;text-align:center;font-weight:800;font-size:.9rem;opacity:0;pointer-events:none}
    .efn-feedback-ack.efn-show{animation:efnFeedbackAck 4s ease forwards}
    @keyframes efnFeedbackAck{0%{opacity:0;transform:translateY(4px)}10%,70%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(-3px)}}
    @media (prefers-reduced-motion: reduce){.efn-binary-feedback button{transition:none}.efn-feedback-ack.efn-show{animation:none;opacity:1}}
  `;
  document.head.appendChild(style);

  const wrap = document.createElement('div');
  wrap.className = 'efn-binary-feedback';
  wrap.dataset.efnBinaryFeedback = 'true';
  wrap.setAttribute('role', 'group');
  wrap.setAttribute('aria-label', 'משוב על ההגדרה והדוגמה');

  const positive = document.createElement('button');
  positive.type = 'button';
  positive.textContent = '👍';
  positive.setAttribute('aria-label', 'משוב חיובי');

  const negative = document.createElement('button');
  negative.type = 'button';
  negative.textContent = '👎';
  negative.setAttribute('aria-label', 'משוב שלילי');

  const ack = document.createElement('span');
  ack.className = 'efn-feedback-ack';
  ack.textContent = '✓ תודה';
  ack.setAttribute('aria-hidden', 'true');

  const send = (eventName, button) => {
    button.classList.add('efn-pressed');
    window.setTimeout(() => button.classList.remove('efn-pressed'), 180);
    ack.classList.remove('efn-show');
    void ack.offsetWidth;
    ack.classList.add('efn-show');

    const target = `band3-${window.location.pathname.split('/').pop()?.replace(/\.html$/i, '').toLowerCase() || 'activity'}-definition-example`;
    const payload = {
      site: 'module-e',
      path: window.location.pathname,
      pageKind: 'group',
      event: eventName,
      context: { target, feedbackPoint: 'definition_example' }
    };
    try {
      fetch('https://englishfornoar.co.il/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
        mode: 'cors'
      }).catch(() => {});
    } catch (_) {}
  };

  positive.addEventListener('click', (event) => { event.stopPropagation(); send('feedback_positive', positive); });
  negative.addEventListener('click', (event) => { event.stopPropagation(); send('feedback_negative', negative); });
  wrap.append(positive, negative, ack);
  back.appendChild(wrap);
})();
