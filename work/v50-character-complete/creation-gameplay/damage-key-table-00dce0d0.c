// 00dce0d0 FUN_00dce0d0

void __thiscall FUN_00dce0d0(int param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  float fVar3;
  float fVar4;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined1 local_18 [8];
  undefined **local_10;
  int local_c;
  
  local_10 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(param_2,0x14);
  local_10 = BHG::BuffPartIndex::vftable;
  if ((local_c != 0) && ((*(byte *)(local_c + 0x20) & 1) != 0)) {
    FUN_00e2cbd0();
    FUN_00e2c9e0(0);
    iVar1 = *(int *)(DAT_019fe9c4 + 0xca34);
    iVar2 = 0;
    if (0 < iVar1) {
      do {
        fVar4 = DAT_013be4a0;
        if ((iVar2 != 0xc) &&
           (fVar4 = *(float *)(param_1 + 0x15c), *(float *)(param_1 + 0x15c) < 0.0)) {
          fVar4 = 0.0;
        }
        fVar3 = *(float *)(param_1 + iVar2 * 8);
        if (fVar3 < 0.0) {
          fVar3 = 0.0;
        }
        FUN_00e2ca80(fVar3 * fVar4);
        local_30 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca38) + iVar2 * 4);
        local_2c = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca48) + iVar2 * 4);
        FUN_00f682e0(&local_2c,local_18,&local_30,1);
        fVar4 = *(float *)(param_1 + 0x74 + iVar2 * 8);
        if (fVar4 < 0.0) {
          fVar4 = 0.0;
        }
        fVar3 = 0.0;
        if (0.0 <= *(float *)(param_1 + 0x164)) {
          fVar3 = *(float *)(param_1 + 0x164);
        }
        FUN_00e2ca80(fVar3 * fVar4);
        local_28 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca38) + iVar2 * 4);
        local_24 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca58) + iVar2 * 4);
        FUN_00f682e0(&local_24,local_18,&local_28,1);
        fVar4 = *(float *)(param_1 + 0xe8 + iVar2 * 8);
        if (fVar4 < 0.0) {
          fVar4 = 0.0;
        }
        fVar3 = 0.0;
        if (0.0 <= *(float *)(param_1 + 0x164)) {
          fVar3 = *(float *)(param_1 + 0x164);
        }
        FUN_00e2ca80(fVar3 * fVar4);
        local_20 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca38) + iVar2 * 4);
        local_1c = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca68) + iVar2 * 4);
        FUN_00f682e0(&local_1c,local_18,&local_20,1);
        iVar2 = iVar2 + 1;
      } while (iVar2 < iVar1);
    }
    FUN_00e2cbe0();
  }
  local_10 = BHG::PartConstIndex::vftable;
  FUN_00ef71b0();
  return;
}


