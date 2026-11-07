# Independent canopy ownership review

The isolated175-cell candidate passes independent byte/provenance validation. It contains51,831triangles,96,829vertices and400drawranges (maximum9percell), materialcount301. All old76-byte vertex data and everyu32index remain byteexact in their original order. Material IDs are unchanged and rangecoverage is complete/contiguous: nozero-length runs, gaps or overlaps.

Every one of51,831global source triangles occurs exactlyonce across the175cells. This also verifies exactcoverage for all590sourceparts, rather than only trusting per-part totals. Each source's84-byte record is found in its claimed original SPACEfile. TriangleUV0/RGBA/nativeMID matches the independent source soup exactly; position differences including only the5 previously proved TRScorrections are at most.007637cm. Candidate-to-current geometry itself is byteexact.

Each new48-byte run uses flag0x40000000 and a nonzero native SPACEassetID. Sphere0,min0,maxFLT_MAX and distanceScale1 preserve prior selection without introducing a guessed distanceLOD. Every material ID is below301. This fits the existing OARGEO1/76/48 parser and dynamicrange limit.

The33 native SPACE-positive VS877 draws were crosschecked separately using captured pose/FAB and raw-source audit:32maptoWest431646 and1toTransition431650. Every expanded matching sourceowner carries the sameSpaceID, and thoseIDs are present in the newranges. The other18VS877 draws belong to the separately recovered Region stream and are not falsely treated as SPACEpositives.

No actionable staging bug found. This validates ownership metadata and preservation; it does not validate the pending sourceportal traversal/activeSpace selector. Dense mode must bypass this new flag and thereby retain identical geometry/material selection. Root owns actualselector integration/promotion and image tests. ExistingRegion/shadow/waterfall assets were not changed by this review.
