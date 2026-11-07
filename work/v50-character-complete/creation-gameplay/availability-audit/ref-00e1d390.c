// 00e1d390 FUN_00e1d390

void __thiscall FUN_00e1d390(int param_1,undefined2 param_2,undefined4 param_3)

{
  uint uVar1;
  int iVar2;
  undefined4 uVar3;
  int iVar4;
  int iVar5;
  undefined4 local_6c;
  byte local_66;
  undefined **local_64 [5];
  int local_50;
  undefined4 local_4c;
  undefined4 local_48;
  short local_44;
  undefined2 local_42;
  
  if (*(uint *)(param_1 + 0x1dc) <= *(uint *)(param_1 + 0x1d8)) {
    FUN_00a0b7a0((int)*(short *)(param_1 + 0x1e2));
  }
  *(undefined2 *)(*(int *)(param_1 + 0x1d4) + *(int *)(param_1 + 0x1d8) * 2) = param_2;
  *(int *)(param_1 + 0x1d8) = *(int *)(param_1 + 0x1d8) + 1;
  if (*(uint *)(param_1 + 0x1ec) <= *(uint *)(param_1 + 0x1e8)) {
    FUN_00e1b850((int)*(short *)(param_1 + 0x1f2));
  }
  *(int *)(param_1 + 0x1e8) = *(int *)(param_1 + 0x1e8) + 1;
  iVar5 = *(int *)(param_1 + 0x1e8);
  FUN_00af0590(param_3);
  FUN_00af77a0("GlobalBinaryData\\persistent_table_manifest.conditional_expression_mgr");
  BHG_FileExtracted__xtor();
  if ((local_66 & 0x80) == 0) {
    FUN_00af14b0();
  }
  FUN_00a8fd30(local_6c);
  iVar2 = FUN_00a85620();
  uVar3 = FUN_00afdf70(0x37,iVar2);
  iVar4 = FUN_00b07340(local_6c,uVar3,iVar2);
  if (iVar4 == iVar2) {
    FUN_00a8a1d0();
    local_64[0] = BHG::MemoryDataWalk::vftable;
    local_44 = 0x1a;
    local_50 = 0;
    local_48 = 0;
    local_4c = 0;
    local_42 = 0xffff;
    FUN_00a87550();
    FUN_00a92ba0(uVar3,iVar2,0);
    iVar5 = (iVar5 + -1) * 0x20 + *(int *)(param_1 + 0x1e4);
    FUN_00e081e0(iVar5,local_64);
    uVar1 = *(uint *)(iVar5 + 4);
    if (*(uint *)(iVar5 + 0x14) < uVar1) {
      FUN_00dea6f0(uVar1 - 1);
    }
    else {
      *(uint *)(iVar5 + 0x14) = uVar1;
    }
    FUN_00afe180(0x37,uVar3);
    local_64[0] = BHG::MemoryDataWalk::vftable;
    FUN_00a87560();
    if (local_50 != 0) {
      FUN_00afe180((int)local_44,local_50);
    }
    local_50 = 0;
    local_48 = 0;
    local_4c = 0;
    local_42 = 0xffff;
  }
  else {
    FUN_00afe180(0x37,uVar3);
  }
  BHG_File__xtor();
  FUN_00af2060();
  return;
}

