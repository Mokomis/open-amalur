// 00f6ce40 FUN_00f6ce40

void __thiscall FUN_00f6ce40(int param_1,char param_2)

{
  undefined4 uVar1;
  char cVar2;
  int iVar3;
  undefined4 *puVar4;
  float10 fVar5;
  undefined4 local_14;
  undefined **local_10;
  int local_c;
  undefined **local_8;
  int local_4;
  
  uVar1 = *(undefined4 *)(param_1 + 0x18);
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(uVar1,8);
  local_10 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(uVar1,0x14);
  if ((((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) && (local_c != 0)) &&
     ((*(byte *)(local_c + 0x20) & 1) != 0)) {
    iVar3 = FUN_00f23c10(*(undefined4 *)(param_1 + 0x18));
    if ((*(byte *)(iVar3 + 0x10c) >> 1 & 1) == 0) {
      FUN_00e2cbd0();
      FUN_00e2c9e0(1);
      puVar4 = (undefined4 *)FUN_00dbacb0(&local_10,0);
      cVar2 = FUN_00f50a30(*puVar4);
      if (cVar2 == '\0') {
        fVar5 = (float10)FUN_00ff9ca0();
      }
      else {
        fVar5 = (float10)FUN_00ff9d00();
      }
      FUN_00e2ca80((float)fVar5);
      uVar1 = *(undefined4 *)(param_1 + 0x48);
      local_14 = 0x57bc72;
      local_10 = (undefined **)0x194c55;
      FUN_00f5aca0(&local_10,&local_14);
      local_10 = (undefined **)0x57bc72;
      local_14 = 0x194c55;
      FUN_00f682e0(&local_14,&local_8,&local_10,1);
      if (param_2 == '\0') {
        iVar3 = *(int *)(param_1 + 0x4c);
        if (iVar3 < 1) {
          iVar3 = 1;
        }
        *(int *)(param_1 + 0x48) = iVar3;
        FUN_00e2cbe0();
        return;
      }
      *(undefined4 *)(param_1 + 0x48) = uVar1;
      FUN_00e2cbe0();
    }
  }
  return;
}


