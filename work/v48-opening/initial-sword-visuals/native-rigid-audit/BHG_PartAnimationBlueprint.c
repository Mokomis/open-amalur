// 00efcf30 BHG_PartAnimationBlueprint__vf1

void BHG_PartAnimationBlueprint__vf1(void)

{
  return;
}


// 00efcf40 BHG_PartAnimationBlueprint__vf2

void __thiscall BHG_PartAnimationBlueprint__vf2(int param_1,undefined4 param_2)

{
  *(undefined4 *)(param_1 + 4) = param_2;
  return;
}


// 00efcf50 BHG_PartAnimationBlueprint__vf3

undefined4 BHG_PartAnimationBlueprint__vf3(void)

{
  return 4;
}


// 00efcf60 BHG_PartAnimationBlueprint__vf0

undefined4 * __thiscall BHG_PartAnimationBlueprint__vf0(undefined4 *param_1,byte param_2)

{
  *param_1 = BHG::PartBlueprint::vftable;
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00f09d90 BHG_PartAnimationBlueprint__xtor

void BHG_PartAnimationBlueprint__xtor(undefined4 param_1,undefined4 param_2)

{
  undefined4 *puVar1;
  
  puVar1 = (undefined4 *)FUN_00afdf70(param_1,param_2);
  if (puVar1 != (undefined4 *)0x0) {
    *puVar1 = BHG::PartAnimationBlueprint::vftable;
  }
  return;
}


