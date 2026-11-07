// 00a1ada0 BHG_RandomMotionChooser__xtor

undefined4 * __fastcall BHG_RandomMotionChooser__xtor(undefined4 *param_1)

{
  *param_1 = BHG::RandomMotionChooser::vftable;
  *(undefined2 *)(param_1 + 4) = 0x1f;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  FUN_00c3c760();
  return param_1;
}


// 00a1add0 BHG_RandomMotionChooser__vf1

void BHG_RandomMotionChooser__vf1(undefined4 *param_1)

{
  *param_1 = &DAT_013e8f54;
  return;
}


// 00a1ae60 BHG_RandomMotionChooser__vf0

undefined4 BHG_RandomMotionChooser__vf0(char *param_1,char param_2)

{
  if ((param_1 != "\x02") && ((param_2 != '\0' || (param_1 != "ts")))) {
    return 0;
  }
  return 1;
}


// 00a1b060 BHG_RandomMotionChooser__vf2

undefined4 * __thiscall BHG_RandomMotionChooser__vf2(undefined4 *param_1,byte param_2)

{
  *param_1 = BHG::RandomMotionChooser::vftable;
  FUN_00c3c770();
  if (param_1[1] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 4),param_1[1]);
  }
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  *param_1 = BHG::MotionVariantChooser::vftable;
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00a1b1d0 BHG_RandomMotionChooser__vf3

void __thiscall BHG_RandomMotionChooser__vf3(int param_1,undefined4 param_2)

{
  FUN_00a1b0c0(param_1 + 4,param_2);
  return;
}


// 00c8ff30 BHG_RandomMotionChooser__vf4

void __thiscall
BHG_RandomMotionChooser__vf4
          (int param_1,undefined4 param_2,int param_3,undefined4 param_4,int *param_5)

{
  float fVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  float10 fVar5;
  float fVar6;
  float local_4;
  
  fVar6 = 0.0;
  *param_5 = 0;
  iVar3 = *(int *)(param_1 + 8);
  iVar2 = 0;
  local_4 = 0.0;
  if (3 < iVar3) {
    iVar4 = 2;
    do {
      if (param_3 != iVar2) {
        fVar6 = (float)*(int *)(*(int *)(param_1 + 4) + iVar2 * 4) + fVar6;
      }
      if (param_3 != iVar4 + -1) {
        fVar6 = (float)*(int *)(*(int *)(param_1 + 4) + 4 + iVar2 * 4) + fVar6;
      }
      if (param_3 != iVar4) {
        fVar6 = (float)*(int *)(*(int *)(param_1 + 4) + 8 + iVar2 * 4) + fVar6;
      }
      if (param_3 != iVar4 + 1) {
        fVar6 = (float)*(int *)(*(int *)(param_1 + 4) + 0xc + iVar2 * 4) + fVar6;
      }
      iVar2 = iVar2 + 4;
      iVar4 = iVar4 + 4;
      local_4 = fVar6;
    } while (iVar2 < iVar3 + -3);
  }
  for (; iVar2 < iVar3; iVar2 = iVar2 + 1) {
    if (param_3 != iVar2) {
      local_4 = (float)*(int *)(*(int *)(param_1 + 4) + iVar2 * 4) + local_4;
    }
  }
  fVar5 = (float10)FUN_00b0ac90();
  fVar6 = 0.0;
  iVar3 = 0;
  if (0 < *(int *)(param_1 + 8)) {
    do {
      if (param_3 != iVar3) {
        fVar1 = (float)*(int *)(*(int *)(param_1 + 4) + iVar3 * 4) / local_4;
        if ((fVar6 <= (float)fVar5) && ((float)fVar5 < fVar1 + fVar6)) {
          *param_5 = iVar3;
          return;
        }
        fVar6 = fVar1 + fVar6;
      }
      iVar3 = iVar3 + 1;
      if (*(int *)(param_1 + 8) <= iVar3) {
        return;
      }
    } while( true );
  }
  return;
}


