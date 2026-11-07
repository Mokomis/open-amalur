// 00fd9630 BHG_SpaceGraph__xtor

void __fastcall BHG_SpaceGraph__xtor(undefined4 *param_1)

{
  int iVar1;
  
  *param_1 = BHG::SpaceGraph::vftable;
  FUN_00fb4a10();
  if (param_1[1] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 4),param_1[1]);
  }
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  iVar1 = param_1[0x15];
  if (1 < iVar1) {
    param_1[0x15] = 0;
    (**(code **)(*DAT_019f4df8 + 0xa8))(iVar1);
  }
  if (param_1[0x11] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 0x14),param_1[0x11]);
  }
  param_1[0x11] = 0;
  param_1[0x13] = 0;
  param_1[0x12] = 0;
  *(undefined2 *)((int)param_1 + 0x52) = 0xffff;
  if (param_1[0xd] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 0x10),param_1[0xd]);
  }
  param_1[0xd] = 0;
  param_1[0xf] = 0;
  param_1[0xe] = 0;
  *(undefined2 *)((int)param_1 + 0x42) = 0xffff;
  if (param_1[9] != 0) {
    FUN_00fca490((int)*(short *)(param_1 + 0xc),param_1[0xb],param_1[9]);
  }
  param_1[9] = 0;
  param_1[0xb] = 0;
  param_1[10] = 0;
  *(undefined2 *)((int)param_1 + 0x32) = 0xffff;
  if (param_1[5] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 8),param_1[5]);
  }
  param_1[5] = 0;
  param_1[7] = 0;
  param_1[6] = 0;
  *(undefined2 *)((int)param_1 + 0x22) = 0xffff;
  if (param_1[1] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 4),param_1[1]);
  }
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  return;
}


// 00fd9750 BHG_SpaceGraph__vf0

undefined4 __thiscall BHG_SpaceGraph__vf0(undefined4 param_1,byte param_2)

{
  BHG_SpaceGraph__xtor();
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00fe7510 BHG_SpaceGraph__xtor_2

/* WARNING: Removing unreachable block (ram,0x00fe7595) */

undefined4 * __fastcall BHG_SpaceGraph__xtor_2(undefined4 *param_1)

{
  *param_1 = BHG::SpaceGraph::vftable;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  *(undefined2 *)(param_1 + 4) = 0x2b;
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)(param_1 + 8) = 0x2b;
  *(undefined2 *)((int)param_1 + 0x22) = 0xffff;
  param_1[5] = 0;
  param_1[7] = 0;
  param_1[6] = 0;
  param_1[9] = 0;
  param_1[0xb] = 0;
  param_1[10] = 0;
  *(undefined2 *)(param_1 + 0xc) = 0x2b;
  *(undefined2 *)((int)param_1 + 0x32) = 0xffff;
  *(undefined2 *)(param_1 + 0x10) = 0x2b;
  param_1[0xd] = 0;
  param_1[0xf] = 0;
  param_1[0xe] = 0;
  *(undefined2 *)((int)param_1 + 0x42) = 0xffff;
  *(undefined2 *)((int)param_1 + 0x52) = 0xffff;
  *(undefined2 *)(param_1 + 0x14) = 0x2b;
  param_1[0x11] = 0;
  param_1[0x13] = 0;
  param_1[0x12] = 0;
  param_1[0x15] = 0;
  param_1[0x15] = 0;
  if (param_1[9] != 0) {
    FUN_00fca490((int)*(short *)(param_1 + 0xc),param_1[0xb],param_1[9]);
  }
  param_1[9] = 0;
  param_1[0xb] = 0;
  param_1[10] = 0;
  *(undefined2 *)((int)param_1 + 0x32) = 0xffff;
  param_1[0x12] = 0;
  param_1[0xe] = 0;
  return param_1;
}


