// 00dcdfd0 FUN_00dcdfd0

void FUN_00dcdfd0(undefined4 param_1)

{
  int iVar1;
  int iVar2;
  undefined4 local_14;
  undefined4 local_10;
  undefined1 *local_c;
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
        local_14 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca48) + iVar2 * 4);
        FUN_00f878a0(&local_14);
        local_10 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca58) + iVar2 * 4);
        FUN_00f878a0(&local_10);
        local_c = *(undefined1 **)(*(int *)(DAT_019fe9c4 + 0xca68) + iVar2 * 4);
        FUN_00f878a0(&local_c);
        iVar2 = iVar2 + 1;
      } while (iVar2 < iVar1);
    }
    local_c = &DAT_015d45d1;
    FUN_00f878a0(&local_c);
    local_c = &LAB_012aedbc;
    FUN_00f878a0(&local_c);
  }
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00ef71b0();
  return;
}


