// 00dce2f0 FUN_00dce2f0

void FUN_00dce2f0(undefined4 param_1)

{
  int iVar1;
  int iVar2;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  undefined **local_8;
  int local_4;
  
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(param_1,0x14);
  local_8 = BHG::BuffPartIndex::vftable;
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    iVar1 = *(int *)(DAT_019fe9c4 + 0xca34);
    iVar2 = 0;
    if (0 < iVar1) {
      do {
        local_20 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca38) + iVar2 * 4);
        local_1c = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca48) + iVar2 * 4);
        FUN_00f5aca0(&local_1c,&local_20);
        local_18 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca38) + iVar2 * 4);
        local_14 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca58) + iVar2 * 4);
        FUN_00f5aca0(&local_14,&local_18);
        local_10 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca38) + iVar2 * 4);
        local_c = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca68) + iVar2 * 4);
        FUN_00f5aca0(&local_c,&local_10);
        iVar2 = iVar2 + 1;
      } while (iVar2 < iVar1);
    }
  }
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00ef71b0();
  return;
}


