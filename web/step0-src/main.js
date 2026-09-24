import { createApp } from 'vue';
import Step0App from './Step0App.vue';

let currentApp = null;
let currentRootInstance = null;

const GeoStep0Bridge = {
  mount(el, bridge) {
    if (currentApp) {
      currentApp.unmount();
      currentApp = null;
      currentRootInstance = null;
    }
    const container = typeof el === 'string' ? document.querySelector(el) : el;
    if (!container) {
      console.warn('[GEO_STEP0] 挂载节点不存在:', el);
      return null;
    }
    currentApp = createApp(Step0App, { bridge: bridge || {} });
    currentRootInstance = currentApp.mount(container);
    return currentRootInstance;
  },

  unmount() {
    if (currentApp) {
      currentApp.unmount();
      currentApp = null;
      currentRootInstance = null;
    }
  },

  refresh(opts) {
    if (currentRootInstance && currentRootInstance.refresh) {
      return currentRootInstance.refresh(opts);
    }
  },

  setSubStep(num) {
    if (currentRootInstance && currentRootInstance.setSubStep) {
      return currentRootInstance.setSubStep(num);
    }
  },

  renderPanel() {
    if (currentRootInstance && currentRootInstance.renderPanel) {
      return currentRootInstance.renderPanel();
    }
  },
};

if (typeof window !== 'undefined') {
  window.__GEO_STEP0__ = GeoStep0Bridge;
}

export default GeoStep0Bridge;
