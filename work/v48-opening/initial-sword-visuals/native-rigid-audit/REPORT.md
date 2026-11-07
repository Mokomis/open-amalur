# Native rigid/rest transform evidence

Static cached-native pass only, executable SHA16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314. No original process launched or queried, database writes, assets/core edits, animation sampling or GPU tests.

## Exact answer

A rigid FAB part uses its current instance bone TQS, composed with actor world. It does not use an identity skin matrix or apply a separate inverse-bind in the rigid branch. The source rest hierarchy is one real native way to populate that bone array; an animation-enabled branch can replace it.

-00d196c0 reads each runtime FAB descriptor stride0x5c. It reads remap count+20, remap pointer+24 and52B entries, then37B at+2c containing boneID+34 and flags+50.
-00cae460 selects descriptor=fab+4c +assembly*0x5c. If(flags@50 &4)==0, copies boneTQS[boneID@34] (48B perbone) and composes with caller actorTQS. It emits the rigid scene-transform command without a remap/inverse-bind operand.
-00caf530/00ccc470 call that updater with actor+124 and bone array actor+34.
-00caf5f0 independently confirms descriptor+34 selection: valid index chooses actor+34 pointer+bone*48; -1/out-of-range falls back actor-only; then applies descriptor+2c scalar.
-Decompiler omits some ECX/hidden destination arguments, so exact command-member ABI is not newly claimed. The bone-array selector and branch are explicit in the retained bodies.

Source container branches match exactly: parts0..17 flag1/9 have bit4clear, nonnegative bones and no remaps; parts18..20 flag13 have bit4set, bone-1 and6/4/4remaps. Sword descriptor flag1/bone2 is rigid.

## Native rest-path certificate

-00cea2a0 allocates bone count from skeleton header+10 and calls00c9a9b0.
-00c9a9b0 loops all bone indices; obtains source local TQS through00c44f20, optionally applies actor scalar to root0, then reads signed parent indices from skeleton-relative pointer+1c. Valid parent composes parent global with local; invalid parent copies local.
-00c44f20 loads source48B transform Q@0,T@16,S@32 from skeleton-relative pointer+18.00adcd40 stores runtime T@0,Q@16,S@32,flags@44.
-00ac5770 is the native TQS composition. Its quaternion multiplication order corresponds to R(conjugate(qParent))*R(conjugate(qLocal)), consistent with parent*local matrix.
-00ac4b10 explicitly converts runtime T/Q/S to3x4. Its rotation entries are R(conjugate(rawQ)), not the older external importer's standard-Hamilton orientation.
-00c8ac80 initializes actor+184 uniform scale to1.0. Native data constants at013be4a0(float)=1,013be4b0(double)=1,013be4b8(double)=2; native near-unit scale epsilon01732204=.0010000000474974513. Container's54 source scale triples are exactly1, so scale-elision has no effect here.

Concrete source certificate in concrete-source-witnesses.json:
part0 uses bone51,parent0, sourceTRS atfile2788; parent0identity. Its rest matrix is:
[ .8496201650268453,-.40441297165699375,-.33851991879941856,56.01029968261719;
 -.0828050493123218,-.7362010779728738,.6716780730823562,52.72074890136719;
 -.5208540206975361,-.5426400818284645,-.658978726417681,91.9975357055664 ].
Part2 uses bone52,parent0 and exact translation(2.9279849529266357,2.3730838298797607,-.7578800916671753), identity rotation.
Part1 uses bone53,parent0 and exact translation(-98.13925170898438,-11.049633979797363,158.0728302001953).
These native rest equations agree algebraically with the already-staged candidates. No claim of bit-identical floating evaluation or original active animation is made.

## Remap decoder narrowed

The earlier generic FAB reader incorrectly labeled each52B remap entry as serialized skeleton Q/T. Native evidence now proves runtime TQS48+boneIndex:
T@0,Q@16,S@32,flagword@44,boneID@48.
The14 source remap quaternions become unit with maximum norm-squared error7.81e-8. Raw values and sourcebone IDs are in concrete-source-witnesses.json.
00cae460's bit4 branch composes each runtime global bone TQS with that source remap TQS, then00ac4b10 emits a3x4 palette entry. The asset's remap offsets behave as bind offsets; a complete active palette or bind-cancellation certificate was not produced in this bounded pass. No multibone candidate was silently added.

## Active-pose condition

00d0fe20 checks current motion-state entries; nonempty enabled state delegates00d01c20.00d01c20 takes animated branch only when state pointer exists,00c8e340 succeeds and state+48 bit4 is set; otherwise00c9a9b0 rest fallback.
Animated path00cf6370 ->00ce58c0 samples through native animation library0111d920/01116c80, then converts resulting TQS. It can therefore differ from source rest.

Smallest remaining input for original active geometry: which initial motion-tree state/flags and time the placed actor uses, plus decoding/sampling1789841. The rest candidate may be previewed explicitly as native rest-path, never presented as the actual closed opening pose without this input.

No staged geometry/profile/texture bytes were changed by this native audit.
