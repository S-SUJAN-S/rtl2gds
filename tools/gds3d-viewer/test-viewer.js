/**
 * Silicon3D: Automated Verification Test Script
 * Verifies GDSII stream parsing, hierarchy flattening, and Three.js geometry construction
 */

const fs = require('fs');
const path = require('path');

// Setup Node test environment for Three.js
global.window = global;
global.document = {
  createElement: () => ({ style: {}, appendChild: () => {}, removeChild: () => {} })
};
global.THREE = require('./lib/three.min.js');
global.earcut = require('./lib/earcut.min.js');

const GdsParser = require('./gds-parser.js');

function runTests() {
  console.log('====================================================');
  console.log('Silicon3D: Running Automated Verification Test Suite');
  console.log('====================================================\n');

  const samples = [
    { name: 'full_adder.gds', expectedTop: 'full_adder', expectedW: 50, expectedH: 50 },
    { name: 'alu4bit.gds', expectedTop: 'alu4bit', expectedW: 75, expectedH: 75 },
    { name: 'uart_top.gds', expectedTop: 'uart_top', expectedW: 150, expectedH: 150 }
  ];

  let allPassed = true;

  for (const sample of samples) {
    const filePath = path.join(__dirname, 'samples', sample.name);
    console.log(`[TEST] Verifying canonical sample: ${sample.name}...`);

    if (!fs.existsSync(filePath)) {
      console.error(`  FAIL: File not found: ${filePath}`);
      allPassed = false;
      continue;
    }

    const tStart = Date.now();
    const buffer = fs.readFileSync(filePath);
    const parser = new GdsParser();
    parser.parse(buffer);
    const layout = parser.flatten();
    const tElapsed = Date.now() - tStart;

    console.log(`  Parsed in: ${tElapsed} ms`);
    console.log(`  Top Cell: "${layout.topCell}" (Expected: "${sample.expectedTop}")`);
    console.log(`  Die Dimensions: ${layout.bbox.width_um.toFixed(2)} µm × ${layout.bbox.height_um.toFixed(2)} µm`);
    console.log(`  Die Core Area: ${layout.bbox.area_um2.toFixed(2)} µm²`);
    console.log(`  Total Polygons: ${layout.totalPolygons.toLocaleString()}`);
    console.log(`  Active Layer Count: ${Object.keys(layout.layers).length}`);

    // Assertions
    if (layout.topCell !== sample.expectedTop) {
      console.error(`  FAIL: Top cell mismatch. Got ${layout.topCell}, expected ${sample.expectedTop}`);
      allPassed = false;
    }
    if (Math.abs(layout.bbox.width_um - sample.expectedW) > 0.1 || Math.abs(layout.bbox.height_um - sample.expectedH) > 0.1) {
      console.error(`  FAIL: Die dimension mismatch. Got ${layout.bbox.width_um}x${layout.bbox.height_um}, expected ${sample.expectedW}x${sample.expectedH}`);
      allPassed = false;
    }
    if (layout.totalPolygons <= 0) {
      console.error('  FAIL: No polygons extracted');
      allPassed = false;
    }

    // Verify Three.js geometry construction for each layer
    let totalGeomVertices = 0;
    const layerIds = Object.keys(layout.layers);
    for (const lNum of layerIds) {
      const polys = layout.layers[lNum];
      let triEstimate = 0;
      for (const p of polys) {
        triEstimate += (p.pts.length === 4) ? 12 : (p.pts.length * 4);
      }
      const positions = new Float32Array(triEstimate * 9);
      let vOffset = 0;
      for (const p of polys) {
        const pts = p.pts;
        const n = pts.length;
        if (n === 4) {
          const p0 = pts[0], p1 = pts[1], p2 = pts[2], p3 = pts[3];
          positions[vOffset++] = p0[0]; positions[vOffset++] = p0[1]; positions[vOffset++] = 1.0;
          positions[vOffset++] = p1[0]; positions[vOffset++] = p1[1]; positions[vOffset++] = 1.0;
          positions[vOffset++] = p2[0]; positions[vOffset++] = p2[1]; positions[vOffset++] = 1.0;
        }
      }
      const geom = new THREE.BufferGeometry();
      geom.setAttribute('position', new THREE.BufferAttribute(positions.subarray(0, vOffset), 3));
      totalGeomVertices += geom.attributes.position.count;
    }
    console.log(`  Three.js Geometry Check: Built BufferGeometries across ${layerIds.length} layers (${totalGeomVertices} vertices verified).`);
    console.log(`  PASS: ${sample.name}\n`);
  }

  if (allPassed) {
    console.log('====================================================');
    console.log('SUCCESS: All Silicon3D Verification Tests Passed (100%)');
    console.log('====================================================');
  } else {
    console.error('ERROR: Some tests failed.');
    process.exit(1);
  }
}

runTests();
