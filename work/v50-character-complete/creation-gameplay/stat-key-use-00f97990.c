// 00f97990 BHG_PartTalent__vf29

void __fastcall BHG_PartTalent__vf29(int param_1)

{
  undefined *local_c;
  undefined **local_8;
  int local_4;
  
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(*(undefined4 *)(param_1 + 0x18),0x14);
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    local_c = *(undefined **)(param_1 + 0x1c);
    local_8 = (undefined **)0xefbb2;
    FUN_00f929b0(param_1 + 0x74,&local_8,&local_c);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined *)0x3fe1bf;
    FUN_00f929b0(param_1 + 0x7c,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined *)0x96407b;
    FUN_00f92a50(param_1 + 0x88,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = &DAT_01709970;
    FUN_00f92a50(param_1 + 0x90,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined *)0x72d623;
    FUN_00f92a50(param_1 + 0x98,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined *)0x453063f;
    FUN_00f92a50(param_1 + 0xa8,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined *)0x45bf238;
    FUN_00f92a50(param_1 + 0xb0,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = (undefined *)0x49fec42;
    FUN_00f92a50(param_1 + 0xb8,&local_c,&local_8);
    local_8 = *(undefined ***)(param_1 + 0x1c);
    local_c = &LAB_0125c4f6;
    FUN_00f92a50(param_1 + 0xc0,&local_c,&local_8);
  }
  return;
}


