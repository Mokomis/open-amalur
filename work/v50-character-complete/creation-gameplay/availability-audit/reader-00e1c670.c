// 00e1c670 FUN_00e1c670

undefined4 FUN_00e1c670(int param_1,undefined4 param_2,undefined **param_3)

{
  undefined4 uVar1;
  int iVar2;
  int unaff_EDI;
  undefined **ppuStack_34;
  undefined4 uStack_30;
  int iStack_20;
  short sStack_14;
  
  iVar2 = param_1;
  if (param_1 == 0) {
    return 1;
  }
  uStack_30 = 0xe1c6c0;
  FUN_00a87550();
  uStack_30 = 0;
  ppuStack_34 = param_3;
  FUN_00a92ba0(param_2);
  uStack_30 = 4;
  ppuStack_34 = (undefined **)&param_1;
  (*(code *)PTR_BHG_MemoryDataWalk__vf1_0172e47c)();
  uVar1 = *(undefined4 *)(iVar2 + 0xc);
  (**(code **)(unaff_EDI + 4))((undefined4 *)(iVar2 + 4),4);
  FUN_00e1a8f0(uVar1,&ppuStack_34,iVar2 + 8,*(undefined4 *)(iVar2 + 4));
  ppuStack_34 = BHG::MemoryDataWalk::vftable;
  FUN_00a87560();
  if (iStack_20 != 0) {
    FUN_00afe180((int)sStack_14,iStack_20);
  }
  return 0;
}

