// 00a126c0 T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor

void __fastcall T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor(undefined4 *param_1)

{
  *param_1 = BHG::FactoryAllocator<BHG::MotionVariantChooser>::vftable;
  param_1[2] = 0;
  if (param_1[1] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 4),param_1[1]);
  }
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  return;
}


// 00a12700 T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__vf0

undefined4 * __thiscall
T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__vf0(undefined4 *param_1,byte param_2)

{
  *param_1 = BHG::FactoryAllocator<BHG::MotionVariantChooser>::vftable;
  param_1[2] = 0;
  if (param_1[1] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 4),param_1[1]);
  }
  param_1[1] = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00a15c60 T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor_2

void T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor_2(undefined4 param_1)

{
  int *piVar1;
  undefined4 *puVar2;
  
  if ((DAT_019fa71c == (undefined4 *)0x0) &&
     (DAT_019fa71c = (undefined4 *)FUN_00afdf70(0x26,0x14), DAT_019fa71c != (undefined4 *)0x0)) {
    *DAT_019fa71c = BHG::FactoryAllocator<BHG::MotionVariantChooser>::vftable;
    *(undefined2 *)(DAT_019fa71c + 4) = 0x26;
    DAT_019fa71c[1] = 0;
    DAT_019fa71c[3] = 0;
    DAT_019fa71c[2] = 0;
    *(undefined2 *)((int)DAT_019fa71c + 0x12) = 0xffff;
  }
  puVar2 = DAT_019fa71c;
  piVar1 = DAT_019fa71c + 1;
  if ((uint)DAT_019fa71c[3] <= (uint)DAT_019fa71c[2]) {
    FUN_00a0c060((int)*(short *)((int)DAT_019fa71c + 0x12));
  }
  *(undefined4 *)(*piVar1 + puVar2[2] * 4) = param_1;
  piVar1 = puVar2 + 2;
  *piVar1 = *piVar1 + 1;
  return;
}


// 00d2c080 T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor_3

undefined4 T_FactoryAllocator_VMotionVariantChooser_BHG_BHG__xtor_3(int param_1)

{
  int *piVar1;
  undefined4 uVar2;
  int iVar3;
  
  if ((DAT_019fa71c == (undefined4 *)0x0) &&
     (DAT_019fa71c = (undefined4 *)FUN_00afdf70(0x26,0x14), DAT_019fa71c != (undefined4 *)0x0)) {
    *DAT_019fa71c = BHG::FactoryAllocator<BHG::MotionVariantChooser>::vftable;
    *(undefined2 *)(DAT_019fa71c + 4) = 0x26;
    DAT_019fa71c[1] = 0;
    DAT_019fa71c[3] = 0;
    DAT_019fa71c[2] = 0;
    *(undefined2 *)((int)DAT_019fa71c + 0x12) = 0xffff;
  }
  iVar3 = 0;
  if (0 < (int)DAT_019fa71c[2]) {
    piVar1 = (int *)DAT_019fa71c[1];
    do {
      if (((int *)*piVar1)[1] == param_1) {
                    /* WARNING: Could not recover jumptable at 0x00d2c0ec. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        uVar2 = (**(code **)(*(int *)*piVar1 + 4))();
        return uVar2;
      }
      iVar3 = iVar3 + 1;
      piVar1 = piVar1 + 1;
    } while (iVar3 < (int)DAT_019fa71c[2]);
  }
  return 0;
}


