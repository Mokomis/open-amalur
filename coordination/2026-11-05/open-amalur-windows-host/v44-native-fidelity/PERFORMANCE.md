# Resolution scaling — measured on the tablet

| Scale | Size | FPS | GPU ms | Submission ms | Thermal |
|---|---|---:|---:|---:|---|
|100%|2520×1680|35.73|26.37|21.96|0→0|
|75%|1890×1260|46.57|17.79|19.67|2→2|
|50%|1260×840|53.02|13.89|18.03|2→2|

Short stationary samples, same scene/pose/features, varying thermal state; not sustained gameplay.

GPU-limited at full resolution; lower resolution exposes draw submission/driver overhead. Optimize draw/state/depth/shadow work before simulation threading.

The final installed build retains full resolution by default. Test overrides were restored.
