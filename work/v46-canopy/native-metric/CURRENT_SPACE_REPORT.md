# Current-space identity: native camera to renderer

## Resolved native path

The renderer does not compute currentSpace by taking the nearest tree, bound center or view depth. The active camera supplies an explicit identity.

1. SceneWin render writer00bd0d80 reads the gameplay Camera object from SceneWin+0x410. Its actual x86 ABI was checked against the existing native PE (not inferred solely from decompiler prototypes).
2.00c36070 copies Camera+0x38c, a compact asset reference.00c36090 likewise copies Camera+0x390 (the companion region reference).
3.00a6fe10 translates the first reference to an assetID. Writer00bd0d80 stores it in opcode6 payload+0x36c, independently of copied camera position/matrices.
4. Dispatcher00d42f40 selects renderCamera through backend+0x5f0 using payload.cameraHandle at+8 and writes renderCamera+0x360=payload+0x36c. The copied cameraData begins payload+0xc. Foliage agent preserved/ABI-checked this dispatcher.
5.00c97d40 makes context.currentSpace=renderCamera+0x360.00c3e3e0 and00ce93e0 use this exact ID for visibility/admission.

The gameplay Camera's space reference is populated from active camera implementation virtual+0x80 when installing/transitioning implementations (00d08970/00d2d500). Active TaskCameraImplementation inherits BaseCameraImplementation::vf32@00a24070; its actual x86 code adds0xc to ECX then tailcalls compact reference copy00a6c340. Thus BaseCameraImplementation+0xc carries that space identity. TaskCameraImplementation's task-object property getter00c46080 exposes the same reference under nameHash0x68164b. This chain has no point-containment query.

The full actor/location producer that assigns BaseCameraImplementation+0xc and changes actor space at a portal has not yet been followed end-to-end. Camera task coordinate getters/updates were inspected but did not provide a justified automatic point→space classifier. No nearest-space or arbitrary bounding-box fallback is proposed as native behavior.

## Runtime reference is independently known

Read-only preserved runtime evidence `work/v46-canopy/runtime/registered-collections.json` directly reports camera slot0 at0x25f1b5b0:

- spaceID431646.
- cull XYZ(8591.9326171875,-87036.03125,6493.06640625), exactly the original captured bridge eye.
- camera raw dump SHA7e7a5514a02548ad6c913346c7c771580f94a6bb421bc4327e5e466acf3e2320.
- static descriptor IDs0,431646,431650; source198's431642 collection is absent before per-draw culling.
- quality flag1, squared scale4.

The running executable was already paused at the verified bridge, and the runtime reader used PROCESS_VM_READ|PROCESS_QUERY_INFORMATION only. No input, process writes, debugger attach or new replay was used by this investigation.

Reference-camera metadata may therefore explicitly carry spaceID431646 with its exact VP/eye. This is a matched captured frame property, not an inferred arbitrary whitelist. A normal camera must retain the active gameplay scene/space identity; changing its eye alone does not reproduce native streaming state. The current host's source initial spawn431638 and its reference-camera override are distinct states, as the parent noted.

## Source graph and portal records

Existing Region loader00fcb620 calls00fc4a70 on sourceRegionRoot+0xc0. That loader retains arrays0xc0/0xc8 and instantiates each source0xd0 row as BHG_RegionLink:

- source row stride0x70=112B, source count atRoot+0xd4.
- runtime RegionLink stride0x74=116B, including a vtable and source-data pointer+0x70.
- RegionLink derives from Portal. Initialization00faf460 stores the source row pointer then calls00fa6f20 to derive portal frame/extents.
-00fa6f20 reads two source dimensions at row0/4, derives transformed axes from row+8, and sets runtime portal center/axes/extents. This establishes portal geometry, not a general enclosing room volume.
- RegionLink::vf4@00fb8d00 resolves a connected destination using source-data+0x68 or the indirect lookup from+0x6c. These fields can be translated/mutated at runtime; source IDs must be decoded with the asset-reference rules rather than treated as arbitrary pointers.

For Region431608, the parent's source audit found27 entries each at0xc0/0xc8 (164B records) and35 entries at0xd0 (112B), with source edges including431646→431650. The class/loader proof above confirms what0xd0 represents; it does not prove a point-in-volume algorithm.

SpaceGraph itself (00fe7510) owns arrays of nodes/deferred loads and a root space reference. SpaceGraphNode (00fea2c0) owns a Space ref and neighbor/reference arrays; the examined node constructors/destructors do not carry an enclosing geometric volume. This is consistent with persistent source identity and graph/portal transitions. Foliage agent owns the exact streaming/graph-registration route and current/neighbor admission data.

## Portable implementation boundary

Supported now: use exact source initial scene/space identity for normal startup; preserve it as state, propagate it to render/stream selection; carry exact431646 identity in the matched bridge reference profile; decode source portal graph rather than selecting spaces from foliage instances. The actual source/native portal-crossing update rule, tie-breaks and hysteresis still require the actor/location producer. A persistent-state portal implementation is a principled reconstruction direction, but is not labelled fully native until that producer is correlated. No new renderer/core/assets were edited here.
