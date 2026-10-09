/**
 * Silicon3D: Interactive 3D GDSII Silicon Layout Visualizer
 * Client-Side Binary GDSII Parser & Hierarchy Flattener
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
    root.GdsParser = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  class GdsParser {
    constructor() {
      this.reset();
    }

    reset() {
      this.structures = new Map();
      this.referencedStructures = new Set();
      this.userUnit = 0.001;        // User units in db units
      this.dbUnitInMeters = 1e-9;   // Database unit in meters (e.g. 1e-9 = 1nm)
      this.scaleMicron = 0.001;     // Factor to convert db coordinates into micrometers (um)
      this.libName = '';
      this.headerVersion = 600;
    }

    /**
     * Decodes an 8-byte Excess-64 (IBM hexadecimal) floating point number.
     * Formula: (-1)^sign * (Mantissa / 2^56) * 16^(Exponent - 64)
     */
    static decodeExcess64Float(view, offset) {
      const b0 = view.getUint8(offset);
      const sign = (b0 & 0x80) ? -1 : 1;
      const exponent = (b0 & 0x7F) - 64;
      let mantissa = 0;
      for (let i = 1; i <= 7; i++) {
        mantissa += view.getUint8(offset + i) * Math.pow(256, -i);
      }
      if (mantissa === 0) return 0.0;
      return sign * mantissa * Math.pow(16, exponent);
    }

    /**
     * Parse binary GDSII ArrayBuffer or Uint8Array.
     */
    parse(buffer) {
      this.reset();
      const raw = buffer instanceof ArrayBuffer ? buffer : buffer.buffer;
      const byteOffset = buffer.byteOffset || 0;
      const byteLength = buffer.byteLength || raw.byteLength;
      const view = new DataView(raw, byteOffset, byteLength);

      let offset = 0;
      let curStruct = null;
      let curElem = null;

      while (offset < byteLength) {
        if (offset + 4 > byteLength) break;
        const recordLen = view.getUint16(offset);
        if (recordLen < 4) break; // Invalid record, terminate safely

        const recordType = view.getUint8(offset + 2);
        const dataType = view.getUint8(offset + 3);
        const dataOffset = offset + 4;
        const dataLen = recordLen - 4;

        switch (recordType) {
          case 0x00: // HEADER
            if (dataLen >= 2) this.headerVersion = view.getInt16(dataOffset);
            break;

          case 0x02: // LIBNAME
            this.libName = this._readAscii(view, dataOffset, dataLen);
            break;

          case 0x03: // UNITS
            if (dataLen >= 16) {
              this.userUnit = GdsParser.decodeExcess64Float(view, dataOffset);
              this.dbUnitInMeters = GdsParser.decodeExcess64Float(view, dataOffset + 8);
              this.scaleMicron = this.dbUnitInMeters * 1e6;
            }
            break;

          case 0x05: // BGNSTR
            // Structure begins
            break;

          case 0x06: // STRNAME
            {
              const name = this._readAscii(view, dataOffset, dataLen);
              curStruct = {
                name,
                boundaries: [],
                paths: [],
                srefs: [],
                arefs: []
              };
              this.structures.set(name, curStruct);
            }
            break;

          case 0x07: // ENDSTR
            curStruct = null;
            break;

          case 0x08: // BOUNDARY
            curElem = { type: 'BOUNDARY', layer: 0, datatype: 0, xy: [] };
            break;

          case 0x09: // PATH
            curElem = { type: 'PATH', layer: 0, datatype: 0, width: 0, pathtype: 0, xy: [] };
            break;

          case 0x0A: // SREF
            curElem = { type: 'SREF', sname: '', strans: 0, mag: 1.0, angle: 0.0, xy: [] };
            break;

          case 0x0B: // AREF
            curElem = { type: 'AREF', sname: '', strans: 0, mag: 1.0, angle: 0.0, cols: 1, rows: 1, xy: [] };
            break;

          case 0x0C: // TEXT
            curElem = { type: 'TEXT', layer: 0, texttype: 0, string: '', xy: [] };
            break;

          case 0x0D: // LAYER
            if (curElem && dataLen >= 2) {
              curElem.layer = view.getUint16(dataOffset);
            }
            break;

          case 0x0E: // DATATYPE
            if (curElem && dataLen >= 2) {
              curElem.datatype = view.getUint16(dataOffset);
            }
            break;

          case 0x0F: // WIDTH
            if (curElem && dataLen >= 4) {
              curElem.width = view.getInt32(dataOffset);
            }
            break;

          case 0x10: // XY coordinates
            if (curElem) {
              const numPoints = Math.floor(dataLen / 8);
              const pts = new Array(numPoints);
              for (let i = 0; i < numPoints; i++) {
                pts[i] = [
                  view.getInt32(dataOffset + i * 8),
                  view.getInt32(dataOffset + i * 8 + 4)
                ];
              }
              curElem.xy = pts;
            }
            break;

          case 0x11: // ENDEL (End of element)
            if (curStruct && curElem) {
              if (curElem.type === 'BOUNDARY') {
                curStruct.boundaries.push(curElem);
              } else if (curElem.type === 'PATH') {
                // Convert path ribbon to boundaries
                const ribbons = this._expandPathToBoundaries(curElem);
                for (let r = 0; r < ribbons.length; r++) {
                  curStruct.boundaries.push(ribbons[r]);
                }
              } else if (curElem.type === 'SREF') {
                curStruct.srefs.push(curElem);
              } else if (curElem.type === 'AREF') {
                curStruct.arefs.push(curElem);
              }
            }
            curElem = null;
            break;

          case 0x12: // SNAME
            if (curElem) {
              curElem.sname = this._readAscii(view, dataOffset, dataLen);
              this.referencedStructures.add(curElem.sname);
            }
            break;

          case 0x13: // COLROW
            if (curElem && curElem.type === 'AREF' && dataLen >= 4) {
              curElem.cols = view.getUint16(dataOffset);
              curElem.rows = view.getUint16(dataOffset + 2);
            }
            break;

          case 0x16: // TEXTTYPE
            if (curElem && dataLen >= 2) {
              curElem.texttype = view.getUint16(dataOffset);
            }
            break;

          case 0x19: // STRING
            if (curElem) {
              curElem.string = this._readAscii(view, dataOffset, dataLen);
            }
            break;

          case 0x1A: // STRANS
            if (curElem && dataLen >= 2) {
              curElem.strans = view.getUint16(dataOffset);
            }
            break;

          case 0x1B: // MAG
            if (curElem && dataLen >= 8) {
              curElem.mag = GdsParser.decodeExcess64Float(view, dataOffset);
            }
            break;

          case 0x1C: // ANGLE
            if (curElem && dataLen >= 8) {
              curElem.angle = GdsParser.decodeExcess64Float(view, dataOffset);
            }
            break;

          case 0x21: // PATHTYPE
            if (curElem && dataLen >= 2) {
              curElem.pathtype = view.getUint16(dataOffset);
            }
            break;

          case 0x2D: // BOX
            curElem = { type: 'BOUNDARY', layer: 0, datatype: 0, xy: [] };
            break;

          default:
            // Unhandled records skipped
            break;
        }

        offset += recordLen;
      }

      return this;
    }

    _readAscii(view, offset, len) {
      let str = '';
      for (let i = 0; i < len; i++) {
        const c = view.getUint8(offset + i);
        if (c === 0) break; // Null terminator
        str += String.fromCharCode(c);
      }
      return str.trim();
    }

    /**
     * Expands PATH lines with thickness into closed 2D polygon ribbons.
     */
    _expandPathToBoundaries(path) {
      const pts = path.xy;
      if (!pts || pts.length < 2) return [];

      let width = path.width;
      if (!width || width <= 0) {
        // Fallback default wire width: 50nm in database units
        width = Math.max(10, Math.round(0.05 / Math.max(1e-6, this.scaleMicron)));
      }
      const halfW = width / 2;
      const ribbons = [];

      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i];
        const p1 = pts[i + 1];
        const dx = p1[0] - p0[0];
        const dy = p1[1] - p0[1];
        const len = Math.hypot(dx, dy);
        if (len < 1e-4) continue;

        // Normal vector perpendicular to segment
        const nx = (-dy / len) * halfW;
        const ny = (dx / len) * halfW;

        // Cap extension for pathtype 2
        let extX = 0, extY = 0;
        if (path.pathtype === 2) {
          extX = (dx / len) * halfW;
          extY = (dy / len) * halfW;
        }

        const x0 = p0[0] - extX, y0 = p0[1] - extY;
        const x1 = p1[0] + extX, y1 = p1[1] + extY;

        const poly = [
          [Math.round(x0 + nx), Math.round(y0 + ny)],
          [Math.round(x1 + nx), Math.round(y1 + ny)],
          [Math.round(x1 - nx), Math.round(y1 - ny)],
          [Math.round(x0 - nx), Math.round(y0 - ny)]
        ];

        ribbons.push({
          type: 'BOUNDARY',
          layer: path.layer,
          datatype: path.datatype,
          xy: poly
        });
      }

      return ribbons;
    }

    /**
     * Determines candidate top cell of the GDSII file.
     */
    getTopStructure() {
      const allNames = Array.from(this.structures.keys());
      if (allNames.length === 0) return null;

      // Top cell is never instantiated by another cell via SREF/AREF
      const unreferenced = allNames.filter(name => !this.referencedStructures.has(name));
      if (unreferenced.length === 1) return unreferenced[0];
      if (unreferenced.length > 1) {
        // Prioritize by polygon and sub-instance volume
        unreferenced.sort((a, b) => {
          const sa = this.structures.get(a), sb = this.structures.get(b);
          const scoreA = sa.boundaries.length + sa.srefs.length * 10;
          const scoreB = sb.boundaries.length + sb.srefs.length * 10;
          return scoreB - scoreA;
        });
        return unreferenced[0];
      }

      // If circular or all referenced, pick structure with largest content
      allNames.sort((a, b) => {
        const sa = this.structures.get(a), sb = this.structures.get(b);
        return (sb.boundaries.length + sb.srefs.length) - (sa.boundaries.length + sa.srefs.length);
      });
      return allNames[0];
    }

    /**
     * Recursively flattens hierarchy into world coordinates and normalizes to physical microns.
     */
    flatten(topCellName) {
      const topName = topCellName || this.getTopStructure();
      if (!topName || !this.structures.has(topName)) {
        throw new Error('Top cell not found in GDSII database: ' + (topName || 'none'));
      }

      const flattenedPolygons = [];
      const MAX_DEPTH = 64;

      const traverse = (cellName, matrix, depth) => {
        if (depth > MAX_DEPTH) return;
        const cell = this.structures.get(cellName);
        if (!cell) return;

        // 1. Process boundaries
        for (let bIdx = 0; bIdx < cell.boundaries.length; bIdx++) {
          const b = cell.boundaries[bIdx];
          let pts = b.xy;
          if (!pts || pts.length < 3) continue;

          // Strip identical closing vertex if present
          if (pts.length > 3 && pts[0][0] === pts[pts.length - 1][0] && pts[0][1] === pts[pts.length - 1][1]) {
            pts = pts.slice(0, pts.length - 1);
          }
          if (pts.length < 3) continue;

          // Apply 2D affine transform matrix [a, b, c, d, tx, ty]
          const a = matrix[0], b_m = matrix[1], c = matrix[2], d = matrix[3], tx = matrix[4], ty = matrix[5];
          const transformed = new Array(pts.length);
          for (let p = 0; p < pts.length; p++) {
            const x = pts[p][0];
            const y = pts[p][1];
            transformed[p] = [
              a * x + c * y + tx,
              b_m * x + d * y + ty
            ];
          }

          flattenedPolygons.push({
            layer: b.layer,
            datatype: b.datatype,
            pts: transformed
          });
        }

        // 2. Process SREF (single instance)
        for (let sIdx = 0; sIdx < cell.srefs.length; sIdx++) {
          const ref = cell.srefs[sIdx];
          const childMatrix = this._composeTransform(matrix, ref.strans, ref.mag, ref.angle, ref.xy && ref.xy[0] ? ref.xy[0] : [0, 0]);
          traverse(ref.sname, childMatrix, depth + 1);
        }

        // 3. Process AREF (array of instances)
        for (let aIdx = 0; aIdx < cell.arefs.length; aIdx++) {
          const aref = cell.arefs[aIdx];
          if (!aref.xy || aref.xy.length < 3) continue;

          const p0 = aref.xy[0];
          const p1 = aref.xy[1];
          const p2 = aref.xy[2];
          const cols = Math.max(1, aref.cols || 1);
          const rows = Math.max(1, aref.rows || 1);
          const colStepX = (p1[0] - p0[0]) / cols;
          const colStepY = (p1[1] - p0[1]) / cols;
          const rowStepX = (p2[0] - p0[0]) / rows;
          const rowStepY = (p2[1] - p0[1]) / rows;

          for (let r = 0; r < rows; r++) {
            for (let col = 0; col < cols; col++) {
              const instX = p0[0] + col * colStepX + r * rowStepX;
              const instY = p0[1] + col * colStepY + r * rowStepY;
              const childMatrix = this._composeTransform(matrix, aref.strans, aref.mag, aref.angle, [instX, instY]);
              traverse(aref.sname, childMatrix, depth + 1);
            }
          }
        }
      };

      // Identity matrix: [1, 0, 0, 1, 0, 0]
      traverse(topName, [1, 0, 0, 1, 0, 0], 0);

      // Compute bounding box in database units
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (let i = 0; i < flattenedPolygons.length; i++) {
        const poly = flattenedPolygons[i].pts;
        for (let p = 0; p < poly.length; p++) {
          const x = poly[p][0];
          const y = poly[p][1];
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }

      if (minX === Infinity) {
        minX = 0; maxX = 1000; minY = 0; maxY = 1000;
      }

      const scale = this.scaleMicron;
      const widthUm = (maxX - minX) * scale;
      const heightUm = (maxY - minY) * scale;
      const areaUm2 = widthUm * heightUm;
      const centerDbX = (minX + maxX) / 2;
      const centerDbY = (minY + maxY) / 2;

      // Group polygons by layer and normalize coordinates centered at (0, 0) in microns
      const layersMap = new Map();
      for (let i = 0; i < flattenedPolygons.length; i++) {
        const poly = flattenedPolygons[i];
        const normPts = new Array(poly.pts.length);
        for (let p = 0; p < poly.pts.length; p++) {
          normPts[p] = [
            (poly.pts[p][0] - centerDbX) * scale,
            (poly.pts[p][1] - centerDbY) * scale
          ];
        }

        const lNum = poly.layer;
        if (!layersMap.has(lNum)) {
          layersMap.set(lNum, []);
        }
        layersMap.get(lNum).push({
          datatype: poly.datatype,
          pts: normPts
        });
      }

      // Convert map to sorted object
      const layersObj = {};
      const layerKeys = Array.from(layersMap.keys()).sort((a, b) => a - b);
      for (let k = 0; k < layerKeys.length; k++) {
        const lNum = layerKeys[k];
        layersObj[lNum] = layersMap.get(lNum);
      }

      return {
        topCell: topName,
        allCells: Array.from(this.structures.keys()),
        libName: this.libName,
        scaleMicron: this.scaleMicron,
        units: {
          userUnit: this.userUnit,
          dbUnitInMeters: this.dbUnitInMeters
        },
        bbox: {
          minX_um: minX * scale,
          maxX_um: maxX * scale,
          minY_um: minY * scale,
          maxY_um: maxY * scale,
          width_um: widthUm,
          height_um: heightUm,
          area_um2: areaUm2
        },
        totalPolygons: flattenedPolygons.length,
        layers: layersObj
      };
    }

    /**
     * Composes parent affine matrix with local instance transformation.
     */
    _composeTransform(matrix, strans, mag, angleDeg, origin) {
      const rad = ((angleDeg || 0.0) * Math.PI) / 180.0;
      const cos = Math.cos(rad);
      const sin = Math.sin(rad);
      const m = mag || 1.0;
      const mirrorX = (strans & 0x8000) !== 0; // Bit 15: reflection across X axis
      const my = mirrorX ? -1 : 1;

      // Local 2x2 matrix and translation
      const la = m * cos;
      const lb = m * sin;
      const lc = -m * my * sin;
      const ld = m * my * cos;
      const ltx = origin[0] || 0;
      const lty = origin[1] || 0;

      // Matrix multiply: [A][B]
      const pa = matrix[0], pb = matrix[1], pc = matrix[2], pd = matrix[3], ptx = matrix[4], pty = matrix[5];

      return [
        pa * la + pc * lb,
        pb * la + pd * lb,
        pa * lc + pc * ld,
        pb * lc + pd * ld,
        pa * ltx + pc * lty + ptx,
        pb * ltx + pd * lty + pty
      ];
    }
  }

  return GdsParser;
}));
