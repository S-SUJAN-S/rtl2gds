/**
 * Silicon3D: Interactive 3D GDSII Silicon Layout Visualizer
 * Three.js 3D Silicon Extrusion, Exploded View, & CAD Rendering Engine
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
  const SKY130_STACKUP = {
    64:  { name: 'nwell',       label: 'N-Well',                  color: '#06b6d4', elevation: 0.00, thickness: 0.20, opacity: 0.35, metalness: 0.0, roughness: 0.85 },
    65:  { name: 'diff',        label: 'Diffusion / Active',       color: '#10b981', elevation: 0.20, thickness: 0.15, opacity: 0.85, metalness: 0.1, roughness: 0.60 },
    66:  { name: 'poly',        label: 'Polysilicon Gate',        color: '#ef4444', elevation: 0.35, thickness: 0.18, opacity: 0.90, metalness: 0.2, roughness: 0.50 },
    67:  { name: 'li1',         label: 'Local Interconnect (li1)',color: '#0284c7', elevation: 0.55, thickness: 0.15, opacity: 0.95, metalness: 0.85, roughness: 0.30 },
    68:  { name: 'm1',          label: 'Metal 1 (m1)',            color: '#3b82f6', elevation: 0.85, thickness: 0.35, opacity: 1.00, metalness: 0.90, roughness: 0.20 },
    69:  { name: 'm2',          label: 'Metal 2 (m2)',            color: '#f59e0b', elevation: 1.45, thickness: 0.35, opacity: 1.00, metalness: 0.90, roughness: 0.20 },
    70:  { name: 'm3',          label: 'Metal 3 (m3)',            color: '#059669', elevation: 2.10, thickness: 0.80, opacity: 1.00, metalness: 0.90, roughness: 0.20 },
    71:  { name: 'm4',          label: 'Metal 4 (m4)',            color: '#8b5cf6', elevation: 3.20, thickness: 0.80, opacity: 1.00, metalness: 0.90, roughness: 0.20 },
    72:  { name: 'm5',          label: 'Metal 5 (m5)',            color: '#eab308', elevation: 4.30, thickness: 1.20, opacity: 1.00, metalness: 0.95, roughness: 0.15 },
    78:  { name: 'tap',         label: 'Substrate Tap',           color: '#ec4899', elevation: 0.20, thickness: 0.15, opacity: 0.70, metalness: 0.0, roughness: 0.60 },
    81:  { name: 'nsdm',        label: 'N+ Source/Drain',         color: '#a855f7', elevation: 0.10, thickness: 0.10, opacity: 0.40, metalness: 0.0, roughness: 0.70 },
    83:  { name: 'psdm',        label: 'P+ Source/Drain',         color: '#6366f1', elevation: 0.10, thickness: 0.10, opacity: 0.40, metalness: 0.0, roughness: 0.70 },
    93:  { name: 'hvi',         label: 'High Voltage Imp.',       color: '#14b8a6', elevation: 0.05, thickness: 0.08, opacity: 0.30, metalness: 0.0, roughness: 0.70 },
    94:  { name: 'licon',       label: 'LI Contact (licon)',      color: '#00d2d3', elevation: 0.50, thickness: 0.12, opacity: 0.90, metalness: 0.8, roughness: 0.35 },
    95:  { name: 'mcon',        label: 'M1 Contact (mcon)',       color: '#38bdf8', elevation: 0.70, thickness: 0.15, opacity: 0.90, metalness: 0.8, roughness: 0.35 },
    122: { name: 'pad',         label: 'Bonding Pad',             color: '#f97316', elevation: 4.30, thickness: 1.20, opacity: 0.90, metalness: 0.90, roughness: 0.20 },
    235: { name: 'prBoundary',  label: 'PR / Die Boundary',       color: '#22d3ee', elevation: -0.02, thickness: 0.02, opacity: 0.50, metalness: 0.0, roughness: 0.90, isBoundary: true },
    236: { name: 'fill',        label: 'Fill / Core Margin',      color: '#64748b', elevation: 0.00, thickness: 0.05, opacity: 0.25, metalness: 0.0, roughness: 0.90 }
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
      this.scene.background = new THREE.Color(0x0a0d14); // Deep cyber dark
      this.scene.fog = new THREE.FogExp2(0x0a0d14, 0.0008);

      // 2. Cameras
      const aspect = width / height;
      this.perspectiveCamera = new THREE.PerspectiveCamera(45, aspect, 0.1, 10000);
      this.perspectiveCamera.position.set(0, -120, 100);

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
      this.renderer.toneMappingExposure = 1.15;
      this.container.appendChild(this.renderer.domElement);

      // 4. OrbitControls
      this.controls = new THREE.OrbitControls(this.activeCamera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.screenSpacePanning = true;
      this.controls.maxDistance = 3000;
      this.controls.minDistance = 2;

      // 5. Container groups
      this.layoutGroup = new THREE.Group();
      this.substrateGroup = new THREE.Group();
      this.rulerGroup = new THREE.Group();

      this.scene.add(this.substrateGroup);
      this.scene.add(this.layoutGroup);
      this.scene.add(this.rulerGroup);

      // Raycaster for cursor telemetry and measurement ruler
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();
    }

    _setupLights() {
      // Balanced EDA ambient illumination
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
      this.scene.add(ambientLight);

      // Key light for crisp metallic wire highlights
      const keyLight = new THREE.DirectionalLight(0xffffff, 0.85);
      keyLight.position.set(150, 100, 250);
      this.scene.add(keyLight);

      // Fill light for soft shadow filling
      const fillLight = new THREE.DirectionalLight(0x60a5fa, 0.45);
      fillLight.position.set(-150, -120, 150);
      this.scene.add(fillLight);

      // Rim light for edge bevel and silicon layering
      const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.35);
      rimLight.position.set(0, 200, -50);
      this.scene.add(rimLight);
    }

    _setupClipping() {
      // Slicing planes in world coordinate space
      this.clipPlaneX = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 1000);
      this.clipPlaneY = new THREE.Plane(new THREE.Vector3(0, -1, 0), 1000);
      this.clipPlaneZ = new THREE.Plane(new THREE.Vector3(0, 0, -1), 1000);
    }

    _setupEvents() {
      window.addEventListener('resize', this._onWindowResize.bind(this));

      // Pointer tracking for HUD cursor coords and ruler
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
        Math.max(this.currentLayout.bbox.width_um, this.currentLayout.bbox.height_um) * 1.5 : 150;
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
        this._renderRulerMarker(pt, 0x00ffff);
      } else if (this.rulerPoints.length === 1) {
        this.rulerPoints.push(pt.clone());
        this._renderRulerMarker(pt, 0xff007f);
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

      // 3. Set camera to frame the chip nicely
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
      const waferW = Math.max(width * 1.35, width + 20);
      const waferH = Math.max(height * 1.35, height + 20);
      const waferThickness = 2.0;

      const waferGeom = new THREE.BoxGeometry(waferW, waferH, waferThickness);
      const waferMat = new THREE.MeshStandardMaterial({
        color: 0x111622,
        metalness: 0.3,
        roughness: 0.85,
        clippingPlanes: this.slicingEnabled ? [this.clipPlaneX, this.clipPlaneY, this.clipPlaneZ] : []
      });
      const waferMesh = new THREE.Mesh(waferGeom, waferMat);
      waferMesh.position.set(0, 0, -waferThickness / 2 - 0.05);
      this.substrateGroup.add(waferMesh);

      // Glowing die boundary frame
      const borderGeom = new THREE.BufferGeometry();
      const halfW = width / 2;
      const halfH = height / 2;
      const borderVerts = new Float32Array([
        -halfW, -halfH, 0.01,
         halfW, -halfH, 0.01,
         halfW,  halfH, 0.01,
        -halfW,  halfH, 0.01,
        -halfW, -halfH, 0.01
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

      // Substrate grid gridlines
      const grid = new THREE.GridHelper(Math.max(waferW, waferH), 20, 0x1e293b, 0x0f172a);
      grid.rotation.x = Math.PI / 2;
      grid.position.z = -0.01;
      this.substrateGroup.add(grid);
    }

    _createLayerMesh(layerNum, polygons) {
      const def = SKY130_STACKUP[layerNum] || this._getDynamicLayerDef(layerNum);
      const { elevation, thickness, color, opacity, metalness, roughness } = def;

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

          // 1. Top Face (2 triangles: p0,p1,p2 and p0,p2,p3)
          this._addTriangle(positions, normals, vOffset, p0[0], p0[1], z1, p1[0], p1[1], z1, p2[0], p2[1], z1, 0, 0, 1);
          vOffset += 9;
          this._addTriangle(positions, normals, vOffset, p0[0], p0[1], z1, p2[0], p2[1], z1, p3[0], p3[1], z1, 0, 0, 1);
          vOffset += 9;

          // 2. Bottom Face (2 triangles: p0,p2,p1 and p0,p3,p2)
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
            // Simple fan fallback
            indices = [];
            for (let i = 1; i < n - 1; i++) indices.push(0, i, i + 1);
          }

          if (indices && indices.length >= 3) {
            // Top and Bottom caps
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

      // Silicon PBR material
      const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        metalness: metalness !== undefined ? metalness : 0.5,
        roughness: roughness !== undefined ? roughness : 0.4,
        transparent: opacity < 1.0,
        opacity: opacity !== undefined ? opacity : 1.0,
        side: THREE.DoubleSide,
        depthWrite: opacity >= 0.95,
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
        polyCount: polygons.length
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
      // Normal vector pointing outwards from wall
      const dx = x1 - x0;
      const dy = y1 - y0;
      const len = Math.hypot(dx, dy) || 1e-5;
      const nx = dy / len;
      const ny = -dx / len;

      // Triangle 1: (p0,z0), (p1,z0), (p1,z1)
      this._addTriangle(pos, norm, offset, x0, y0, z0, x1, y1, z0, x1, y1, z1, nx, ny, 0);
      // Triangle 2: (p0,z0), (p1,z1), (p0,z1)
      this._addTriangle(pos, norm, offset + 9, x0, y0, z0, x1, y1, z1, x0, y0, z1, nx, ny, 0);
    }

    _getDynamicLayerDef(layerNum) {
      const hue = (layerNum * 137.5) % 360;
      return {
        name: `layer_${layerNum}`,
        label: `Layer ${layerNum}`,
        color: `hsl(${Math.round(hue)}, 75%, 55%)`,
        elevation: (layerNum % 10) * 0.45,
        thickness: 0.20,
        opacity: 0.85,
        metalness: 0.5,
        roughness: 0.5
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
     * 2D / 3D Mode Toggle
     */
    set2DMode(enable2D) {
      this.is2DMode = enable2D;
      const targetPos = this.controls.target.clone();

      if (this.is2DMode) {
        this.activeCamera = this.orthographicCamera;
        this.controls.object = this.orthographicCamera;
        this.controls.enableRotate = false;
        this.orthographicCamera.position.set(targetPos.x, targetPos.y, 500);
        this.orthographicCamera.lookAt(targetPos);
      } else {
        this.activeCamera = this.perspectiveCamera;
        this.controls.object = this.perspectiveCamera;
        this.controls.enableRotate = true;
        this.perspectiveCamera.position.set(targetPos.x, targetPos.y - 120, targetPos.z + 100);
        this.perspectiveCamera.lookAt(targetPos);
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

      const dist = maxDim * 1.6;
      this.perspectiveCamera.position.set(0, -dist * 0.95, dist * 0.85);
      this.perspectiveCamera.lookAt(0, 0, 0);

      this.orthographicCamera.position.set(0, 0, 500);
      this.orthographicCamera.lookAt(0, 0, 0);

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
      // normalizedVal between -1 and 1
      this.clipPlaneX.constant = (normalizedVal) * (w / 2);
    }

    setSliceY(normalizedVal) {
      if (!this.currentLayout) return;
      const h = this.currentLayout.bbox.height_um;
      this.clipPlaneY.constant = (normalizedVal) * (h / 2);
    }

    setSliceZ(normalizedVal) {
      // Slices top-down through max metal height
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
        mesh.material.depthWrite = opacity >= 0.95;
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
      const sphereGeom = new THREE.SphereGeometry(0.8, 16, 16);
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
      const lineMat = new THREE.LineBasicMaterial({ color: 0x00ffff, linewidth: 2 });
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

      // Clone visual elements
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

      // Dispose layer meshes
      this.layerMeshes.forEach((mesh) => {
        if (mesh.geometry) mesh.geometry.dispose();
        if (mesh.material) mesh.material.dispose();
        this.layoutGroup.remove(mesh);
      });
      this.layerMeshes.clear();
      this.layerMeta.clear();

      // Dispose substrate
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
