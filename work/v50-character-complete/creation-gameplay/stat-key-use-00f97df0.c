// 00f97df0 BHG_PartTarget__vf29

void __fastcall BHG_PartTarget__vf29(int param_1)

{
  undefined **local_c;
  undefined **local_8;
  int local_4;
  
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(*(undefined4 *)(param_1 + 0x18),0x14);
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    local_c = *(undefined ***)(param_1 + 0x1c);
    local_8 = (undefined **)0x194c55;
    FUN_00f929b0(param_1 + 0x4c,&local_8,&local_c);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0xafaf36;
    FUN_00f92a50(param_1 + 0x54,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0x198f075;
    FUN_00f92a50(param_1 + 0x5c,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = &PTR_caseD_52_009e20c0;
    FUN_00f92a50(param_1 + 0x88,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0x203d64a;
    FUN_00f92af0(param_1 + 0x90,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0x10dffbb;
    FUN_00f92a50(param_1 + 200,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0xec0e92;
    FUN_00f92a50(param_1 + 0xd0,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)&DAT_0149329d;
    FUN_00f929b0(param_1 + 0x78,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0x756f31;
    FUN_00f929b0(param_1 + 0xd8,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined **)0x5d21d9;
    FUN_00f929b0(param_1 + 0x68,&local_c,&local_8);
  }
  return;
}


