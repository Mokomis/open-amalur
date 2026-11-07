// 01031480 FUN_01031480

undefined4 *
FUN_01031480(undefined4 *param_1,undefined4 *param_2,undefined4 *param_3,undefined4 *param_4)

{
  undefined4 uVar1;
  int iVar2;
  int local_38;
  int local_34;
  undefined4 local_30;
  short local_2c;
  undefined2 local_2a;
  undefined **local_28 [10];
  
  *(undefined2 *)((int)param_1 + 0xe) = 0xffff;
  iVar2 = 0;
  *(undefined2 *)(param_1 + 3) = 0x1e;
  *param_1 = 0;
  param_1[2] = 0;
  param_1[1] = 0;
  local_2c = 0x27;
  local_2a = 0xffff;
  local_38 = 0;
  local_30 = 0;
  local_34 = 0;
  FUN_00f42aa0(&local_38,*param_2,*param_3,*param_4);
  if (0 < local_34) {
    do {
      uVar1 = FUN_00a6fe10();
      FUN_00a6c280();
      BHG_LuaParameter__xtor_19(uVar1,0x2f);
      if ((uint)param_1[2] <= (uint)param_1[1]) {
        FUN_00aab210((int)*(short *)((int)param_1 + 0xe));
      }
      param_1[1] = param_1[1] + 1;
      FUN_00aa1ac0(local_28);
      local_28[0] = BHG::LuaParameter::vftable;
      FUN_00aa1e60();
      FUN_00af2060();
      iVar2 = iVar2 + 1;
    } while (iVar2 < local_34);
  }
  if (local_38 != 0) {
    FUN_00afe180((int)local_2c,local_38);
  }
  return param_1;
}

