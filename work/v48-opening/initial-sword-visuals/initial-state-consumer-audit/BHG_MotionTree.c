// 00c63ac0 BHG_MotionTree__vf2

void __fastcall BHG_MotionTree__vf2(int param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_013be4dc;
  *(undefined4 *)(param_1 + 0xd8) = 0;
  *(undefined4 *)(param_1 + 0xdc) = uVar1;
  FUN_00a7d580();
  FUN_00a7d580();
  FUN_00a7d580();
  FUN_00a7d580();
  BHG_Asset__vf2();
  return;
}


// 00d0f8b0 BHG_MotionTree__vf4

void __fastcall BHG_MotionTree__vf4(int param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar2 = 0;
  if (0 < *(int *)(param_1 + 0x10)) {
    do {
      (**(code **)(**(int **)(*(int *)(param_1 + 0x14) + iVar2 * 4) + 0x10))();
      iVar2 = iVar2 + 1;
    } while (iVar2 < *(int *)(param_1 + 0x10));
  }
  FUN_00a7edc0(*(undefined4 *)(param_1 + 4),0);
  FUN_00a7edc0(*(undefined4 *)(param_1 + 4),0);
  iVar2 = 0;
  if (0 < *(int *)(param_1 + 4)) {
    iVar1 = 0;
    do {
      iVar3 = *(int *)(param_1 + 8) + iVar1;
      if ((*(byte *)(iVar3 + 0x2b) & 0x20) != 0) {
        FUN_00a7ad80(iVar2,1);
      }
      if (*(char *)(iVar3 + 0x28) == '\0') {
        FUN_00a7ad80(iVar2,1);
      }
      if ((*(char *)(iVar3 + 0x28) == '\x01') && ((*(byte *)(iVar3 + 0x2b) & 8) == 0)) {
        FUN_00a7ad80(iVar2,1);
      }
      iVar2 = iVar2 + 1;
      iVar1 = iVar1 + 0x2c;
    } while (iVar2 < *(int *)(param_1 + 4));
  }
  FUN_00cf7a50();
  return;
}


// 00d1a250 BHG_MotionTree__xtor

undefined4 * __fastcall BHG_MotionTree__xtor(undefined4 *param_1)

{
  undefined4 uVar1;
  
  *param_1 = BHG::Asset::vftable;
  FUN_00a6bfd0();
  *param_1 = BHG::MotionTree::vftable;
  param_1[1] = 0;
  param_1[2] = 0;
  param_1[3] = 0x1f;
  param_1[4] = 0;
  param_1[5] = 0;
  param_1[6] = 0x1f;
  param_1[7] = 0;
  param_1[8] = 0;
  param_1[9] = 0x1f;
  *(undefined2 *)(param_1 + 0xd) = 0x1f;
  FUN_00a7b0f0();
  *(undefined2 *)(param_1 + 0x12) = 0x1f;
  FUN_00a7b0f0();
  param_1[0x14] = 0;
  param_1[0x16] = 0;
  param_1[0x15] = 0;
  *(undefined2 *)((int)param_1 + 0x5e) = 0xffff;
  *(undefined2 *)(param_1 + 0x17) = 0x1f;
  *(undefined2 *)(param_1 + 0x1b) = 0x1f;
  param_1[0x18] = 0;
  param_1[0x1a] = 0;
  param_1[0x19] = 0;
  *(undefined2 *)((int)param_1 + 0x6e) = 0xffff;
  param_1[0x1c] = 0x1f;
  param_1[0x1d] = 0;
  param_1[0x1e] = 0;
  param_1[0x1f] = 0x1f;
  *(undefined2 *)(param_1 + 0x23) = 0x1f;
  param_1[0x20] = 0;
  param_1[0x22] = 0;
  param_1[0x21] = 0;
  *(undefined2 *)((int)param_1 + 0x8e) = 0xffff;
  *(undefined2 *)(param_1 + 0x27) = 0x1f;
  param_1[0x24] = 0;
  param_1[0x26] = 0;
  param_1[0x25] = 0;
  *(undefined2 *)((int)param_1 + 0x9e) = 0xffff;
  param_1[0x28] = 0x1f;
  param_1[0x29] = 0;
  param_1[0x2a] = 0;
  param_1[0x2b] = 0x1f;
  *(undefined2 *)(param_1 + 0x2f) = 0x1f;
  FUN_00a7b0f0();
  *(undefined2 *)(param_1 + 0x34) = 0x1f;
  FUN_00a7b0f0();
  uVar1 = DAT_013be4dc;
  param_1[0x36] = 0;
  param_1[0x37] = uVar1;
  FUN_00a7d580();
  FUN_00a7d580();
  FUN_00a7d580();
  FUN_00a7d580();
  return param_1;
}


// 00d1a3b0 BHG_MotionTree__xtor_2

void __fastcall BHG_MotionTree__xtor_2(undefined4 *param_1)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  
  *param_1 = BHG::MotionTree::vftable;
  FUN_00a7c6c0();
  FUN_00a7c6c0();
  if (param_1[0x2a] != 0) {
    FUN_00afe180(param_1[0x2b],param_1[0x2a]);
  }
  if (param_1[0x24] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 0x27),param_1[0x24]);
  }
  param_1[0x24] = 0;
  param_1[0x26] = 0;
  param_1[0x25] = 0;
  *(undefined2 *)((int)param_1 + 0x9e) = 0xffff;
  if (param_1[0x20] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 0x23),param_1[0x20]);
  }
  param_1[0x20] = 0;
  param_1[0x22] = 0;
  param_1[0x21] = 0;
  *(undefined2 *)((int)param_1 + 0x8e) = 0xffff;
  if (param_1[0x1e] != 0) {
    FUN_00afe180(param_1[0x1f],param_1[0x1e]);
  }
  if (param_1[0x18] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 0x1b),param_1[0x18]);
  }
  param_1[0x18] = 0;
  param_1[0x1a] = 0;
  param_1[0x19] = 0;
  *(undefined2 *)((int)param_1 + 0x6e) = 0xffff;
  if (param_1[0x14] != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 0x17),param_1[0x14]);
  }
  param_1[0x14] = 0;
  param_1[0x16] = 0;
  param_1[0x15] = 0;
  *(undefined2 *)((int)param_1 + 0x5e) = 0xffff;
  FUN_00a7c6c0();
  FUN_00a7c6c0();
  if (param_1[8] != 0) {
    FUN_00afe180(param_1[9],param_1[8]);
  }
  FUN_00c82600(param_1[6],param_1[5],param_1[4]);
  iVar1 = param_1[2];
  uVar2 = param_1[3];
  iVar3 = param_1[1];
  if (iVar1 != 0) {
    for (; iVar3 != 0; iVar3 = iVar3 + -1) {
      FUN_00ab8e10();
    }
    FUN_00afe180(uVar2,iVar1);
  }
  BHG_Asset__xtor();
  return;
}


// 00d1a540 BHG_MotionTree__vf0

undefined4 __thiscall BHG_MotionTree__vf0(undefined4 param_1,byte param_2)

{
  BHG_MotionTree__xtor_2();
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00d40390 BHG_MotionTree__vf3

undefined4 __thiscall BHG_MotionTree__vf3(int param_1,undefined4 *param_2,undefined4 param_3)

{
  undefined4 *puVar1;
  int iVar2;
  undefined4 uVar3;
  int unaff_EBP;
  int unaff_EDI;
  undefined **ppuVar4;
  undefined4 *puVar5;
  int *piVar6;
  int iVar7;
  undefined4 *puStack_3c;
  undefined ***pppuStack_38;
  undefined **local_24 [5];
  undefined4 local_10;
  undefined4 local_c;
  undefined4 local_8;
  undefined2 local_4;
  undefined2 local_2;
  
  local_4 = 0x1a;
  local_2 = 0xffff;
  local_24[0] = BHG::MemoryDataWalk::vftable;
  local_10 = 0;
  local_8 = 0;
  local_c = 0;
  pppuStack_38 = (undefined ***)0xd403ca;
  FUN_00a87550();
  pppuStack_38 = (undefined ***)param_3;
  puStack_3c = param_2;
  FUN_00a92bf0();
  pppuStack_38 = local_24;
  puStack_3c = (undefined4 *)0xd403e9;
  FUN_00d276b0();
  uVar3 = *(undefined4 *)(param_1 + 0x18);
  pppuStack_38 = (undefined ***)0x4;
  puStack_3c = (undefined4 *)(param_1 + 0x10);
  (*(code *)local_24[0][1])();
  FUN_00d3b3b0(uVar3,&stack0xffffffd4,param_1 + 0x14,*(undefined4 *)(param_1 + 0x10));
  uVar3 = *(undefined4 *)(param_1 + 0x24);
  iVar7 = 4;
  piVar6 = (int *)(param_1 + 0x1c);
  (**(code **)(unaff_EBP + 4))();
  iVar2 = *(int *)(param_1 + 0x1c);
  if (iVar2 != 0) {
    iVar2 = iVar2 * 4;
    uVar3 = FUN_00afdf70(uVar3,iVar2);
    *(undefined4 *)(param_1 + 0x20) = uVar3;
    (**(code **)(unaff_EDI + 4))(uVar3,iVar2);
  }
  FUN_00ce0600(param_1 + 0x50,&stack0xffffffcc);
  FUN_00ce0680(param_1 + 0x60,&stack0xffffffcc);
  uVar3 = *(undefined4 *)(param_1 + 0x7c);
  puVar1 = (undefined4 *)(param_1 + 0x74);
  puVar5 = puVar1;
  (**(code **)(unaff_EDI + 4))(puVar1,4);
  FUN_00ce0200(uVar3,&puStack_3c,param_1 + 0x78,*puVar1);
  FUN_00ce0600(param_1 + 0x80,&puStack_3c);
  FUN_00ce0680(param_1 + 0x90,&puStack_3c);
  uVar3 = *(undefined4 *)(param_1 + 0xac);
  (*(code *)puStack_3c[1])((int *)(param_1 + 0xa4),4);
  iVar2 = *(int *)(param_1 + 0xa4);
  if (iVar2 != 0) {
    iVar2 = iVar2 * 4;
    uVar3 = FUN_00afdf70(uVar3,iVar2);
    *(undefined4 *)(param_1 + 0xa8) = uVar3;
    (*(code *)piVar6[1])(uVar3,iVar2);
  }
  (*(code *)piVar6[1])(param_1 + 0xd8,4);
  (*(code *)puVar5[1])(param_1 + 0xdc,4);
  ppuVar4 = BHG::MemoryDataWalk::vftable;
  FUN_00a87560();
  if (iVar7 != 0) {
    FUN_00afe180((int)(short)unaff_EDI,iVar7,ppuVar4);
  }
  return 0;
}


