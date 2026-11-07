// 00a67490 FUN_00a67490

void __fastcall FUN_00a67490(int param_1)

{
  bool bVar1;
  uint *puVar2;
  undefined4 uVar3;
  int iVar4;
  undefined4 uVar5;
  int *piVar6;
  undefined8 uVar7;
  undefined1 local_48 [4];
  undefined1 auStack_44 [63];
  undefined1 uStack_5;
  uint local_4;
  
  local_4 = DAT_0197713c ^ (uint)local_48;
  bVar1 = false;
  puVar2 = (uint *)FUN_00a8cba0(local_48);
  if ((*puVar2 >> 0xc & 1) != 0) {
    puVar2 = (uint *)FUN_00a8cbe0(local_48);
    if ((*puVar2 >> 0xc & 1) != 0) {
      bVar1 = true;
    }
  }
  uVar3 = FUN_01073480(*(undefined4 *)(param_1 + 0x6c));
  if (bVar1) {
    if (((*(int *)(param_1 + 0xc) == -1) && (*(int *)(param_1 + 0x10) == -1)) &&
       (*(int *)(param_1 + 0x14) == -1)) {
      iVar4 = FUN_01078af0(*(undefined4 *)(param_1 + 0x68),0,uVar3,"dlcdata");
      if (iVar4 != 0) {
        FUN_00a63810("/dlcdata",1);
      }
      if (*(int *)(param_1 + 0xc) == -1) {
        uVar7 = FUN_01054d20(uVar3,"/gamebuild","/dlcdata/dlc_mit_0.pak",0xffffffff);
        iVar4 = (int)((ulonglong)uVar7 >> 0x20);
        uVar5 = (undefined4)uVar7;
        if ((iVar4 != 0) && (iVar4 != 9)) {
          uVar5 = FUN_00a63810("/dlcdata/dlc_mit_0.pak",iVar4);
        }
        *(undefined4 *)(param_1 + 0xc) = uVar5;
      }
      if (*(int *)(param_1 + 0x10) == -1) {
        uVar7 = FUN_01054d20(uVar3,"/sound","/dlcdata/dlc_mit_0.pak",0);
        iVar4 = (int)((ulonglong)uVar7 >> 0x20);
        uVar5 = (undefined4)uVar7;
        if ((iVar4 != 0) && (iVar4 != 9)) {
          uVar5 = FUN_00a63810("/dlcdata/dlc_mit_0.pak",iVar4);
        }
        *(undefined4 *)(param_1 + 0x10) = uVar5;
      }
      if (*(int *)(param_1 + 0x14) == -1) {
        uVar7 = FUN_01051b40(uVar3,"/videos","dlcdata/videos",0);
        iVar4 = (int)((ulonglong)uVar7 >> 0x20);
        uVar5 = (undefined4)uVar7;
        if ((iVar4 != 0) && (iVar4 != 9)) {
          uVar5 = FUN_00a63810("/dlcdata/videos",iVar4);
        }
        *(undefined4 *)(param_1 + 0x14) = uVar5;
      }
      uVar7 = FUN_0104bf80(uVar3,"/gamebuild/dlc.version",0);
      if ((int)((ulonglong)uVar7 >> 0x20) == 0) {
        _memset(auStack_44,0,0x40);
        FUN_01040d90(uVar3,(int)uVar7,auStack_44,0x40);
        uStack_5 = 0;
        FUN_0103b1d0(auStack_44,&DAT_017146dc,0);
        FUN_01050e90("Mounted Fatesworn DLC with version \'%s\'\n",auStack_44);
        FUN_01040d50(uVar3,(int)uVar7);
        __security_check_cookie(local_4 ^ (uint)local_48);
        return;
      }
      FUN_01050e90("Unable to read DLC version, disabling dlc.\n");
      FUN_00a8faa0(0xc);
      __security_check_cookie(local_4 ^ (uint)local_48);
      return;
    }
  }
  else {
    FUN_01050e90("DLC not licensed, unmounting.\n");
    piVar6 = (int *)(param_1 + 0xc);
    iVar4 = 3;
    do {
      if (*piVar6 != -1) {
        FUN_0104be40(uVar3,*piVar6);
        *piVar6 = -1;
      }
      piVar6 = piVar6 + 1;
      iVar4 = iVar4 + -1;
    } while (iVar4 != 0);
  }
  __security_check_cookie(local_4 ^ (uint)local_48);
  return;
}

