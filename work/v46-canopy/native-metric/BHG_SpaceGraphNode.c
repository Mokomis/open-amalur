// 00fea2c0 BHG_SpaceGraphNode__xtor

undefined4 * __fastcall BHG_SpaceGraphNode__xtor(undefined4 *param_1)

{
  *param_1 = BHG::SpaceGraphNode::vftable;
  param_1[1] = 0;
  *(undefined2 *)((int)param_1 + 0x16) = 0xffff;
  *(undefined2 *)(param_1 + 5) = 0x2b;
  param_1[2] = 0;
  param_1[4] = 0;
  param_1[3] = 0;
  *(undefined2 *)(param_1 + 9) = 0x2b;
  FUN_00a7b0f0();
  if (1 < (int)param_1[1]) {
    (**(code **)(*DAT_019f4df8 + 0xa8))(param_1[1]);
  }
  param_1[1] = 0;
  FUN_00fc8ba0();
  return param_1;
}


// 00fea330 BHG_SpaceGraphNode__xtor_2

void __fastcall BHG_SpaceGraphNode__xtor_2(undefined4 *param_1)

{
  int iVar1;
  
  *param_1 = BHG::SpaceGraphNode::vftable;
  FUN_00a7c6c0();
  if (param_1[2] != 0) {
    FUN_00fc2410((int)*(short *)(param_1 + 5),param_1[4],param_1[2]);
  }
  param_1[2] = 0;
  param_1[4] = 0;
  param_1[3] = 0;
  *(undefined2 *)((int)param_1 + 0x16) = 0xffff;
  iVar1 = param_1[1];
  if (1 < iVar1) {
    param_1[1] = 0;
    (**(code **)(*DAT_019f4df8 + 0xa8))(iVar1);
  }
  return;
}


// 00fea390 BHG_SpaceGraphNode__vf0

undefined4 __thiscall BHG_SpaceGraphNode__vf0(undefined4 param_1,byte param_2)

{
  BHG_SpaceGraphNode__xtor_2();
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


