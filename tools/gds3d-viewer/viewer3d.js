/**
 * Silicon3D: Interactive 3D GDSII Silicon Layout Visualizer
 * Three.js 3D Silicon Extrusion, Exploded View, PBR Studio Lighting & CAD Engine
 * 
 * Author: Sujan S (@S-SUJAN-S) — Independent Hardware AI & Autonomous EDA Researcher
 * License: Apache 2.0 / MIT
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.SiliconViewer3D = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // SkyWater 130nm Physical Metallization, Vias, Contacts & Diffusion Stackup
  // Authenticated against official sky130A.lyp, sky130A.map, and sky130A.tech
  // Implements authentic contiguous physical Z heights, vertical tungsten/copper via plugs,
  // flat surface pin ports (never floating 3D pillars!), and non-fogging boundary outlines
  const SKY130_STACKUP = {
    // 1. Sub-surface Well Doping & Implants (Sunken bulk Z <= 0, subtle non-fogging)
    '64/20':  { name: 'nwell',       label: 'N-Well (L64/20)',           color: '#047857', elevation: -0.60, thickness: 0.50, opacity: 0.15, metalness: 0.05, roughness: 0.90, depthWrite: false, type: 'subsurface' },
    '93/44':  { name: 'nsdm',        label: 'N+ Source/Drain (L93/44)',  color: '#a855f7', elevation: -0.15, thickness: 0.12, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    '94/20':  { name: 'psdm',        label: 'P+ Source/Drain (L94/20)',  color: '#6366f1', elevation: -0.15, thickness: 0.12, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    '78/44':  { name: 'hvtp',        label: 'HV P-Tap (L78/44)',         color: '#ec4899', elevation: -0.12, thickness: 0.10, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    '95/20':  { name: 'npc',         label: 'Nitride Poly Cut (L95/20)', color: '#64748b', elevation: -0.08, thickness: 0.06, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    '81/4':   { name: 'standardc',   label: 'StdCell Core (L81/4)',      color: '#475569', elevation: 0.00,  thickness: 0.02, opacity: 0.10, metalness: 0.05, roughness: 0.90, isBoundary: true, type: 'marker' },
    '81/23':  { name: 'diode',       label: 'Antenna Diode (L81/23)',    color: '#06b6d4', elevation: 0.00,  thickness: 0.05, opacity: 0.20, metalness: 0.05, roughness: 0.90, depthWrite: false, type: 'subsurface' },
    '236/0':  { name: 'fill',        label: 'Core Margin (L236/0)',      color: '#334155', elevation: -0.05, thickness: 0.04, opacity: 0.10, metalness: 0.10, roughness: 0.85, depthWrite: false, type: 'subsurface' },

    // 2. Front-End-of-Line (FEOL) Active Transistors (Z in [0.00, 0.45] um) - Stable Matte Finish
    '65/20':  { name: 'diff',        label: 'Diffusion / Active (L65/20)',color: '#10b981', elevation: 0.00, thickness: 0.15, opacity: 0.95, metalness: 0.18, roughness: 0.65, emissiveIntensity: 0.0, type: 'frontend' },
    '65/44':  { name: 'tap',         label: 'Substrate Tap (L65/44)',    color: '#f43f5e', elevation: 0.00,  thickness: 0.15, opacity: 0.90, metalness: 0.18, roughness: 0.65, emissiveIntensity: 0.0, type: 'frontend' },
    '66/20':  { name: 'poly',        label: 'Polysilicon Gate (L66/20)', color: '#ef4444', elevation: 0.15,  thickness: 0.20, opacity: 0.98, metalness: 0.22, roughness: 0.60, emissiveIntensity: 0.0, type: 'frontend' },

    // 3. Middle-of-Line (MOL) Local Interconnect & Contacts (Anchored 5nm to avoid coplanar Z-fighting)
    '66/44':  { name: 'licon1',      label: 'LI Contact (L66/44)',       color: '#94a3b8', elevation: 0.145, thickness: 0.310, opacity: 1.00, metalness: 0.30, roughness: 0.62, emissiveIntensity: 0.0, type: 'via' },
    '67/20':  { name: 'li1',         label: 'Local Interconnect (L67/20)',color: '#0284c7', elevation: 0.45,  thickness: 0.20, opacity: 0.98, metalness: 0.28, roughness: 0.62, emissiveIntensity: 0.0, type: 'mol' },
    '67/44':  { name: 'mcon',        label: 'M1 Contact (L67/44)',       color: '#cbd5e1', elevation: 0.645, thickness: 0.210, opacity: 1.00, metalness: 0.30, roughness: 0.62, emissiveIntensity: 0.0, type: 'via' },

    // 4. Back-End-of-Line (BEOL) Metallization Interconnect Stack - Flicker-Free Satin PBR Metals
    '68/20':  { name: 'met1',        label: 'Metal 1 (L68/20)',          color: '#2563eb', elevation: 0.85,  thickness: 0.30, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    '68/44':  { name: 'via1',        label: 'Via 1 (L68/44)',            color: '#60a5fa', elevation: 1.145, thickness: 0.310, opacity: 1.00, metalness: 0.30, roughness: 0.62, emissiveIntensity: 0.0, type: 'via' },
    '69/20':  { name: 'met2',        label: 'Metal 2 (L69/20)',          color: '#f59e0b', elevation: 1.45,  thickness: 0.35, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    '69/44':  { name: 'via2',        label: 'Via 2 (L69/44)',            color: '#fbbf24', elevation: 1.795, thickness: 0.360, opacity: 1.00, metalness: 0.30, roughness: 0.62, emissiveIntensity: 0.0, type: 'via' },
    '70/20':  { name: 'met3',        label: 'Metal 3 (L70/20)',          color: '#059669', elevation: 2.15,  thickness: 0.40, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    '70/44':  { name: 'via3',        label: 'Via 3 (L70/44)',            color: '#34d399', elevation: 2.545, thickness: 0.460, opacity: 1.00, metalness: 0.30, roughness: 0.62, emissiveIntensity: 0.0, type: 'via' },
    '71/20':  { name: 'met4',        label: 'Metal 4 (L71/20)',          color: '#8b5cf6', elevation: 3.00,  thickness: 0.55, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    '71/44':  { name: 'via4',        label: 'Via 4 (L71/44)',            color: '#a78bfa', elevation: 3.545, thickness: 0.610, opacity: 1.00, metalness: 0.30, roughness: 0.62, emissiveIntensity: 0.0, type: 'via' },
    '72/20':  { name: 'met5',        label: 'Metal 5 (L72/20)',          color: '#eab308', elevation: 4.15,  thickness: 1.10, opacity: 1.00, metalness: 0.32, roughness: 0.60, emissiveIntensity: 0.0, type: 'metal' },

    // 5. CAD Pin Ports (Flat surface wireframe markers on parent layers, NEVER floating 3D pillars!)
    '64/16':  { name: 'nwell_pin',   label: 'N-Well Pin (L64/16)',       color: '#34d399', elevation: 0.01,  thickness: 0.00, opacity: 0.80, isPin: true, type: 'pin' },
    '122/16': { name: 'pwell_pin',   label: 'P-Well Pin (L122/16)',      color: '#6ee7b7', elevation: 0.01,  thickness: 0.00, opacity: 0.80, isPin: true, type: 'pin' },
    '67/16':  { name: 'li1_pin',     label: 'LI1 Pin (L67/16)',          color: '#38bdf8', elevation: 0.66,  thickness: 0.00, opacity: 0.85, isPin: true, type: 'pin' },
    '68/16':  { name: 'met1_pin',    label: 'Met1 Pin (L68/16)',         color: '#60a5fa', elevation: 1.16,  thickness: 0.00, opacity: 0.85, isPin: true, type: 'pin' },
    '69/16':  { name: 'met2_pin',    label: 'Met2 Pin (L69/16)',         color: '#fcd34d', elevation: 1.81,  thickness: 0.00, opacity: 0.85, isPin: true, type: 'pin' },
    '70/16':  { name: 'met3_pin',    label: 'Met3 Pin (L70/16)',         color: '#6ee7b7', elevation: 2.56,  thickness: 0.00, opacity: 0.85, isPin: true, type: 'pin' },
    '71/16':  { name: 'met4_pin',    label: 'Met4 Pin (L71/16)',         color: '#c4b5fd', elevation: 3.56,  thickness: 0.00, opacity: 0.85, isPin: true, type: 'pin' },
    '72/16':  { name: 'met5_pin',    label: 'Met5 Pin (L72/16)',         color: '#fde047', elevation: 5.26,  thickness: 0.00, opacity: 0.85, isPin: true, type: 'pin' },

    // 6. Die Boundary Outline
    '235/4':  { name: 'prBoundary',  label: 'PR / Die Boundary (L235/4)',color: '#38bdf8', elevation: 0.05,  thickness: 0.02, opacity: 0.90, isBoundary: true, type: 'marker' },

    // 7. Numeric Fallbacks for generic GDS files without datatypes
    64:  { name: 'nwell',       label: 'N-Well (L64)',            color: '#047857', elevation: -0.60, thickness: 0.50, opacity: 0.15, metalness: 0.05, roughness: 0.90, depthWrite: false, type: 'subsurface' },
    65:  { name: 'diff',        label: 'Diffusion / Active (L65)',color: '#10b981', elevation: 0.00,  thickness: 0.15, opacity: 0.95, metalness: 0.18, roughness: 0.65, emissiveIntensity: 0.0, type: 'frontend' },
    66:  { name: 'poly',        label: 'Polysilicon Gate (L66)',  color: '#ef4444', elevation: 0.15,  thickness: 0.20, opacity: 0.98, metalness: 0.22, roughness: 0.60, emissiveIntensity: 0.0, type: 'frontend' },
    67:  { name: 'li1',         label: 'Local Interconnect (L67)',color: '#0284c7', elevation: 0.45,  thickness: 0.20, opacity: 0.98, metalness: 0.28, roughness: 0.62, emissiveIntensity: 0.0, type: 'mol' },
    68:  { name: 'm1',          label: 'Metal 1 (L68)',           color: '#2563eb', elevation: 0.85,  thickness: 0.30, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    69:  { name: 'm2',          label: 'Metal 2 (L69)',           color: '#f59e0b', elevation: 1.45,  thickness: 0.35, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    70:  { name: 'm3',          label: 'Metal 3 (L70)',           color: '#059669', elevation: 2.15,  thickness: 0.40, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    71:  { name: 'm4',          label: 'Metal 4 (L71)',           color: '#8b5cf6', elevation: 3.00,  thickness: 0.55, opacity: 1.00, metalness: 0.28, roughness: 0.65, emissiveIntensity: 0.0, type: 'metal' },
    72:  { name: 'm5',          label: 'Metal 5 (L72)',           color: '#eab308', elevation: 4.15,  thickness: 1.10, opacity: 1.00, metalness: 0.32, roughness: 0.60, emissiveIntensity: 0.0, type: 'metal' },
    78:  { name: 'hvtp',        label: 'HV P-Tap (L78)',          color: '#ec4899', elevation: -0.12, thickness: 0.10, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    81:  { name: 'standardc',   label: 'StdCell Core (L81)',      color: '#475569', elevation: 0.00,  thickness: 0.02, opacity: 0.10, isBoundary: true, type: 'marker' },
    93:  { name: 'nsdm',        label: 'N+ Source/Drain (L93)',   color: '#a855f7', elevation: -0.15, thickness: 0.12, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    94:  { name: 'psdm',        label: 'P+ Source/Drain (L94)',   color: '#6366f1', elevation: -0.15, thickness: 0.12, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    95:  { name: 'npc',         label: 'Nitride Poly Cut (L95)',  color: '#64748b', elevation: -0.08, thickness: 0.06, opacity: 0.12, metalness: 0.05, roughness: 0.85, depthWrite: false, type: 'subsurface' },
    122: { name: 'pwell_pin',   label: 'P-Well Pin (L122)',       color: '#6ee7b7', elevation: 0.01,  thickness: 0.00, opacity: 0.80, isPin: true, type: 'pin' },
    235: { name: 'prBoundary',  label: 'PR / Die Boundary (L235)',color: '#38bdf8', elevation: 0.05,  thickness: 0.02, opacity: 0.90, isBoundary: true, type: 'marker' },
    236: { name: 'fill',        label: 'Core Margin (L236)',      color: '#334155', elevation: -0.05, thickness: 0.04, opacity: 0.10, metalness: 0.10, roughness: 0.85, depthWrite: false, type: 'subsurface' }
  };

  class SiliconViewer3D {
    constructor(containerElement, options = {}) {
      this.container = containerElement;
      this.options = Object.assign({
        antialias: true,
        alpha: false,
        initialExplode: 1.0 // 100% Real Physical Silicon Scale (1:1) by default
      }, options);

      this.scene = null;
      this.renderer = null;
      this.perspectiveCamera = null;
      this.orthographicCamera = null;
      this.activeCamera = null;
      this.controls = null;
      this.is2DMode = false;

      // Layout objects & data
      this.layoutGroup = null;
      this.substrateGroup = null;
      this.rulerGroup = null;
      this.layerMeshes = new Map(); // layerId -> Mesh
      this.layerMeta = new Map();   // layerId -> metadata
      this.currentLayout = null;

      // Exploded view
      this.explodeFactor = this.options.initialExplode;

      // Cross-section clipping planes
      this.clipPlaneX = null;
      this.clipPlaneY = null;
      this.clipPlaneZ = null;
      this.slicingEnabled = false;

      // Measurement tool
      this.rulerActive = false;
      this.rulerPoints = [];
      this.raycaster = null;
      this.mouse = null;
      this.onRulerUpdate = null;

      // Telemetry
      this.fps = 60;
      this._frameCount = 0;
      this._lastFpsTime = performance.now();
      this.onTelemetryUpdate = null;

      this._initThree();
      this._setupEnvironment();
      this._setupLights();
      this._setupClipping();
      this._setupEvents();
      this._animate();
    }

    _initThree() {
      const width = this.container.clientWidth || 800;
      const height = this.container.clientHeight || 600;

      // 1. Scene
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x060910); // Rich deep midnight background
      this.scene.fog = new THREE.FogExp2(0x060910, 0.0004);

      // 2. Cameras
      const aspect = width / height;
      this.perspectiveCamera = new THREE.PerspectiveCamera(40, aspect, 0.5, 4000);
      this.perspectiveCamera.position.set(0, -110, 95);
      this.perspectiveCamera.up.set(0, 0, 1); // Z is vertical in 3D silicon stackup!

      const frustumSize = 150;
      this.orthographicCamera = new THREE.OrthographicCamera(
        (frustumSize * aspect) / -2,
        (frustumSize * aspect) / 2,
        frustumSize / 2,
        frustumSize / -2,
        0.5,
        4000
      );
      this.orthographicCamera.position.set(0, 0, 500);
      this.orthographicCamera.up.set(0, 1, 0); // Y is up in 2D top-down view
      this.orthographicCamera.lookAt(0, 0, 0);

      this.activeCamera = this.perspectiveCamera;

      // 3. Renderer - Anti-Blink High-Precision WebGL Configuration
      this.renderer = new THREE.WebGLRenderer({
        antialias: this.options.antialias,
        alpha: this.options.alpha,
        preserveDrawingBuffer: true,
        powerPreference: 'high-performance',
        logarithmicDepthBuffer: true,
        precision: 'highp'
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.localClippingEnabled = true;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.0;
      this.renderer.outputEncoding = THREE.sRGBEncoding;
      this.container.appendChild(this.renderer.domElement);

      // 4. OrbitControls
      this.controls = new THREE.OrbitControls(this.activeCamera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.07;
      this.controls.screenSpacePanning = true;
      this.controls.maxDistance = 2500;
      this.controls.minDistance = 2;
      this.controls.target.set(0, 0, 0);

      // 5. Container groups
      this.layoutGroup = new THREE.Group();
      this.substrateGroup = new THREE.Group();
      this.rulerGroup = new THREE.Group();

      this.scene.add(this.substrateGroup);
      this.scene.add(this.layoutGroup);
      this.scene.add(this.rulerGroup);

      // Raycaster for cursor telemetry and ruler tool
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
    }

    /**
     * Synthetic Studio Environment Map
     * Generates a neutral soft-light studio environment so PBR metal layers have crisp specular reflections
     * without casting cyan or pastel color casts over the silicon.
     */
    _setupEnvironment() {
      if (typeof document === 'undefined' || !document.createElement) return;

      try {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        // Continuous smooth dark slate studio gradient (no harsh rectangular reflection flashes)
        const grad = ctx.createLinearGradient(0, 0, 0, 256);
        grad.addColorStop(0.0, '#334155'); // Soft slate ambient
        grad.addColorStop(0.3, '#1e293b');
        grad.addColorStop(0.7, '#0f172a');
        grad.addColorStop(1.0, '#020617');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 512, 256);

        const envTexture = new THREE.CanvasTexture(canvas);
        envTexture.mapping = THREE.EquirectangularReflectionMapping;
        envTexture.encoding = THREE.sRGBEncoding;

        this.scene.environment = envTexture;
      } catch (err) {
        console.warn('Synthetic envMap skipped:', err);
      }
    }

    /**
     * Anti-Flicker Studio EDA Lighting
     * High ambient baseline + gentle directional key light to provide crisp 3D relief without specular strobing
     */
    _setupLights() {
      // 1. High-fidelity balanced ambient illumination (stable from all camera angles, zero specular jitter)
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.88);
      this.scene.add(ambientLight);

      // 2. Soft sky/ground hemisphere fill
      const hemiLight = new THREE.HemisphereLight(0xe2e8f0, 0x0f172a, 0.35);
      hemiLight.position.set(0, 0, 200);
      this.scene.add(hemiLight);

      // 3. Gentle directional key light (provides 3D sidewall relief gradient without blinding specular strobe)
      const keyLight = new THREE.DirectionalLight(0xffffff, 0.42);
      keyLight.position.set(80, -70, 160);
      this.scene.add(keyLight);
    }

    _setupClipping() {
      // Slicing planes in world coordinate space
      this.clipPlaneX = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 1000);
      this.clipPlaneY = new THREE.Plane(new THREE.Vector3(0, -1, 0), 1000);
      this.clipPlaneZ = new THREE.Plane(new THREE.Vector3(0, 0, -1), 1000);
    }

    _setupEvents() {
      window.addEventListener('resize', this._onWindowResize.bind(this));

      // Pointer tracking for HUD cursor coords and ruler tool
      this.renderer.domElement.addEventListener('pointermove', this._onPointerMove.bind(this));
      this.renderer.domElement.addEventListener('pointerdown', this._onPointerDown.bind(this));
    }

    _onWindowResize() {
      if (!this.container) return;
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      const aspect = width / height;

      this.perspectiveCamera.aspect = aspect;
      this.perspectiveCamera.updateProjectionMatrix();

      const frustumSize = (this.currentLayout && this.currentLayout.bbox) ?
        Math.max(this.currentLayout.bbox.width_um, this.currentLayout.bbox.height_um) * 1.35 : 150;
      this.orthographicCamera.left = (-frustumSize * aspect) / 2;
      this.orthographicCamera.right = (frustumSize * aspect) / 2;
      this.orthographicCamera.top = frustumSize / 2;
      this.orthographicCamera.bottom = -frustumSize / 2;
      this.orthographicCamera.updateProjectionMatrix();

      this.renderer.setSize(width, height);
    }

    _onPointerMove(event) {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      // Update cursor coordinates on plane
      this.raycaster.setFromCamera(this.mouse, this.activeCamera);
      const groundPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
      const intersectionPoint = new THREE.Vector3();
      this.raycaster.ray.intersectPlane(groundPlane, intersectionPoint);

      if (this.onTelemetryUpdate) {
        this.onTelemetryUpdate({
          cursorX: intersectionPoint.x,
          cursorY: intersectionPoint.y,
          cursorZ: intersectionPoint.z,
          fps: this.fps
        });
      }

      // Live ruler preview
      if (this.rulerActive && this.rulerPoints.length === 1) {
        this._updateRulerPreview(intersectionPoint);
      }
    }

    _onPointerDown(event) {
      if (!this.rulerActive || event.button !== 0) return;

      const rect = this.renderer.domElement.getBoundingClientRect();
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      this.raycaster.setFromCamera(this.mouse, this.activeCamera);
      const groundPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
      const pt = new THREE.Vector3();
      this.raycaster.ray.intersectPlane(groundPlane, pt);

      if (this.rulerPoints.length === 0) {
        this.rulerPoints.push(pt.clone());
        this._renderRulerMarker(pt, 0x22d3ee);
      } else if (this.rulerPoints.length === 1) {
        this.rulerPoints.push(pt.clone());
        this._renderRulerMarker(pt, 0xf43f5e);
        this._finalizeRulerLine();
      }
    }

    _animate() {
      requestAnimationFrame(this._animate.bind(this));

      // Telemetry FPS calculation
      this._frameCount++;
      const now = performance.now();
      if (now - this._lastFpsTime >= 500) {
        this.fps = Math.round((this._frameCount * 1000) / (now - this._lastFpsTime));
        this._frameCount = 0;
        this._lastFpsTime = now;
      }

      this.controls.update();
      this.renderer.render(this.scene, this.activeCamera);
    }

    /**
     * Loads and visualizes flattened layout data from GdsParser.
     */
    loadLayout(layoutData) {
      this.currentLayout = layoutData;
      this.clear();

      const { bbox, layers } = layoutData;
      const width = bbox.width_um || 100;
      const height = bbox.height_um || 100;

      // 1. Render Substrate & Die Outline
      this._createSubstrateWafer(width, height);

      // 2. Build 3D Layer Meshes (1 merged BufferGeometry per layer)
      const layerNums = Object.keys(layers).sort((a, b) => {
        const partsA = String(a).split('/').map(Number);
        const partsB = String(b).split('/').map(Number);
        const lA = partsA[0] || 0, dA = partsA[1] || 0;
        const lB = partsB[0] || 0, dB = partsB[1] || 0;
        return lA !== lB ? lA - lB : dA - dB;
      });
      for (let i = 0; i < layerNums.length; i++) {
        const layerNum = layerNums[i];
        const polys = layers[layerNum];
        this._createLayerMesh(layerNum, polys);
      }

      // 3. Reset camera to frame the chip
      this.resetCamera();

      // 4. Apply initial exploded view elevation
      this.setExplodedView(this.explodeFactor);

      // 5. Update slicing plane limits to design bounding box
      const margin = Math.max(width, height) * 0.8;
      this.clipPlaneX.constant = margin;
      this.clipPlaneY.constant = margin;
      this.clipPlaneZ.constant = 50.0;
    }

    _createSubstrateWafer(width, height) {
      // Substrate wafer base plate (Dark polished semiconductor silicon)
      const waferW = Math.max(width * 1.4, width + 30);
      const waferH = Math.max(height * 1.4, height + 30);
      const waferThickness = 1.5;

      const waferGeom = new THREE.BoxGeometry(waferW, waferH, waferThickness);
      const waferMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a, // Deep slate polished silicon wafer
        metalness: 0.65,
        roughness: 0.30,
        clippingPlanes: this.slicingEnabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : []
      });
      const waferMesh = new THREE.Mesh(waferGeom, waferMat);
      waferMesh.position.set(0, 0, -waferThickness / 2);
      this.substrateGroup.add(waferMesh);

      // Die perimeter line (Cyan active area boundary)
      const halfW = width / 2;
      const halfH = height / 2;
      const borderGeom = new THREE.BufferGeometry();
      const borderVerts = new Float32Array([
        -halfW, -halfH, 0.01,
         halfW, -halfH, 0.01,
         halfW,  halfH, 0.01,
        -halfW,  halfH, 0.01,
        -halfW, -halfH, 0.01
      ]);
      borderGeom.setAttribute('position', new THREE.BufferAttribute(borderVerts, 3));
      const borderMat = new THREE.LineBasicMaterial({
        color: 0x38bdf8,
        linewidth: 2,
        transparent: true,
        opacity: 0.95
      });
      const borderLine = new THREE.Line(borderGeom, borderMat);
      this.substrateGroup.add(borderLine);

      // Substrate gridlines
      const grid = new THREE.GridHelper(Math.max(waferW, waferH), 24, 0x1e293b, 0x090d16);
      grid.rotation.x = Math.PI / 2;
      grid.position.z = -0.005;
      this.substrateGroup.add(grid);
    }

    _createLayerMesh(layerNum, polygons) {
      const def = this._getLayerDef(layerNum);
      const { elevation, thickness, color, opacity, metalness, roughness, emissive, emissiveIntensity, depthWrite } = def;

      // Special Case 1: Die Boundary (PR Boundary) - Render strictly as crisp outline wireframe
      // NEVER as an extruded solid slab, which would fog and bleach the chip in 3D and 2D!
      if (def.isBoundary || layerNum === 235 || layerNum === '235/4') {
        const linePositions = [];
        for (let pIdx = 0; pIdx < polygons.length; pIdx++) {
          const pts = polygons[pIdx].pts;
          const n = pts.length;
          if (n < 2) continue;
          const zLine = 0.05;
          for (let i = 0; i < n; i++) {
            const pA = pts[i];
            const pB = pts[(i + 1) % n];
            linePositions.push(pA[0], pA[1], zLine);
            linePositions.push(pB[0], pB[1], zLine);
          }
        }
        if (linePositions.length === 0) return;
        const lineGeom = new THREE.BufferGeometry();
        lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
        const lineMat = new THREE.LineBasicMaterial({
          color: new THREE.Color(color || '#38bdf8'),
          linewidth: 2,
          transparent: true,
          opacity: opacity !== undefined ? opacity : 0.90,
          clippingPlanes: this.slicingEnabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : []
        });
        const mesh = new THREE.LineSegments(lineGeom, lineMat);
        mesh.userData = {
          layerNum,
          name: def.name,
          label: def.label,
          baseElevation: elevation,
          thickness: thickness,
          color: color,
          opacity: opacity,
          polyCount: polygons.length,
          isBoundary: true,
          baseEmissiveIntensity: 0
        };
        this.layoutGroup.add(mesh);
        this.layerMeshes.set(layerNum, mesh);
        this.layerMeta.set(layerNum, Object.assign({}, def, { polyCount: polygons.length }));
        return;
      }

      // Special Case 2: CAD Pin Ports - Render as flat surface wireframe markers on their respective layer
      // NEVER as an extruded 3D vertical pillar shooting into the sky!
      if (def.isPin) {
        const linePositions = [];
        const zLine = elevation !== undefined ? elevation : 0.02;
        for (let pIdx = 0; pIdx < polygons.length; pIdx++) {
          const pts = polygons[pIdx].pts;
          const n = pts.length;
          if (n < 2) continue;
          for (let i = 0; i < n; i++) {
            const pA = pts[i];
            const pB = pts[(i + 1) % n];
            linePositions.push(pA[0], pA[1], zLine);
            linePositions.push(pB[0], pB[1], zLine);
          }
        }
        if (linePositions.length === 0) return;
        const lineGeom = new THREE.BufferGeometry();
        lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
        const lineMat = new THREE.LineBasicMaterial({
          color: new THREE.Color(color || '#38bdf8'),
          linewidth: 1.5,
          transparent: true,
          opacity: opacity !== undefined ? opacity : 0.85,
          clippingPlanes: this.slicingEnabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : []
        });
        const mesh = new THREE.LineSegments(lineGeom, lineMat);
        mesh.userData = {
          layerNum,
          name: def.name,
          label: def.label,
          baseElevation: elevation,
          thickness: 0,
          color: color,
          opacity: opacity,
          polyCount: polygons.length,
          isPin: true,
          baseEmissiveIntensity: 0
        };
        this.layoutGroup.add(mesh);
        this.layerMeshes.set(layerNum, mesh);
        this.layerMeta.set(layerNum, Object.assign({}, def, { polyCount: polygons.length }));
        return;
      }

      // Estimate vertex count to pre-allocate typed buffer
      let totalTrisEstimate = 0;
      for (let p = 0; p < polygons.length; p++) {
        const n = polygons[p].pts.length;
        if (n === 4) {
          totalTrisEstimate += 12; // 2 top + 2 bottom + 8 sides
        } else {
          totalTrisEstimate += (n - 2) * 2 + n * 2;
        }
      }

      const positions = new Float32Array(totalTrisEstimate * 9);
      const normals = new Float32Array(totalTrisEstimate * 9);
      let vOffset = 0;

      const z0 = elevation;
      const z1 = elevation + Math.max(0.04, thickness);

      const earcutFn = (typeof window !== 'undefined' && window.earcut) ?
        window.earcut : (typeof earcut !== 'undefined' ? earcut : null);

      for (let pIdx = 0; pIdx < polygons.length; pIdx++) {
        const poly = polygons[pIdx];
        let pts = poly.pts;
        const n = pts.length;
        if (n < 3) continue;

        // Ensure counter-clockwise winding so face normals always point outwards
        let area = 0;
        for (let i = 0, j = n - 1; i < n; j = i++) {
          area += (pts[j][0] * pts[i][1]) - (pts[i][0] * pts[j][1]);
        }
        if (area < 0) {
          pts = pts.slice().reverse();
        }

        if (n === 4) {
          // Fast-path optimized rectangle (90%+ of ASIC standard cells)
          const p0 = pts[0], p1 = pts[1], p2 = pts[2], p3 = pts[3];

          // 1. Top Face
          this._addTriangle(positions, normals, vOffset, p0[0], p0[1], z1, p1[0], p1[1], z1, p2[0], p2[1], z1, 0, 0, 1);
          vOffset += 9;
          this._addTriangle(positions, normals, vOffset, p0[0], p0[1], z1, p2[0], p2[1], z1, p3[0], p3[1], z1, 0, 0, 1);
          vOffset += 9;

          // 2. Bottom Face
          this._addTriangle(positions, normals, vOffset, p0[0], p0[1], z0, p2[0], p2[1], z0, p1[0], p1[1], z0, 0, 0, -1);
          vOffset += 9;
          this._addTriangle(positions, normals, vOffset, p0[0], p0[1], z0, p3[0], p3[1], z0, p2[0], p2[1], z0, 0, 0, -1);
          vOffset += 9;

          // 3. Side Walls (4 segments)
          this._addWallQuad(positions, normals, vOffset, p0[0], p0[1], p1[0], p1[1], z0, z1); vOffset += 18;
          this._addWallQuad(positions, normals, vOffset, p1[0], p1[1], p2[0], p2[1], z0, z1); vOffset += 18;
          this._addWallQuad(positions, normals, vOffset, p2[0], p2[1], p3[0], p3[1], z0, z1); vOffset += 18;
          this._addWallQuad(positions, normals, vOffset, p3[0], p3[1], p0[0], p0[1], z0, z1); vOffset += 18;
        } else {
          // Arbitrary N-gon: Ear-clipping triangulation
          let indices = null;
          if (earcutFn) {
            const flat = new Float64Array(n * 2);
            for (let i = 0; i < n; i++) {
              flat[i * 2] = pts[i][0];
              flat[i * 2 + 1] = pts[i][1];
            }
            indices = earcutFn(flat, null, 2);
          } else {
            indices = [];
            for (let i = 1; i < n - 1; i++) indices.push(0, i, i + 1);
          }

          if (indices && indices.length >= 3) {
            for (let t = 0; t < indices.length; t += 3) {
              const i0 = indices[t], i1 = indices[t + 1], i2 = indices[t + 2];
              // Top
              this._addTriangle(positions, normals, vOffset, pts[i0][0], pts[i0][1], z1, pts[i1][0], pts[i1][1], z1, pts[i2][0], pts[i2][1], z1, 0, 0, 1);
              vOffset += 9;
              // Bottom
              this._addTriangle(positions, normals, vOffset, pts[i0][0], pts[i0][1], z0, pts[i2][0], pts[i2][1], z0, pts[i1][0], pts[i1][1], z0, 0, 0, -1);
              vOffset += 9;
            }
          }

          // Side walls
          for (let i = 0; i < n; i++) {
            const cur = pts[i];
            const next = pts[(i + 1) % n];
            this._addWallQuad(positions, normals, vOffset, cur[0], cur[1], next[0], next[1], z0, z1);
            vOffset += 18;
          }
        }
      }

      if (vOffset === 0) return;

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(positions.subarray(0, vOffset), 3));
      geometry.setAttribute('normal', new THREE.BufferAttribute(normals.subarray(0, vOffset), 3));

      // Anti-Flicker Satin PBR Material: diffuse stability, zero specular flash, hardware backface culling
      const isOpaqueSolid = (opacity >= 0.90 && thickness > 0);
      const isVia = (def.type === 'via');
      const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        metalness: metalness !== undefined ? metalness : 0.28,
        roughness: roughness !== undefined ? roughness : 0.65,
        emissive: new THREE.Color(0x000000),
        emissiveIntensity: 0.0,
        transparent: opacity < 1.0,
        opacity: opacity !== undefined ? opacity : 1.0,
        side: isOpaqueSolid ? THREE.FrontSide : THREE.DoubleSide,
        depthWrite: depthWrite !== undefined ? depthWrite : (opacity >= 0.85),
        polygonOffset: isVia,
        polygonOffsetFactor: isVia ? -1.0 : 0,
        polygonOffsetUnits: isVia ? -2.0 : 0,
        clippingPlanes: this.slicingEnabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : []
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.userData = {
        layerNum,
        name: def.name,
        label: def.label,
        baseElevation: elevation,
        thickness: thickness,
        color: color,
        opacity: opacity,
        polyCount: polygons.length,
        baseEmissiveIntensity: 0.0
      };

      this.layoutGroup.add(mesh);
      this.layerMeshes.set(layerNum, mesh);
      this.layerMeta.set(layerNum, Object.assign({}, def, { polyCount: polygons.length }));
    }

    _addTriangle(pos, norm, offset, x0, y0, z0, x1, y1, z1, x2, y2, z2, nx, ny, nz) {
      pos[offset]     = x0; pos[offset + 1] = y0; pos[offset + 2] = z0;
      pos[offset + 3] = x1; pos[offset + 4] = y1; pos[offset + 5] = z1;
      pos[offset + 6] = x2; pos[offset + 7] = y2; pos[offset + 8] = z2;

      norm[offset]     = nx; norm[offset + 1] = ny; norm[offset + 2] = nz;
      norm[offset + 3] = nx; norm[offset + 4] = ny; norm[offset + 5] = nz;
      norm[offset + 6] = nx; norm[offset + 7] = ny; norm[offset + 8] = nz;
    }

    _addWallQuad(pos, norm, offset, x0, y0, x1, y1, z0, z1) {
      const dx = x1 - x0;
      const dy = y1 - y0;
      const len = Math.hypot(dx, dy) || 1e-5;
      const nx = dy / len;
      const ny = -dx / len;

      this._addTriangle(pos, norm, offset, x0, y0, z0, x1, y1, z0, x1, y1, z1, nx, ny, 0);
      this._addTriangle(pos, norm, offset + 9, x0, y0, z0, x1, y1, z1, x0, y0, z1, nx, ny, 0);
    }

    _getLayerDef(layerKey) {
      if (SKY130_STACKUP[layerKey]) return SKY130_STACKUP[layerKey];
      // Check if string has slash, try numeric layer
      if (typeof layerKey === 'string' && layerKey.includes('/')) {
        const parts = layerKey.split('/');
        const lNum = parseInt(parts[0], 10);
        const dNum = parseInt(parts[1], 10);
        if (dNum === 16 || dNum === 5) {
          // Pin port or text label: Flat surface marker on corresponding metal or substrate
          const baseZ = (lNum >= 68 && lNum <= 72) ? (0.85 + (lNum - 68) * 0.6) : 0.02;
          return {
            name: `pin_${lNum}`,
            label: `Pin (L${lNum}/${dNum})`,
            color: '#38bdf8',
            elevation: baseZ,
            thickness: 0,
            opacity: 0.85,
            isPin: true,
            type: 'pin'
          };
        }
        if (SKY130_STACKUP[lNum]) return SKY130_STACKUP[lNum];
      }
      const num = parseInt(layerKey, 10);
      if (!isNaN(num) && SKY130_STACKUP[num]) return SKY130_STACKUP[num];
      return this._getDynamicLayerDef(layerKey);
    }

    _getDynamicLayerDef(layerKey) {
      const parts = String(layerKey).split('/');
      const num = parseInt(parts[0], 10) || 1;
      const dt = parts[1] !== undefined ? parseInt(parts[1], 10) : 0;
      const isPin = (dt === 16 || dt === 5);
      const hue = (num * 137.5) % 360;
      const c = `hsl(${Math.round(hue)}, 80%, 60%)`;
      return {
        name: `layer_${layerKey}`,
        label: isPin ? `Pin (L${layerKey})` : `Layer ${layerKey}`,
        color: c,
        elevation: (num % 10) * 0.45,
        thickness: isPin ? 0 : 0.20,
        opacity: isPin ? 0.85 : 0.90,
        metalness: 0.28,
        roughness: 0.65,
        emissive: c,
        emissiveIntensity: 0.0,
        isPin: isPin,
        type: isPin ? 'pin' : 'metal'
      };
    }

    /**
     * Interactive Exploded View: Z-axis scaling
     */
    setExplodedView(factor) {
      this.explodeFactor = Math.max(1.0, factor);
      this.layerMeshes.forEach((mesh) => {
        const baseZ = mesh.userData.baseElevation || 0;
        if (baseZ > 0) {
          mesh.position.z = baseZ * (this.explodeFactor - 1.0);
        } else {
          mesh.position.z = 0;
        }
      });
    }

    /**
     * Camera View Angle Presets ("All Angles")
     */
    setCameraAngle(angleKey) {
      const bbox = (this.currentLayout && this.currentLayout.bbox) ? this.currentLayout.bbox : { width_um: 75, height_um: 75 };
      const maxDim = Math.max(bbox.width_um, bbox.height_um, 20);
      const dist = maxDim * 1.5;

      if (angleKey === 'top' && this.is2DMode) {
        this.resetCamera();
        return;
      }

      if (this.is2DMode) {
        this.set2DMode(false);
      }

      this.activeCamera = this.perspectiveCamera;
      this.controls.object = this.perspectiveCamera;

      switch (angleKey) {
        case 'iso': // 3D Isometric 45° CAD angle (Full 3D Overview)
          this.perspectiveCamera.position.set(dist * 0.70, -dist * 0.75, dist * 0.75);
          this.perspectiveCamera.up.set(0, 0, 1);
          this.perspectiveCamera.lookAt(0, 0, 1.0);
          this.controls.target.set(0, 0, 1.0);
          break;

        case 'top': // 90° Top-Down Overhead View
          this.perspectiveCamera.position.set(0, -0.01, dist * 1.3);
          this.perspectiveCamera.up.set(0, 1, 0);
          this.perspectiveCamera.lookAt(0, 0, 0);
          this.controls.target.set(0, 0, 0);
          break;

        case 'front': // Front View (XZ plane cross-section: vertical metal & via stack)
          this.perspectiveCamera.position.set(0, -dist * 1.15, 2.5);
          this.perspectiveCamera.up.set(0, 0, 1);
          this.perspectiveCamera.lookAt(0, 0, 2.5);
          this.controls.target.set(0, 0, 2.5);
          break;

        case 'side': // Side View (YZ plane cross-section: vertical metal & via stack)
          this.perspectiveCamera.position.set(dist * 1.15, 0, 2.5);
          this.perspectiveCamera.up.set(0, 0, 1);
          this.perspectiveCamera.lookAt(0, 0, 2.5);
          this.controls.target.set(0, 0, 2.5);
          break;

        case 'macro': // High-magnification Transistor / Gate Macro Zoom
          this.perspectiveCamera.position.set(dist * 0.28, -dist * 0.32, dist * 0.22);
          this.perspectiveCamera.up.set(0, 0, 1);
          this.perspectiveCamera.lookAt(0, 0, 1.0);
          this.controls.target.set(0, 0, 1.0);
          break;

        default:
          this.perspectiveCamera.position.set(dist * 0.70, -dist * 0.75, dist * 0.75);
          this.perspectiveCamera.up.set(0, 0, 1);
          this.perspectiveCamera.lookAt(0, 0, 1.0);
          this.controls.target.set(0, 0, 1.0);
          break;
      }
      this._onWindowResize();
      this.controls.update();
    }

    /**
     * 2D CAD Top-Down / 3D Perspective Mode Toggle
     */
    set2DMode(enable2D) {
      this.is2DMode = enable2D;

      if (this.is2DMode) {
        // Switch to Orthographic Top-Down CAD View
        this.activeCamera = this.orthographicCamera;
        this.controls.object = this.orthographicCamera;
        this.controls.enableRotate = false; // CAD 2D pan/zoom only
        
        // Ensure camera is perfectly aligned straight down with Y pointing up
        this.orthographicCamera.position.set(0, 0, 500);
        this.orthographicCamera.up.set(0, 1, 0);
        this.orthographicCamera.lookAt(0, 0, 0);
        this.controls.target.set(0, 0, 0);

        // In 2D CAD mode, reduce specular glare so colors appear pure and unbleached like KLayout
        this.layerMeshes.forEach((mesh) => {
          if (mesh.material && !mesh.userData.isBoundary) {
            mesh.material.roughness = 0.95;
            mesh.material.metalness = 0.05;
            mesh.material.needsUpdate = true;
          }
        });
      } else {
        // Switch to 3D Perspective Orbiting Mode
        this.activeCamera = this.perspectiveCamera;
        this.controls.object = this.perspectiveCamera;
        this.controls.enableRotate = true; // Full 3D rotation
        this.perspectiveCamera.up.set(0, 0, 1);

        const bbox = (this.currentLayout && this.currentLayout.bbox) ? this.currentLayout.bbox : { width_um: 75, height_um: 75 };
        const maxDim = Math.max(bbox.width_um, bbox.height_um);
        const dist = maxDim * 1.5;

        // Default to classic 45° CAD isometric angle
        this.perspectiveCamera.position.set(dist * 0.70, -dist * 0.75, dist * 0.75);
        this.perspectiveCamera.lookAt(0, 0, 1.0);
        this.controls.target.set(0, 0, 1.0);

        // Restore 3D PBR satin metallic and roughness
        this.layerMeshes.forEach((mesh, layerNum) => {
          if (mesh.material && !mesh.userData.isBoundary) {
            const def = this._getLayerDef(layerNum);
            mesh.material.roughness = def.roughness !== undefined ? def.roughness : 0.65;
            mesh.material.metalness = def.metalness !== undefined ? def.metalness : 0.28;
            mesh.material.emissive = new THREE.Color(0x000000);
            mesh.material.emissiveIntensity = 0.0;
            mesh.material.needsUpdate = true;
          }
        });
      }

      this._onWindowResize();
      this.controls.update();
    }

    toggle2D3D() {
      this.set2DMode(!this.is2DMode);
      return this.is2DMode;
    }

    /**
     * Reset Camera to center and focus bounding box in 45° isometric view.
     */
    resetCamera() {
      const bbox = (this.currentLayout && this.currentLayout.bbox) ? this.currentLayout.bbox : { width_um: 75, height_um: 75 };
      const maxDim = Math.max(bbox.width_um, bbox.height_um);
      this.controls.target.set(0, 0, 0);

      if (this.is2DMode) {
        this.orthographicCamera.position.set(0, 0, 500);
        this.orthographicCamera.up.set(0, 1, 0);
        this.orthographicCamera.lookAt(0, 0, 0);
      } else {
        const dist = maxDim * 1.5;
        this.perspectiveCamera.position.set(dist * 0.70, -dist * 0.75, dist * 0.75);
        this.perspectiveCamera.up.set(0, 0, 1);
        this.perspectiveCamera.lookAt(0, 0, 1.0);
        this.controls.target.set(0, 0, 1.0);
      }

      this._onWindowResize();
      this.controls.update();
    }

    /**
     * Master Reset: Complete restoration of all visualizer and engine state
     */
    resetAll() {
      // 1. Reset 2D/3D mode back to 3D perspective and 45° isometric camera
      if (this.is2DMode) {
        this.set2DMode(false);
      }
      this.setCameraAngle('iso');

      // 2. Reset exploded view to default 1.0x (100% Real Physical Silicon Scale)
      const defaultExp = this.options.initialExplode || 1.0;
      this.setExplodedView(defaultExp);

      // 3. Turn on all layers and restore default stackup opacities
      this.showAllLayers();
      this.layerMeshes.forEach((mesh, layerNum) => {
        const def = this._getLayerDef(layerNum);
        if (def && def.opacity !== undefined) {
          this.setLayerOpacity(layerNum, def.opacity);
        }
        if (mesh.material && !mesh.userData.isBoundary) {
          mesh.material.roughness = def.roughness !== undefined ? def.roughness : 0.65;
          mesh.material.metalness = def.metalness !== undefined ? def.metalness : 0.28;
          mesh.material.emissive = new THREE.Color(0x000000);
          mesh.material.emissiveIntensity = 0.0;
          mesh.material.needsUpdate = true;
        }
      });

      // 4. Reset cross-section slicing
      this.setSlicingEnabled(false);
      if (this.currentLayout && this.currentLayout.bbox) {
        const margin = Math.max(this.currentLayout.bbox.width_um, this.currentLayout.bbox.height_um) * 0.8;
        this.clipPlaneX.constant = margin;
        this.clipPlaneY.constant = margin;
        this.clipPlaneZ.constant = 50.0;
      } else {
        this.clipPlaneX.constant = 1000;
        this.clipPlaneY.constant = 1000;
        this.clipPlaneZ.constant = 1000;
      }

      // 5. Clear measurement ruler
      this.setRulerActive(false);
      this.clearRuler();
    }

    /**
     * Cross-Section Slicing
     */
    setSlicingEnabled(enabled) {
      this.slicingEnabled = enabled;
      const planes = enabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : [];
      this.layerMeshes.forEach((mesh) => {
        mesh.material.clippingPlanes = planes;
        mesh.material.needsUpdate = true;
      });
      this.substrateGroup.traverse((child) => {
        if (child.material) {
          child.material.clippingPlanes = planes;
          child.material.needsUpdate = true;
        }
      });
    }

    setSliceX(normalizedVal) {
      if (!this.currentLayout) return;
      const w = this.currentLayout.bbox.width_um;
      this.clipPlaneX.constant = normalizedVal * (w / 2);
    }

    setSliceY(normalizedVal) {
      if (!this.currentLayout) return;
      const h = this.currentLayout.bbox.height_um;
      this.clipPlaneY.constant = normalizedVal * (h / 2);
    }

    setSliceZ(normalizedVal) {
      const maxZ = 8.0 * (this.explodeFactor || 1.0);
      this.clipPlaneZ.constant = normalizedVal * maxZ;
    }

    /**
     * Layer Visibility & Styling Controls
     */
    setLayerVisibility(layerNum, visible) {
      const mesh = this.layerMeshes.get(layerNum);
      if (mesh) mesh.visible = visible;
    }

    setLayerOpacity(layerNum, opacity) {
      const mesh = this.layerMeshes.get(layerNum);
      if (mesh) {
        mesh.material.opacity = opacity;
        mesh.material.transparent = opacity < 1.0;
        mesh.material.depthWrite = opacity >= 0.90;
      }
    }

    highlightLayer(layerNum, highlight) {
      const mesh = this.layerMeshes.get(layerNum);
      if (mesh && mesh.material) {
        if (highlight) {
          mesh.material.emissive = new THREE.Color(mesh.userData.color || 0x38bdf8);
          mesh.material.emissiveIntensity = 0.35;
        } else {
          mesh.material.emissive = new THREE.Color(0x000000);
          mesh.material.emissiveIntensity = 0.0;
        }
      }
    }

    soloLayer(layerNum) {
      this.layerMeshes.forEach((mesh, id) => {
        mesh.visible = (id === layerNum);
      });
    }

    showAllLayers() {
      this.layerMeshes.forEach((mesh) => {
        mesh.visible = true;
      });
    }

    hideAllLayers() {
      this.layerMeshes.forEach((mesh) => {
        mesh.visible = false;
      });
    }

    isolateMetalsOnly() {
      this.layerMeshes.forEach((mesh, id) => {
        const meta = this.layerMeta.get(id);
        const isMetal = (meta && meta.type === 'metal') ||
          (typeof id === 'string' && (id.startsWith('68/20') || id.startsWith('69/20') || id.startsWith('70/20') || id.startsWith('71/20') || id.startsWith('72/20'))) ||
          ([68, 69, 70, 71, 72].includes(Number(id)));
        mesh.visible = isMetal;
      });
    }

    isolateViasOnly() {
      this.layerMeshes.forEach((mesh, id) => {
        const meta = this.layerMeta.get(id);
        const isVia = (meta && meta.type === 'via') ||
          (typeof id === 'string' && (id.includes('/44') || id === '67/44' || id === '66/44'));
        mesh.visible = isVia;
      });
    }

    isolateFrontEndOnly() {
      this.layerMeshes.forEach((mesh, id) => {
        const meta = this.layerMeta.get(id);
        const isFE = (meta && (meta.type === 'frontend' || meta.type === 'subsurface' || meta.type === 'mol')) ||
          (typeof id === 'string' && (id.startsWith('64/') || id.startsWith('65/') || id.startsWith('66/20') || id.startsWith('67/20') || id.startsWith('78/') || id.startsWith('93/') || id.startsWith('94/'))) ||
          ([64, 65, 66, 67, 78, 81, 93, 94].includes(Number(id)));
        mesh.visible = isFE;
      });
    }

    /**
     * Measurement Ruler Tool
     */
    setRulerActive(active) {
      this.rulerActive = active;
      this.clearRuler();
      this.container.style.cursor = active ? 'crosshair' : 'default';
    }

    clearRuler() {
      this.rulerPoints = [];
      while (this.rulerGroup.children.length > 0) {
        const obj = this.rulerGroup.children[0];
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
        this.rulerGroup.remove(obj);
      }
      if (this.onRulerUpdate) this.onRulerUpdate(null);
    }

    _renderRulerMarker(pos, colorHex) {
      const sphereGeom = new THREE.SphereGeometry(0.75, 16, 16);
      const sphereMat = new THREE.MeshBasicMaterial({ color: colorHex });
      const sphere = new THREE.Mesh(sphereGeom, sphereMat);
      sphere.position.copy(pos);
      sphere.position.z += 0.5;
      this.rulerGroup.add(sphere);
    }

    _updateRulerPreview(currentPos) {
      const p0 = this.rulerPoints[0];
      const p1 = currentPos;

      const dx = p1.x - p0.x;
      const dy = p1.y - p0.y;
      const dist = Math.hypot(dx, dy);

      if (this.onRulerUpdate) {
        this.onRulerUpdate({
          p0: { x: p0.x, y: p0.y },
          p1: { x: p1.x, y: p1.y },
          dx: Math.abs(dx),
          dy: Math.abs(dy),
          dist: dist
        });
      }
    }

    _finalizeRulerLine() {
      const p0 = this.rulerPoints[0];
      const p1 = this.rulerPoints[1];

      const lineGeom = new THREE.BufferGeometry();
      const verts = new Float32Array([
        p0.x, p0.y, p0.z + 0.5,
        p1.x, p1.y, p1.z + 0.5
      ]);
      lineGeom.setAttribute('position', new THREE.BufferAttribute(verts, 3));
      const lineMat = new THREE.LineBasicMaterial({ color: 0x22d3ee, linewidth: 2 });
      const line = new THREE.Line(lineGeom, lineMat);
      this.rulerGroup.add(line);

      const dx = p1.x - p0.x;
      const dy = p1.y - p0.y;
      const dist = Math.hypot(dx, dy);

      if (this.onRulerUpdate) {
        this.onRulerUpdate({
          p0: { x: p0.x, y: p0.y },
          p1: { x: p1.x, y: p1.y },
          dx: Math.abs(dx),
          dy: Math.abs(dy),
          dist: dist,
          completed: true
        });
      }
    }

    /**
     * Snapshot Capture (PNG)
     */
    captureSnapshot(filename = 'silicon_layout_3d.png') {
      this.renderer.render(this.scene, this.activeCamera);
      const dataUrl = this.renderer.domElement.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    /**
     * 3D Model Export (.glb)
     */
    exportGLB(filename = 'silicon_layout.glb') {
      if (typeof THREE.GLTFExporter === 'undefined') {
        throw new Error('GLTFExporter library is not loaded');
      }

      const exporter = new THREE.GLTFExporter();
      const exportScene = new THREE.Scene();

      exportScene.add(this.layoutGroup.clone());
      exportScene.add(this.substrateGroup.clone());

      exporter.parse(
        exportScene,
        (gltf) => {
          const blob = new Blob([gltf], { type: 'model/gltf-binary' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        },
        { binary: true }
      );
    }

    /**
     * Clean up resources
     */
    clear() {
      this.clearRuler();

      this.layerMeshes.forEach((mesh) => {
        if (mesh.geometry) mesh.geometry.dispose();
        if (mesh.material) mesh.material.dispose();
        this.layoutGroup.remove(mesh);
      });
      this.layerMeshes.clear();
      this.layerMeta.clear();

      while (this.substrateGroup.children.length > 0) {
        const obj = this.substrateGroup.children[0];
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
        this.substrateGroup.remove(obj);
      }
    }

    dispose() {
      this.clear();
      window.removeEventListener('resize', this._onWindowResize.bind(this));
      if (this.renderer && this.renderer.domElement) {
        this.container.removeChild(this.renderer.domElement);
        this.renderer.dispose();
      }
    }
  }

  return SiliconViewer3D;
}));
