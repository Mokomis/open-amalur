// 00f982d0 BHG_PartWeapon__vf29

void __fastcall BHG_PartWeapon__vf29(int param_1)

{
  undefined *local_c;
  undefined **local_8;
  int local_4;
  
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(*(undefined4 *)(param_1 + 0x18),0x14);
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    FUN_00dcde60(*(undefined4 *)(param_1 + 0x18));
    local_c = *(undefined **)(param_1 + 0x1c);
    local_8 = (undefined **)0x3a416d;
    FUN_00f92a50(param_1 + 400,&local_8,&local_c);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = &DAT_01703b1d;
    FUN_00f92a50(param_1 + 0x198,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = &LAB_01291805;
    FUN_00f92a50(param_1 + 0x1a0,&local_c,&local_8);
  }
  return;
}


