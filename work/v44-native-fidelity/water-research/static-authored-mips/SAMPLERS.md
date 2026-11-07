# Captured static sampler state

Native-only texture IDs658,659,660,666,667,668,669,676 all use native sampler149, identically across552 actual fragment-shader sample/draw uses. The shader OpSampledImage operands were resolved back to image and sampler descriptor bindings, then matched to the live descriptor state at each draw.

|Property|Native value|GLES equivalent|
|---|---|---|
|minification|LINEAR + LINEAR mipmap|GL_LINEAR_MIPMAP_LINEAR|
|magnification|LINEAR|GL_LINEAR|
|address U/V/W|REPEAT|GL_REPEAT|
|anisotropy|disabled; max0 field ignored|MAX_ANISOTROPY1|
|mip LOD bias|0|default0|
|min LOD|0|default0|
|max LOD|1000|retain image MAX_LEVEL=authoredCount−1|

No exceptions were found for these eight images. Other source-only new maps lack captured native sampler proof. No source or asset edits were made. Detailed draw, pipeline, image/sampler binding, view, sampler and state evidence is in captured-sampler-contracts.json.
