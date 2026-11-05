# Allmaps in the viewer

```js
const mod = await import('https://esm.sh/@allmaps/maplibre');
const layer = new mod.WarpedMapLayer();
map.addLayer(layer, 'places-circles');            // under the points
await layer.addGeoreferenceAnnotationByUrl(url);  // the annotation URL from editor.allmaps.org
layer.setOpacity(0.7);
```

An annotation is a small JSON document (`https://annotations.allmaps.org/maps/<id>`)
with the IIIF image service, the ground control points (`resource` pixel ↔
`geo` lon/lat) and the mask. The plugin fetches the image tiles it needs
from the holding library and warps them on the fly; nothing is downloaded
in advance. Discovery: `https://api.allmaps.org/maps?intersects=<lon>,<lat>&limit=200`.
Checked 2026-11-04.
