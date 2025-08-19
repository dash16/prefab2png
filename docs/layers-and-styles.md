# Layers & Styles

## Current Layers
- streets
- player_starts
- biome_pine_forest
- biome_burnt_forest
- biome_desert
- biome_snow
- biome_wasteland

Layers are separated further into points, which show a tier-colored dot centered on the POI, and labels, which draw a line from a text label with the Display Name to the POI dot.

## Exclusion Rules (Labels only)
- Ignore names containing `bridge`, `wilderness_filler`, `rwg_tile_`, etc.  These prefabs are unnamed and don't need to be parsed in the label pass.
- Special allowlist for `sign_260*`, `sign_73*` to ensure they are included in the streets layer.

## 🎨 POI Tier Colors

The following hex colors are defined in `parse.py` → `load_tiers()` and are used for both POI dots and label text in map rendering.

<table>
  <thead>
    <tr><th>Tier</th><th>Hex</th><th>Swatch</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>0</td><td><code>#99896B</code></td>
      <td><svg width="20" height="20"><rect width="20" height="20" fill="#99896B" stroke="#000" stroke-width="1"/></svg></td>
    </tr>
    <tr>
      <td>1</td><td><code>#C4833D</code></td>
      <td><svg width="20" height="20"><rect width="20" height="20" fill="#C4833D" stroke="#000" stroke-width="1"/></svg></td>
    </tr>
    <tr>
      <td>2</td><td><code>#A2A43A</code></td>
      <td><svg width="20" height="20"><rect width="20" height="20" fill="#A2A43A" stroke="#000" stroke-width="1"/></svg></td>
    </tr>
    <tr>
      <td>3</td><td><code>#69BF4B</code></td>
      <td><svg width="20" height="20"><rect width="20" height="20" fill="#69BF4B" stroke="#000" stroke-width="1"/></svg></td>
    </tr>
    <tr>
      <td>4</td><td><code>#3C5CC7</code></td>
      <td><svg width="20" height="20"><rect width="20" height="20" fill="#3C5CC7" stroke="#000" stroke-width="1"/></svg></td>
    </tr>
    <tr>
      <td>5</td><td><code>#9734C5</code></td>
      <td><svg width="20" height="20"><rect width="20" height="20" fill="#9734C5" stroke="#000" stroke-width="1"/></svg></td>
    </tr>
  </tbody>
</table>

**Defined in:** `parse.py` → `load_tiers()`  
**Used by:** Rendering logic in `render.py` (`tier_colors` argument in `render_category_layer()`)

## Legend
- Intended to be used as a fallback when a label cannot be directly drawn on the map due to insufficient space to draw the full display name.  Can be forced on by using `--numbered-dots` to force all POI dots to draw as a number instead, which maps to a legend entry.