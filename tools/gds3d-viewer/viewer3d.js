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

  // SkyWater 130nm Physical Metallization & Diffusion Stackup
  // Calibrated with PBR metallic, roughness, and subtle luminescence for crisp CAD rendering
  const SKY130_STACKUP = {
    64:  { name: 'nwell',       label: 'N-Well (L64)',            color: '#06b6d4', elevation: 0.00, thickness: 0.20, opacity: 0.22, metalness: 0.1, roughness: 0.85, emissive: '#0891b2', emissiveIntensity: 0.08 },
    65:  { name: 'diff',        label: 'Diffusion / Active (L65)',color: '#10b981', elevation: 0.20, thickness: 0.18, opacity: 0.85, metalness: 0.2, roughness: 0.45, emissive: '#059669', emissiveIntensity: 0.15 },
    66:  { name: 'poly',        label: 'Polysilicon Gate (L66)',  color: '#ef4444', elevation: 0.40, thickness: 0.20, opacity: 0.95, metalness: 0.3, roughness: 0.35, emissive: '#dc2626', emissiveIntensity: 0.20 },
    67:  { name: 'li1',         label: 'Local Interconnect (L67)',color: '#0284c7', elevation: 0.65, thickness: 0.18, opacity: 0.95, metalness: 0.6, roughness: 0.28, emissive: '#0284c7', emissiveIntensity: 0.20 },
    68:  { name: 'm1',          label: 'Metal 1 (L68)',           color: '#38bdf8', elevation: 0.95, thickness: 0.35, opacity: 1.00, metalness: 0.65, roughness: 0.22, emissive: '#0284c7', emissiveIntensity: 0.22 },
    69:  { name: 'm2',          label: 'Metal 2 (L69)',           color: '#f59e0b', elevation: 1.55, thickness: 0.35, opacity: 1.00, metalness: 0.65, roughness: 0.22, emissive: '#d97706', emissiveIntensity: 0.22 },
    70:  { name: 'm3',          label: 'Metal 3 (L70)',           color: '#34d399', elevation: 2.20, thickness: 0.80, opacity: 1.00, metalness: 0.65, roughness: 0.22, emissive: '#059669', emissiveIntensity: 0.22 },
    71:  { name: 'm4',          label: 'Metal 4 (L71)',           color: '#c084fc', elevation: 3.35, thickness: 0.80, opacity: 1.00, metalness: 0.65, roughness: 0.22, emissive: '#9333ea', emissiveIntensity: 0.22 },
    72:  { name: 'm5',          label: 'Metal 5 (L72)',           color: '#facc15', elevation: 4.50, thickness: 1.20, opacity: 1.00, metalness: 0.70, roughness: 0.18, emissive: '#ca8a04', emissiveIntensity: 0.25 },
    78:  { name: 'tap',         label: 'Substrate Tap (L78)',     color: '#ec4899', elevation: 0.20, thickness: 0.18, opacity: 0.80, metalness: 0.2, roughness: 0.50, emissive: '#db2777', emissiveIntensity: 0.15 },
    81:  { name: 'nsdm',        label: 'N+ Source/Drain (L81)',   color: '#a855f7', elevation: 0.10, thickness: 0.10, opacity: 0.35, metalness: 0.1, roughness: 0.70, emissive: '#7e22ce', emissiveIntensity: 0.10 },
    83:  { name: 'psdm',        label: 'P+ Source/Drain (L83)',   color: '#6366f1', elevation: 0.10, thickness: 0.10, opacity: 0.35, metalness: 0.1, roughness: 0.70, emissive: '#4f46e5', emissiveIntensity: 0.10 },
    93:  { name: 'hvi',         label: 'High Voltage Imp. (L93)', color: '#14b8a6', elevation: 0.05, thickness: 0.08, opacity: 0.30, metalness: 0.1, roughness: 0.70, emissive: '#0d9488', emissiveIntensity: 0.10 },
    94:  { name: 'licon',       label: 'LI Contact (L94)',        color: '#22d3ee', elevation: 0.60, thickness: 0.15, opacity: 0.95, metalness: 0.7, roughness: 0.25, emissive: '#06b6d4', emissiveIntensity: 0.25 },
    95:  { name: 'mcon',        label: 'M1 Contact (L95)',        color: '#60a5fa', elevation: 0.80, thickness: 0.15, opacity: 0.95, metalness: 0.7, roughness: 0.25, emissive: '#2563eb', emissiveIntensity: 0.25 },
    122: { name: 'pad',         label: 'Bonding Pad (L122)',      color: '#fb923c', elevation: 4.50, thickness: 1.20, opacity: 0.95, metalness: 0.75, roughness: 0.20, emissive: '#ea580c', emissiveIntensity: 0.25 },
    235: { name: 'prBoundary',  label: 'PR / Die Boundary (L235)',color: '#22d3ee', elevation: -0.02, thickness: 0.02, opacity: 0.60, metalness: 0.1, roughness: 0.90, isBoundary: true, emissive: '#06b6d4', emissiveIntensity: 0.30 },
    236: { name: 'fill',        label: 'Fill / Core Margin (L236)',color: '#64748b', elevation: 0.00, thickness: 0.05, opacity: 0.30, metalness: 0.2, roughness: 0.85, emissive: '#475569', emissiveIntensity: 0.10 }
  };

  class SiliconViewer3D {
    constructor(containerElement, options = {}) {
      this.container = containerElement;
      this.options = Object.assign({
        antialias: true,
        alpha: false,
        initialExplode: 2.5
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
      this.perspectiveCamera = new THREE.PerspectiveCamera(40, aspect, 0.1, 10000);
      this.perspectiveCamera.position.set(0, -110, 95);
      this.perspectiveCamera.up.set(0, 0, 1); // Z is vertical in 3D silicon stackup!

      const frustumSize = 150;
      this.orthographicCamera = new THREE.OrthographicCamera(
        (frustumSize * aspect) / -2,
        (frustumSize * aspect) / 2,
        frustumSize / 2,
        frustumSize / -2,
        0.1,
        10000
      );
      this.orthographicCamera.position.set(0, 0, 500);
      this.orthographicCamera.up.set(0, 1, 0); // Y is up in 2D top-down view
      this.orthographicCamera.lookAt(0, 0, 0);

      this.activeCamera = this.perspectiveCamera;

      // 3. Renderer
      this.renderer = new THREE.WebGLRenderer({
        antialias: this.options.antialias,
        alpha: this.options.alpha,
        preserveDrawingBuffer: true,
        powerPreference: 'high-performance'
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.localClippingEnabled = true;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.35;
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
     * Generates a soft-light studio environment so PBR metal layers have crisp specular reflections
     */
    _setupEnvironment() {
      if (typeof document === 'undefined' || !document.createElement) return;

      try {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        // Studio gradient background
        const grad = ctx.createLinearGradient(0, 0, 0, 256);
        grad.addColorStop(0.0, '#38bdf8'); // Sky cyan fill
        grad.addColorStop(0.3, '#1e293b'); // Mid horizon
        grad.addColorStop(0.7, '#0f172a'); // Dark ground
        grad.addColorStop(1.0, '#020617');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 512, 256);

        // Soft studio overhead softbox lights
        ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        ctx.beginPath();
        ctx.arc(256, 70, 60, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(186, 230, 253, 0.6)';
        ctx.beginPath();
        ctx.arc(100, 90, 45, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(254, 240, 138, 0.5)';
        ctx.beginPath();
        ctx.arc(420, 85, 40, 0, Math.PI * 2);
        ctx.fill();

        const envTexture = new THREE.CanvasTexture(canvas);
        envTexture.mapping = THREE.EquirectangularReflectionMapping;
        envTexture.encoding = THREE.sRGBEncoding;

        this.scene.environment = envTexture;
      } catch (err) {
        console.warn('Synthetic envMap skipped:', err);
      }
    }

    /**
     * 4-Point High-Fidelity Studio EDA Lighting
     */
    _setupLights() {
      // 1. Clean ambient illumination
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
      this.scene.add(ambientLight);

      // 2. Hemisphere Light: Sky (cool cyan) vs Ground (dark charcoal)
      const hemiLight = new THREE.HemisphereLight(0xe0f2fe, 0x090d16, 0.75);
      hemiLight.position.set(0, 0, 200);
      this.scene.add(hemiLight);

      // 3. Main Key Directional Light: Overhead isometric angle
      const keyLight = new THREE.DirectionalLight(0xffffff, 1.25);
      keyLight.position.set(120, -100, 180);
      this.scene.add(keyLight);

      // 4. Fill Light: Cool azure fill for dark shadow facets
      const fillLight = new THREE.DirectionalLight(0x7dd3fc, 0.85);
      fillLight.position.set(-140, 90, 140);
      this.scene.add(fillLight);

      // 5. Specular Rim Light: Sharp metallic highlights on interconnects
      const rimLight = new THREE.DirectionalLight(0xfef08a, 0.70);
      rimLight.position.set(0, 160, 100);
      this.scene.add(rimLight);

      // 6. Direct Top-Down Light for 2D CAD mode
      const topLight = new THREE.DirectionalLight(0xffffff, 0.65);
      topLight.position.set(0, 0, 300);
      this.scene.add(topLight);
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
      const layerNums = Object.keys(layers).map(Number).sort((a, b) => a - b);
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
      // Substrate wafer base plate
      const waferW = Math.max(width * 1.35, width + 25);
      const waferH = Math.max(height * 1.35, height + 25);
      const waferThickness = 2.5;

      const waferGeom = new THREE.BoxGeometry(waferW, waferH, waferThickness);
      const waferMat = new THREE.MeshStandardMaterial({
        color: 0x0c101a, // Silicon dark wafer
        metalness: 0.45,
        roughness: 0.65,
        clippingPlanes: this.slicingEnabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : []
      });
      const waferMesh = new THREE.Mesh(waferGeom, waferMat);
      waferMesh.position.set(0, 0, -waferThickness / 2 - 0.05);
      this.substrateGroup.add(waferMesh);

      // Chamfered die perimeter bevel frame
      const halfW = width / 2;
      const halfH = height / 2;
      const borderGeom = new THREE.BufferGeometry();
      const borderVerts = new Float32Array([
        -halfW, -halfH, 0.02,
         halfW, -halfH, 0.02,
         halfW,  halfH, 0.02,
        -halfW,  halfH, 0.02,
        -halfW, -halfH, 0.02
      ]);
      borderGeom.setAttribute('position', new THREE.BufferAttribute(borderVerts, 3));
      const borderMat = new THREE.LineBasicMaterial({
        color: 0x22d3ee,
        linewidth: 2,
        transparent: true,
        opacity: 0.95
      });
      const borderLine = new THREE.Line(borderGeom, borderMat);
      this.substrateGroup.add(borderLine);

      // Substrate gridlines
      const grid = new THREE.GridHelper(Math.max(waferW, waferH), 24, 0x1e293b, 0x0f172a);
      grid.rotation.x = Math.PI / 2;
      grid.position.z = -0.01;
      this.substrateGroup.add(grid);
    }

    _createLayerMesh(layerNum, polygons) {
      const def = SKY130_STACKUP[layerNum] || this._getDynamicLayerDef(layerNum);
      const { elevation, thickness, color, opacity, metalness, roughness, emissive, emissiveIntensity } = def;

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
        const pts = poly.pts;
        const n = pts.length;
        if (n < 3) continue;

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

      // Enhanced PBR Silicon Material with subtle luminescence
      const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        metalness: metalness !== undefined ? metalness : 0.45,
        roughness: roughness !== undefined ? roughness : 0.35,
        emissive: new THREE.Color(emissive || color),
        emissiveIntensity: emissiveIntensity !== undefined ? emissiveIntensity : 0.15,
        transparent: opacity < 1.0,
        opacity: opacity !== undefined ? opacity : 1.0,
        side: THREE.DoubleSide,
        depthWrite: opacity >= 0.90,
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
        baseEmissiveIntensity: emissiveIntensity || 0.15
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

    _getDynamicLayerDef(layerNum) {
      const hue = (layerNum * 137.5) % 360;
      const c = `hsl(${Math.round(hue)}, 80%, 60%)`;
      return {
        name: `layer_${layerNum}`,
        label: `Layer ${layerNum}`,
        color: c,
        elevation: (layerNum % 10) * 0.45,
        thickness: 0.20,
        opacity: 0.85,
        metalness: 0.5,
        roughness: 0.35,
        emissive: c,
        emissiveIntensity: 0.15
      };
    }

    /**
     * Interactive Exploded View: Z-axis scaling
     */
    setExplodedView(factor) {
      this.explodeFactor = Math.max(1.0, factor);
      this.layerMeshes.forEach((mesh) => {
        const baseZ = mesh.userData.baseElevation || 0;
        mesh.position.z = baseZ * (this.explodeFactor - 1.0);
      });
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
      } else {
        // Switch to 3D Perspective Orbiting Mode
        this.activeCamera = this.perspectiveCamera;
        this.controls.object = this.perspectiveCamera;
        this.controls.enableRotate = true; // Full 3D rotation
        this.perspectiveCamera.up.set(0, 0, 1);

        const bbox = (this.currentLayout && this.currentLayout.bbox) ? this.currentLayout.bbox : { width_um: 75, height_um: 75 };
        const maxDim = Math.max(bbox.width_um, bbox.height_um);
        const dist = maxDim * 1.5;

        this.perspectiveCamera.position.set(0, -dist * 0.95, dist * 0.85);
        this.perspectiveCamera.lookAt(0, 0, 0);
        this.controls.target.set(0, 0, 0);
      }

      this._onWindowResize();
      this.controls.update();
    }

    toggle2D3D() {
      this.set2DMode(!this.is2DMode);
      return this.is2DMode;
    }

    /**
     * Reset Camera to center and focus bounding box.
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
        this.perspectiveCamera.position.set(0, -dist * 0.95, dist * 0.85);
        this.perspectiveCamera.up.set(0, 0, 1);
        this.perspectiveCamera.lookAt(0, 0, 0);
      }

      this._onWindowResize();
      this.controls.update();
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
      const maxZ = 6.0 * (this.explodeFactor || 1.0);
      this.clipPlaneZ.constant = (1.0 - normalizedVal) * maxZ;
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
      if (mesh) {
        const base = mesh.userData.baseEmissiveIntensity || 0.15;
        mesh.material.emissiveIntensity = highlight ? 0.70 : base;
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
      const metalLayers = new Set([68, 69, 70, 71, 72, 94, 95, 122]);
      this.layerMeshes.forEach((mesh, id) => {
        mesh.visible = metalLayers.has(id);
      });
    }

    isolateFrontEndOnly() {
      const feLayers = new Set([64, 65, 66, 67, 78, 81, 83, 93]);
      this.layerMeshes.forEach((mesh, id) => {
        mesh.visible = feLayers.has(id);
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
