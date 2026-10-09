/**
 * Silicon3D: Interactive 3D GDSII Silicon Layout Visualizer
 * Application Orchestrator, UI Events, Telemetry & Export Controller
 * 
 * Author: Sujan S (@S-SUJAN-S) — Independent Hardware AI & Autonomous EDA Researcher
 * License: Apache 2.0 / MIT
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // UI DOM Elements
  const viewportContainer = document.getElementById('viewport-container');
  const loadingOverlay = document.getElementById('loading-overlay');
  const loadingStatusText = document.getElementById('loading-status-text');
  const dragOverlay = document.getElementById('drag-overlay');

  const sampleSelect = document.getElementById('sample-select');
  const btnUploadGds = document.getElementById('btn-upload-gds');
  const gdsFileInput = document.getElementById('gds-file-input');

  const sliderExplode = document.getElementById('slider-explode');
  const labelExplodeVal = document.getElementById('label-explode-val');

  const btnToggle2d3d = document.getElementById('btn-toggle-2d3d');
  const textMode = document.getElementById('text-mode');
  const btnResetCam = document.getElementById('btn-reset-cam');

  const btnToggleLayers = document.getElementById('btn-toggle-layers');
  const layerPalette = document.getElementById('layer-palette');
  const layerList = document.getElementById('layer-list');
  const badgeLayerCount = document.getElementById('badge-layer-count');

  const btnAllLayersOn = document.getElementById('btn-all-layers-on');
  const btnAllLayersOff = document.getElementById('btn-all-layers-off');
  const btnMetalsOnly = document.getElementById('btn-metals-only');
  const btnFrontendOnly = document.getElementById('btn-frontend-only');

  const btnToggleSlicing = document.getElementById('btn-toggle-slicing');
  const slicingPanel = document.getElementById('slicing-panel');
  const chkSliceEnable = document.getElementById('chk-slice-enable');
  const sliderSliceX = document.getElementById('slider-slice-x');
  const sliderSliceY = document.getElementById('slider-slice-y');
  const sliderSliceZ = document.getElementById('slider-slice-z');
  const labelSliceX = document.getElementById('label-slice-x');
  const labelSliceY = document.getElementById('label-slice-y');
  const labelSliceZ = document.getElementById('label-slice-z');
  const btnResetSlice = document.getElementById('btn-reset-slice');

  const btnToggleRuler = document.getElementById('btn-toggle-ruler');
  const rulerBanner = document.getElementById('ruler-banner');
  const rulerDist = document.getElementById('ruler-dist');
  const rulerDx = document.getElementById('ruler-dx');
  const rulerDy = document.getElementById('ruler-dy');
  const btnClearRuler = document.getElementById('btn-clear-ruler');

  const btnExportGlb = document.getElementById('btn-export-glb');
  const btnSnapshot = document.getElementById('btn-snapshot');

  const hudTopModule = document.getElementById('hud-top-module');
  const hudDieDim = document.getElementById('hud-die-dim');
  const hudDieArea = document.getElementById('hud-die-area');
  const hudPolys = document.getElementById('hud-polys');
  const hudActiveLayers = document.getElementById('hud-active-layers');
  const hudCursorCoords = document.getElementById('hud-cursor-coords');
  const hudFps = document.getElementById('hud-fps');

  // Core Engine Instances
  let viewer = null;
  const parser = new GdsParser();
  let currentTopCell = 'chip_top';

  // Canonical Sample Paths
  const CANONICAL_SAMPLES = {
    alu4bit: 'samples/alu4bit.gds',
    full_adder: 'samples/full_adder.gds',
    uart_top: 'samples/uart_top.gds'
  };

  /**
   * Helper: Show / Hide Loading Overlay with Status Message
   */
  function showLoading(message) {
    loadingStatusText.textContent = message;
    loadingOverlay.classList.add('active');
  }

  function hideLoading() {
    loadingOverlay.classList.remove('active');
  }

  /**
   * 1. Initialize Silicon 3D Viewer Engine
   */
  function initViewer() {
    viewer = new SiliconViewer3D(viewportContainer, {
      initialExplode: parseFloat(sliderExplode.value) || 2.5
    });
    window.viewer = viewer;

    // Telemetry & Cursor Coordinate Callback
    viewer.onTelemetryUpdate = (data) => {
      if (data.cursorX !== undefined) {
        hudCursorCoords.textContent = `X: ${data.cursorX.toFixed(2)} µm, Y: ${data.cursorY.toFixed(2)} µm`;
      }
      if (data.fps !== undefined) {
        hudFps.textContent = `${data.fps} FPS`;
      }
    };

    // Measurement Ruler Callback
    viewer.onRulerUpdate = (data) => {
      if (!data) {
        rulerBanner.classList.add('hidden');
        return;
      }
      rulerBanner.classList.remove('hidden');
      rulerDist.textContent = `${data.dist.toFixed(2)} µm`;
      rulerDx.textContent = `${data.dx.toFixed(2)} µm`;
      rulerDy.textContent = `${data.dy.toFixed(2)} µm`;
    };
  }

  /**
   * 2. Load and Process GDSII Buffer
   */
  async function loadGdsArrayBuffer(arrayBuffer, displayName = 'layout') {
    try {
      showLoading(`Decoding GDSII Stream for [${displayName}]...`);
      // Yield to browser UI thread
      await new Promise((r) => setTimeout(r, 40));

      parser.parse(arrayBuffer);

      showLoading('Flattening Cell Hierarchy & Normalizing Coordinates...');
      await new Promise((r) => setTimeout(r, 40));

      const layoutData = parser.flatten();
      currentTopCell = layoutData.topCell || displayName;

      showLoading(`Extruding 3D Silicon Geometry (${layoutData.totalPolygons.toLocaleString()} polygons)...`);
      await new Promise((r) => setTimeout(r, 40));

      viewer.loadLayout(layoutData);

      // Update UI Telemetry & Layer Palette
      updateTelemetry(layoutData);
      buildLayerPalette(layoutData);

      hideLoading();
    } catch (err) {
      hideLoading();
      console.error('Failed to load GDSII:', err);
      alert('Error parsing GDSII file: ' + err.message);
    }
  }

  /**
   * 3. Fetch GDSII File via URL
   */
  async function fetchAndLoadGds(url, sampleKey) {
    showLoading(`Fetching ${sampleKey || url}...`);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} fetching ${url}`);
      }
      const buffer = await response.arrayBuffer();
      await loadGdsArrayBuffer(buffer, sampleKey || 'demo');
    } catch (err) {
      hideLoading();
      console.error('Fetch error:', err);
      alert(`Could not load GDS file at "${url}": ${err.message}`);
    }
  }

  /**
   * 4. Update HUD Telemetry
   */
  function updateTelemetry(layoutData) {
    hudTopModule.textContent = layoutData.topCell || '—';

    const w = layoutData.bbox.width_um.toFixed(2);
    const h = layoutData.bbox.height_um.toFixed(2);
    hudDieDim.textContent = `${w} µm × ${h} µm`;

    const area = layoutData.bbox.area_um2;
    if (area >= 1e6) {
      hudDieArea.textContent = `${(area / 1e6).toFixed(3)} mm²`;
    } else {
      hudDieArea.textContent = `${Math.round(area).toLocaleString()} µm²`;
    }

    hudPolys.textContent = layoutData.totalPolygons.toLocaleString();

    const layerCount = Object.keys(layoutData.layers).length;
    hudActiveLayers.textContent = `${layerCount} / ${layerCount}`;
    badgeLayerCount.textContent = `${layerCount} Layers`;
  }

  /**
   * 5. Build Layer Palette UI Cards
   */
  function buildLayerPalette(layoutData) {
    layerList.innerHTML = '';
    const layerIds = Object.keys(layoutData.layers).map(Number).sort((a, b) => a - b);

    layerIds.forEach((layerNum) => {
      const meta = viewer.layerMeta.get(layerNum);
      if (!meta) return;

      const card = document.createElement('div');
      card.className = 'layer-item';
      card.dataset.layerId = layerNum;

      card.innerHTML = `
        <div class="layer-item-row">
          <div class="layer-left">
            <input type="checkbox" class="chk-layer" id="chk-l-${layerNum}" checked title="Toggle layer visibility">
            <div class="layer-swatch" style="background-color: ${meta.color};"></div>
            <div class="layer-info">
              <span class="layer-title">${meta.label || meta.name}</span>
              <span class="layer-sub">L${layerNum} • Elev: ${meta.elevation.toFixed(2)}µm</span>
            </div>
          </div>
          <div class="layer-right">
            <span class="poly-badge">${meta.polyCount.toLocaleString()}</span>
            <button class="solo-btn" id="solo-l-${layerNum}" title="Solo this layer">S</button>
          </div>
        </div>
        <div class="opacity-slider-row">
          <input type="range" class="opacity-slider" id="opac-l-${layerNum}" min="0.0" max="1.0" step="0.05" value="${meta.opacity !== undefined ? meta.opacity : 1.0}" title="Layer opacity">
        </div>
      `;

      // Checkbox visibility
      const chk = card.querySelector(`#chk-l-${layerNum}`);
      chk.addEventListener('change', (e) => {
        viewer.setLayerVisibility(layerNum, e.target.checked);
      });

      // Layer card hover highlight
      card.addEventListener('mouseenter', () => {
        viewer.highlightLayer(layerNum, true);
      });
      card.addEventListener('mouseleave', () => {
        viewer.highlightLayer(layerNum, false);
      });

      // Solo button
      const soloBtn = card.querySelector(`#solo-l-${layerNum}`);
      soloBtn.addEventListener('click', () => {
        const wasSolo = soloBtn.classList.contains('active');
        document.querySelectorAll('.solo-btn').forEach((b) => b.classList.remove('active'));

        if (wasSolo) {
          viewer.showAllLayers();
          document.querySelectorAll('.chk-layer').forEach((c) => (c.checked = true));
        } else {
          soloBtn.classList.add('active');
          viewer.soloLayer(layerNum);
          document.querySelectorAll('.chk-layer').forEach((c) => {
            c.checked = (c.id === `chk-l-${layerNum}`);
          });
        }
      });

      // Opacity slider
      const opacSlider = card.querySelector(`#opac-l-${layerNum}`);
      opacSlider.addEventListener('input', (e) => {
        viewer.setLayerOpacity(layerNum, parseFloat(e.target.value));
      });

      layerList.appendChild(card);
    });
  }

  /**
   * 6. Setup Event Listeners
   */
  function setupEventListeners() {
    // Sample Select Dropdown
    sampleSelect.addEventListener('change', (e) => {
      const sampleKey = e.target.value;
      if (CANONICAL_SAMPLES[sampleKey]) {
        fetchAndLoadGds(CANONICAL_SAMPLES[sampleKey], sampleKey);
      }
    });

    // Upload GDS File
    btnUploadGds.addEventListener('click', () => gdsFileInput.click());
    gdsFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (evt) => {
        loadGdsArrayBuffer(evt.target.result, file.name.replace(/\.gds$/i, ''));
      };
      reader.readAsArrayBuffer(file);
    });

    // Full-Window Drag and Drop
    window.addEventListener('dragover', (e) => {
      e.preventDefault();
      dragOverlay.classList.add('active');
    });

    window.addEventListener('dragleave', (e) => {
      if (e.relatedTarget === null) {
        dragOverlay.classList.remove('active');
      }
    });

    window.addEventListener('drop', (e) => {
      e.preventDefault();
      dragOverlay.classList.remove('active');
      const file = e.dataTransfer.files[0];
      if (file && /\.gds$/i.test(file.name)) {
        const reader = new FileReader();
        reader.onload = (evt) => {
          loadGdsArrayBuffer(evt.target.result, file.name.replace(/\.gds$/i, ''));
        };
        reader.readAsArrayBuffer(file);
      } else if (file) {
        alert('Please drop a valid .gds binary layout file.');
      }
    });

    // Exploded View Slider
    sliderExplode.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value);
      labelExplodeVal.textContent = `${val.toFixed(1)}x`;
      viewer.setExplodedView(val);
    });

    // 2D / 3D Mode Toggle
    btnToggle2d3d.addEventListener('click', () => {
      const is2D = viewer.toggle2D3D();
      if (is2D) {
        textMode.textContent = '3D View';
        btnToggle2d3d.classList.add('active');
      } else {
        textMode.textContent = '2D CAD';
        btnToggle2d3d.classList.remove('active');
      }
    });

    // Reset Camera
    btnResetCam.addEventListener('click', () => {
      viewer.resetCamera();
    });

    // Layer Palette Toggle
    btnToggleLayers.addEventListener('click', () => {
      layerPalette.classList.toggle('collapsed');
      btnToggleLayers.classList.toggle('active');
    });

    // Layer Quick Filters
    btnAllLayersOn.addEventListener('click', () => {
      viewer.showAllLayers();
      document.querySelectorAll('.chk-layer').forEach((c) => (c.checked = true));
      document.querySelectorAll('.solo-btn').forEach((b) => b.classList.remove('active'));
    });

    btnAllLayersOff.addEventListener('click', () => {
      viewer.hideAllLayers();
      document.querySelectorAll('.chk-layer').forEach((c) => (c.checked = false));
      document.querySelectorAll('.solo-btn').forEach((b) => b.classList.remove('active'));
    });

    btnMetalsOnly.addEventListener('click', () => {
      viewer.isolateMetalsOnly();
      const metalIds = new Set([68, 69, 70, 71, 72, 94, 95, 122]);
      document.querySelectorAll('.chk-layer').forEach((c) => {
        const id = parseInt(c.id.replace('chk-l-', ''), 10);
        c.checked = metalIds.has(id);
      });
      document.querySelectorAll('.solo-btn').forEach((b) => b.classList.remove('active'));
    });

    btnFrontendOnly.addEventListener('click', () => {
      viewer.isolateFrontEndOnly();
      const feIds = new Set([64, 65, 66, 67, 78, 81, 83, 93]);
      document.querySelectorAll('.chk-layer').forEach((c) => {
        const id = parseInt(c.id.replace('chk-l-', ''), 10);
        c.checked = feIds.has(id);
      });
      document.querySelectorAll('.solo-btn').forEach((b) => b.classList.remove('active'));
    });

    // Slicing Panel Toggle
    btnToggleSlicing.addEventListener('click', () => {
      slicingPanel.classList.toggle('hidden');
      btnToggleSlicing.classList.toggle('active');
    });

    chkSliceEnable.addEventListener('change', (e) => {
      viewer.setSlicingEnabled(e.target.checked);
    });

    sliderSliceX.addEventListener('input', (e) => {
      const v = parseFloat(e.target.value);
      labelSliceX.textContent = `${Math.round(v * 100)}%`;
      viewer.setSliceX(v);
    });

    sliderSliceY.addEventListener('input', (e) => {
      const v = parseFloat(e.target.value);
      labelSliceY.textContent = `${Math.round(v * 100)}%`;
      viewer.setSliceY(v);
    });

    sliderSliceZ.addEventListener('input', (e) => {
      const v = parseFloat(e.target.value);
      labelSliceZ.textContent = `${Math.round(v * 100)}%`;
      viewer.setSliceZ(v);
    });

    btnResetSlice.addEventListener('click', () => {
      sliderSliceX.value = 1.0; labelSliceX.textContent = '100%';
      sliderSliceY.value = 1.0; labelSliceY.textContent = '100%';
      sliderSliceZ.value = 1.0; labelSliceZ.textContent = '100%';
      viewer.setSliceX(1.0);
      viewer.setSliceY(1.0);
      viewer.setSliceZ(1.0);
    });

    // Measurement Ruler Tool
    btnToggleRuler.addEventListener('click', () => {
      const active = !btnToggleRuler.classList.contains('active');
      btnToggleRuler.classList.toggle('active', active);
      viewer.setRulerActive(active);
    });

    btnClearRuler.addEventListener('click', () => {
      viewer.clearRuler();
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        viewer.clearRuler();
        if (btnToggleRuler.classList.contains('active')) {
          btnToggleRuler.classList.remove('active');
          viewer.setRulerActive(false);
        }
      }
    });

    // Export GLB
    btnExportGlb.addEventListener('click', () => {
      showLoading(`Exporting ${currentTopCell} to .glb 3D asset...`);
      setTimeout(() => {
        try {
          viewer.exportGLB(`${currentTopCell}_sky130.glb`);
          hideLoading();
        } catch (err) {
          hideLoading();
          alert('GLTF export error: ' + err.message);
        }
      }, 50);
    });

    // Snapshot PNG
    btnSnapshot.addEventListener('click', () => {
      viewer.captureSnapshot(`${currentTopCell}_silicon3d.png`);
    });
  }

  /**
   * 7. Process URL Parameters for Direct Deep-Linking
   */
  function handleUrlParameters() {
    const params = new URLSearchParams(window.location.search);
    const demoParam = params.get('demo');
    const urlParam = params.get('url');

    if (urlParam) {
      fetchAndLoadGds(urlParam, 'remote_layout');
    } else if (demoParam && (demoParam === 'alu4bit' || demoParam === 'full_adder' || demoParam === 'uart' || demoParam === 'uart_top')) {
      const key = (demoParam === 'uart') ? 'uart_top' : demoParam;
      sampleSelect.value = key;
      fetchAndLoadGds(CANONICAL_SAMPLES[key], key);
    } else {
      // Default initial layout: alu4bit
      sampleSelect.value = 'alu4bit';
      fetchAndLoadGds(CANONICAL_SAMPLES.alu4bit, 'alu4bit');
    }
  }

  // Bootstrap Application
  initViewer();
  setupEventListeners();
  handleUrlParameters();
});
