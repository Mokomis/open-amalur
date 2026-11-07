// 00dcde60 FUN_00dcde60

void __thiscall FUN_00dcde60(int param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined1 *local_10;
  int local_c;
  undefined **local_8;
  int local_4;
  
  local_8 = BHG::PartConstIndex::vftable;
  local_c = param_1;
  FUN_00f24ef0(param_2,0x14);
  local_8 = BHG::BuffPartIndex::vftable;
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    iVar1 = *(int *)(DAT_019fe9c4 + 0xca34);
    iVar2 = 0;
    if (0 < iVar1) {
      iVar3 = param_1 + 0xe8;
      do {
        local_1c = 0xb;
        local_18 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca48) + iVar2 * 4);
        FUN_00f92a50(iVar3 + -0xe8,&local_18,&local_1c);
        local_1c = 0xb;
        local_14 = *(undefined4 *)(*(int *)(DAT_019fe9c4 + 0xca58) + iVar2 * 4);
        FUN_00f92a50(iVar3 + -0x74,&local_14,&local_1c);
        local_1c = 0xb;
        local_10 = *(undefined1 **)(*(int *)(DAT_019fe9c4 + 0xca68) + iVar2 * 4);
        FUN_00f92a50(iVar3,&local_10,&local_1c);
        iVar2 = iVar2 + 1;
        iVar3 = iVar3 + 8;
        param_1 = local_c;
      } while (iVar2 < iVar1);
    }
    local_c = 0xb;
    local_10 = &DAT_015d45d1;
    FUN_00f92a50(param_1 + 0x15c,&local_10,&local_c);
    local_c = 0xb;
    local_10 = &LAB_012aedbc;
    FUN_00f92a50(param_1 + 0x164,&local_10,&local_c);
  }
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00ef71b0();
  return;
}


