// 00a1aac0 T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__xtor

undefined4 * __fastcall
T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__xtor(undefined4 *param_1)

{
  *param_1 = BHG::BaseClassAllocator<BHG::MotionVariantChooser>::vftable;
  param_1[1] = 0;
  T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor_2(param_1);
  *param_1 = BHG::ClassAllocator<BHG::MotionVariantChooser,BHG::RandomMotionChooser>::vftable;
  param_1[1] = &DAT_013e8f54;
  return param_1;
}


// 00a1abd0 T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__vf2

undefined4
T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__vf2
          (char *param_1,char param_2)

{
  if ((param_1 != "\x02") && ((param_2 != '\0' || (param_1 != "ts")))) {
    return 0;
  }
  return 1;
}


// 00a1ac00 T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__vf0

undefined4 * __thiscall
T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__vf0
          (undefined4 *param_1,byte param_2)

{
  *param_1 = BHG::BaseClassAllocator<BHG::MotionVariantChooser>::vftable;
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00a1b1f0 T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__vf1

undefined4 * T_ClassAllocator_VMotionVariantChooser_BHG_VRandomMotionChooser_2_BHG__vf1(void)

{
  undefined4 *puVar1;
  
  puVar1 = (undefined4 *)FUN_00afdf70(0x1f,0x14);
  if (puVar1 != (undefined4 *)0x0) {
    *puVar1 = BHG::RandomMotionChooser::vftable;
    *(undefined2 *)(puVar1 + 4) = 0x1f;
    puVar1[1] = 0;
    puVar1[3] = 0;
    puVar1[2] = 0;
    *(undefined2 *)((int)puVar1 + 0x12) = 0xffff;
    FUN_00c3c760();
  }
  return puVar1;
}


