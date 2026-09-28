import { createApp } from 'vue';
import Step0App from './Step0App.vue';
import Step1App from './Step1App.vue';
import Step2App from './Step2App.vue';
import Step3App from './Step3App.vue';
import Step4App from './Step4App.vue';
import Step5App from './Step5App.vue';
import Step6App from './Step6App.vue';
import RecurringMonitorStudio from './components/daily/RecurringMonitorStudio.vue';

let currentApp0 = null;
let currentRootInstance0 = null;

let currentApp1 = null;
let currentRootInstance1 = null;

let currentApp2 = null;
let currentRootInstance2 = null;

let currentApp3 = null;
let currentRootInstance3 = null;

let currentApp4 = null;
let currentRootInstance4 = null;

let currentApp5 = null;
let currentRootInstance5 = null;

let currentApp6 = null;
let currentRootInstance6 = null;

let currentAppRecurring = null;
let currentRootInstanceRecurring = null;

export const GeoStep0Bridge = {
  mount(el, bridge) {
    if (currentApp0) {
      currentApp0.unmount();
      currentApp0 = null;
      currentRootInstance0 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP0] 挂载节点不存在:', el);
      return null;
    }
    currentApp0 = createApp(Step0App, { bridge: bridge || {} });
    currentRootInstance0 = currentApp0.mount(container);
    return currentRootInstance0;
  },

  unmount() {
    if (currentApp0) {
      currentApp0.unmount();
      currentApp0 = null;
      currentRootInstance0 = null;
    }
  },

  refresh(opts) {
    if (currentRootInstance0 && currentRootInstance0.refresh) {
      return currentRootInstance0.refresh(opts);
    }
  },

  setSubStep(num) {
    if (currentRootInstance0 && currentRootInstance0.setSubStep) {
      return currentRootInstance0.setSubStep(num);
    }
  },

  renderPanel() {
    if (currentRootInstance0 && currentRootInstance0.renderPanel) {
      return currentRootInstance0.renderPanel();
    }
  },
};

export const GeoStep1Bridge = {
  mount(el, bridge) {
    if (currentApp1) {
      currentApp1.unmount();
      currentApp1 = null;
      currentRootInstance1 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP1] 挂载节点不存在:', el);
      return null;
    }
    currentApp1 = createApp(Step1App, { bridge: bridge || {} });
    currentRootInstance1 = currentApp1.mount(container);
    return currentRootInstance1;
  },

  unmount() {
    if (currentApp1) {
      currentApp1.unmount();
      currentApp1 = null;
      currentRootInstance1 = null;
    }
  },
};

export const GeoStep2Bridge = {
  mount(el, bridge) {
    if (currentApp2) {
      currentApp2.unmount();
      currentApp2 = null;
      currentRootInstance2 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP2] 挂载节点不存在:', el);
      return null;
    }
    currentApp2 = createApp(Step2App, { bridge: bridge || {} });
    currentRootInstance2 = currentApp2.mount(container);
    return currentRootInstance2;
  },

  unmount() {
    if (currentApp2) {
      currentApp2.unmount();
      currentApp2 = null;
      currentRootInstance2 = null;
    }
  },
};

export const GeoStep3Bridge = {
  mount(el, bridge) {
    if (currentApp3) {
      currentApp3.unmount();
      currentApp3 = null;
      currentRootInstance3 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP3] 挂载节点不存在:', el);
      return null;
    }
    currentApp3 = createApp(Step3App, { bridge: bridge || {} });
    currentRootInstance3 = currentApp3.mount(container);
    return currentRootInstance3;
  },

  unmount() {
    if (currentApp3) {
      currentApp3.unmount();
      currentApp3 = null;
      currentRootInstance3 = null;
    }
  },
};

export const GeoStep4Bridge = {
  mount(el, bridge) {
    if (currentApp4) {
      currentApp4.unmount();
      currentApp4 = null;
      currentRootInstance4 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP4] 挂载节点不存在:', el);
      return null;
    }
    currentApp4 = createApp(Step4App, { bridge: bridge || {} });
    currentRootInstance4 = currentApp4.mount(container);
    return currentRootInstance4;
  },

  unmount() {
    if (currentApp4) {
      currentApp4.unmount();
      currentApp4 = null;
      currentRootInstance4 = null;
    }
  },
};

export const GeoStep5Bridge = {
  mount(el, bridge) {
    if (currentApp5) {
      currentApp5.unmount();
      currentApp5 = null;
      currentRootInstance5 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP5] 挂载节点不存在:', el);
      return null;
    }
    currentApp5 = createApp(Step5App, { bridge: bridge || {} });
    currentRootInstance5 = currentApp5.mount(container);
    return currentRootInstance5;
  },

  unmount() {
    if (currentApp5) {
      currentApp5.unmount();
      currentApp5 = null;
      currentRootInstance5 = null;
    }
  },

  refresh(opts) {
    if (currentRootInstance5 && currentRootInstance5.refresh) {
      return currentRootInstance5.refresh(opts);
    }
  },

  setSubStep(num) {
    if (currentRootInstance5 && currentRootInstance5.setSubStep) {
      return currentRootInstance5.setSubStep(num);
    }
  },
};

export const GeoStep6Bridge = {
  mount(el, bridge) {
    if (currentApp6) {
      currentApp6.unmount();
      currentApp6 = null;
      currentRootInstance6 = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP6] 挂载节点不存在:', el);
      return null;
    }
    currentApp6 = createApp(Step6App, { bridge: bridge || {} });
    currentRootInstance6 = currentApp6.mount(container);
    return currentRootInstance6;
  },

  unmount() {
    if (currentApp6) {
      currentApp6.unmount();
      currentApp6 = null;
      currentRootInstance6 = null;
    }
  },
};

export const GeoRecurringMonitorBridge = {
  mount(el, bridge) {
    if (currentAppRecurring) {
      currentAppRecurring.unmount();
      currentAppRecurring = null;
      currentRootInstanceRecurring = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_RECURRING] 挂载节点不存在:', el);
      return null;
    }
    currentAppRecurring = createApp(RecurringMonitorStudio, { bridge: bridge || {} });
    currentRootInstanceRecurring = currentAppRecurring.mount(container);
    return currentRootInstanceRecurring;
  },

  unmount() {
    if (currentAppRecurring) {
      currentAppRecurring.unmount();
      currentAppRecurring = null;
      currentRootInstanceRecurring = null;
    }
  },
};

if (typeof window !== 'undefined') {
  window.__GEO_STEP0__ = GeoStep0Bridge;
  window.__GEO_STEP1__ = GeoStep1Bridge;
  window.__GEO_STEP2__ = GeoStep2Bridge;
  window.__GEO_STEP3__ = GeoStep3Bridge;
  window.__GEO_STEP4__ = GeoStep4Bridge;
  window.__GEO_STEP5__ = GeoStep5Bridge;
  window.__GEO_STEP6__ = GeoStep6Bridge;
  window.__GEO_RECURRING__ = GeoRecurringMonitorBridge;
}

export default {
  step0: GeoStep0Bridge,
  step1: GeoStep1Bridge,
  step2: GeoStep2Bridge,
  step3: GeoStep3Bridge,
  step4: GeoStep4Bridge,
  step5: GeoStep5Bridge,
  step6: GeoStep6Bridge,
  recurring: GeoRecurringMonitorBridge,
};
