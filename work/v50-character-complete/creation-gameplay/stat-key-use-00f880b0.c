// 00f880b0 BHG_PartWeapon__vf30

void __fastcall BHG_PartWeapon__vf30(int param_1)

{
  undefined **local_8;
  int local_4;
  
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(*(undefined4 *)(param_1 + 0x18),0x14);
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    FUN_00dcdfd0(*(undefined4 *)(param_1 + 0x18));
    local_8 = (undefined **)0x3a416d;
    FUN_00f878a0(&local_8);
    local_8 = (undefined **)&DAT_01703b1d;
    FUN_00f878a0(&local_8);
    local_8 = (undefined **)&LAB_01291805;
    FUN_00f878a0(&local_8);
  }
  return;
}


