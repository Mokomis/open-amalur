// 00f42aa0 FUN_00f42aa0

void FUN_00f42aa0(int *param_1,undefined4 param_2,undefined4 param_3,int param_4)

{
  int *piVar1;
  int iVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  char local_35;
  int local_34;
  byte local_30 [4];
  byte local_2c [4];
  uint local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined **local_1c [2];
  undefined **local_14 [5];
  
  piVar1 = param_1;
  iVar5 = 0;
  if (param_1 != (int *)0x0) {
    iVar2 = FUN_00af4d70("genders",0x20eb74,0x20eb74,1);
    if ((*(byte *)(iVar2 + 10) & 0x80) == 0) {
      FUN_00af14b0();
    }
    param_1 = *(int **)(iVar2 + 4);
    BHG_MgrIndex__xtor(local_14,&param_1);
    FUN_00af2060();
    iVar2 = FUN_00af4d70("races",0x13ba23,0x13ba23,1);
    if ((*(byte *)(iVar2 + 10) & 0x80) == 0) {
      FUN_00af14b0();
    }
    param_1 = *(int **)(iVar2 + 4);
    BHG_MgrIndex__xtor(local_1c,&param_1);
    FUN_00af2060();
    FUN_00b3d2e0(local_14,&param_2,local_30);
    FUN_00b3d2e0(local_1c,&param_3,local_2c);
    local_28 = 1 << (local_2c[0] & 0x1f);
    param_1 = (int *)CONCAT31(param_1._1_3_,'\x01' << (local_30[0] & 0x1f));
    uVar3 = 0;
    if (piVar1[1] != 0) {
      do {
        *(undefined4 *)(*piVar1 + uVar3 * 4) = 0;
        uVar3 = uVar3 + 1;
      } while (uVar3 < (uint)piVar1[1]);
    }
    piVar1[1] = 0;
    iVar2 = 0;
    if (0 < *(int *)(local_34 + 8)) {
      do {
        iVar6 = *(int *)(local_34 + 4) + iVar5;
        if (((*(int *)(*(int *)(local_34 + 4) + 8 + iVar5) == param_4) &&
            ((*(uint *)(iVar6 + 0xc) & local_28) != 0)) &&
           ((*(byte *)(iVar6 + 0x10) & (byte)param_1) != 0)) {
          local_24 = 0;
          local_20 = 0;
          iVar4 = FUN_00e08c40(*(undefined4 *)(iVar6 + 4),&local_20,&local_24,&local_35);
          if ((iVar4 != 1) && (local_35 == '\x01')) {
            FUN_00ea1130(iVar6);
          }
        }
        iVar2 = iVar2 + 1;
        iVar5 = iVar5 + 0x14;
      } while (iVar2 < *(int *)(local_34 + 8));
    }
    local_1c[0] = BHG::MgrIndex::vftable;
    (*(code *)PTR_BHG_MgrIndex__vf2_01730720)();
    local_14[0] = BHG::MgrIndex::vftable;
    (*(code *)PTR_BHG_MgrIndex__vf2_01730720)();
  }
  return;
}

