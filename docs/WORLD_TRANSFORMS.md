# Original world transforms and personal GLB previews (M1.18)

This project reads **only a copy of the owner's Riptide GP: Renegade XAPK**. The Python tools here do not embed game assets, coordinates, textures or meshes in the public repository.

## Working scene reconstruction

`tools/resolve_world_instances.py` traverses `VuTemplateAsset/Levels/<arena>` and expands each `#Prefab/... ` reference using the corresponding `VuTemplateAsset` definition. It combines 4×4 matrices along parent-child relationships and applies explicit `ChildEntities` instance overrides by child name. Original per-instance transforms are exported privately.

The current transform convention is a **testable hypothesis** rather than a confirmed game-engine contract:

- XY is horizontal and Z points upward
- Position, rotation and scale are applied as `T · Rz · Ry · Rx · S`
- Euler angles are interpreted in **degrees**
- Matrices are column-major and multiplied `world = parent · local`
- Missing position/rotation/scale values default to `(0,0,0)/(0,0,0)/(1,1,1)`

Basic mathematics (rotated parents, negative coordinates, nonuniform scale) and nested prefab overrides are covered by seven synthetic unit tests. True in-engine Euler order and pivot behavior still need validation from equal-camera screenshots of Renegade and editor.

## Coverage (real XAPK, private computations)

[Per-arena aggregate report](world-transform-coverage.json) was produced locally on the owner's original XAPK:

- 9 arena templates processed
- **14,487** static model references with composed world transforms
- **151** water entities located (no water meshes inferred or rendered)
- **34,103** prefab expansion occurrences, counting nested expansions
- **4,560** child-property overrides applied

Caveats: 28 overrides in FactoryA, two in MilitaryA, and two in SpaceportA still have no matching child name, so they are recorded as unresolved. Counts are renderable *references*, not unique model files or confirmed visible geometry. Most original effects (moving parts, lightmaps, particles, sky, water, animated models) remain unsupported.

## First full-size visual proof: CityB

`tools/export_world_glb.py` creates a GLB **locally and privately** from world transforms and the verified first-LOD portions of static models.

- CityB: **2,818** static references discovered
- **2,658** original static geometry instances exported into a **4,907,752-byte** GLB
- **87** distinct model asset payloads parsed for the preview; three distinct model variants rejected (unknown format)
- **160** instances omitted, mostly because they refer to those unsupported model variants
- **14** water entities found but not drawn

The GLB was successfully re-opened using a GLB scene parser (2,658 transform nodes). The screenshot is a **technical top-down sampling** of transformed model vertices, not game-quality artwork. Geometry and original coordinates are private, and the GLB was supplied only to the owner, **not committed to this repo**. It is untextured; v0.8 Android has a separate texture pipeline that has not yet been integrated into this exporter.

Some original static assets contain an additional data/LOD region after a valid first vertex+index stream, or a verified one-byte LZMA NUL pad. `visual_models.py` remains **strict by default**; its `preview_first_lod=True` mode permits only clearly bounded, finite first-LOD data for the private GLB preview. This does not mean the entire multi-LOD format is decoded.

### Reproduce on your own machine

Requires `numpy` and `trimesh` for the optional GLB exporter, plus Python 3.11+:

```bash
python tools/resolve_world_instances.py game.xapk --arena CityB --out CityB-private-world.json
python tools/export_world_glb.py game.xapk --arena CityB --output CityB-private-preview.glb
python -m unittest discover -s tests -p 'test_resolve_world_instances.py' -v
```

Never push `*-private-world.json`, `*.glb` exported from original game data, `*.xapk` or `*.apf` to this public repository.

## Next blocking tasks for the Android editor

1. **Port the typed scene graph and composition rules to the Android import pipeline** or generate the same private scene cache on device.
2. Render real prefab model instances by referencing each GPU geometry only once and batching/drawing efficiently; a naive 14k draw calls per frame would be too expensive.
3. Confirm transform conventions/pivot behavior against reference geometry and screenshots; handle 32 unresolved overrides.
4. Reconstruct original water surface geometry from `VuWaterSurfaceEntity` and `VuWaterRampEntity` definitions and use `VuWaterMapAsset`; never paint arbitrary blue planes.
5. Add animated objects, special material/lightmaps/cubemap/sky/environment effects and missing geometry to get closer to game fidelity.

**No new Android APK is claimed in this milestone.** The v0.8 APK continues to be the most recent physically tested preview.
