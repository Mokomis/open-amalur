// 00c58570 FUN_00c58570

undefined4 FUN_00c58570(int *param_1,int param_2,uint *param_3,int param_4,int param_5)

{
  short sVar1;
  short sVar2;
  uint uVar3;
  short sVar4;
  int *piVar5;
  int iVar6;
  undefined4 uVar7;
  undefined *puVar8;
  uint uVar9;
  undefined4 *puVar10;
  undefined4 uVar11;
  int *piVar12;
  uint uVar13;
  int *piVar14;
  uint uStack_74;
  uint uStack_70;
  undefined4 local_68;
  int *piStack_64;
  undefined1 auStack_5c [4];
  undefined4 uStack_58;
  undefined4 uStack_54;
  int iStack_50;
  uint uStack_4c;
  undefined4 auStack_48 [3];
  int iStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  uint uStack_28;
  undefined1 auStack_20 [20];
  uint uStack_c;
  
  piVar12 = (int *)0x0;
  uVar13 = 0;
  local_68 = 0;
  if (*(int *)(param_2 + 0xc) == 0) {
    *param_3 = *param_3;
    return 0;
  }
  do {
    piVar5 = (int *)(**(code **)(*param_1 + 0x10))(param_1,piVar12);
    iVar6 = (**(code **)*piVar5)(piVar5,auStack_5c);
    if (iVar6 < 0) {
      FUN_01050e90("PlatformShader: Couldn\'t get constant buffer description!\n");
    }
    else if (iStack_50 == 0) {
      uVar7 = FUN_0103ae60(uStack_54,0);
      puVar8 = (undefined *)FUN_00af09a0(uStack_54,0,uVar7);
      if (&DAT_00e23fb3 < puVar8) {
        if (puVar8 == (undefined *)0xe6c43b) {
          uVar9 = 4;
        }
        else if (puVar8 == (undefined *)0x1d57b25) {
          uVar9 = 0x10;
        }
        else {
LAB_00c58620:
          uVar9 = 0;
        }
      }
      else if (puVar8 == &DAT_00e23fb3) {
        uVar9 = 8;
      }
      else if (puVar8 == &DAT_00afe7c0) {
        uVar9 = 1;
      }
      else {
        if (puVar8 != (undefined *)0xcbc8c5) goto LAB_00c58620;
        uVar9 = 2;
      }
      uVar13 = uVar13 | uVar9;
      if (uVar9 == 8) {
        local_68 = auStack_48[0];
        uStack_70 = 0;
        piVar14 = piVar5;
        if (uStack_4c != 0) {
          do {
            piVar12 = (int *)(**(code **)(*piVar14 + 4))(piVar14,uStack_70);
            piVar12 = (int *)(**(code **)(*piVar12 + 4))(piVar12);
            if (((piVar12 != (int *)0x0) &&
                (iVar6 = (**(code **)*piVar12)(piVar12,auStack_20), -1 < iVar6)) &&
               (uStack_74 = 0, uStack_c != 0)) {
              do {
                puVar10 = (undefined4 *)(**(code **)(*piVar12 + 4))(piVar12,uStack_74);
                iVar6 = (**(code **)*puVar10)(puVar10,auStack_48);
                uVar9 = uStack_28;
                if ((-1 < iVar6) &&
                   (uVar7 = (**(code **)(*piVar12 + 0xc))(piVar12,uStack_74), uVar3 = uStack_28,
                   *(int *)(param_5 + (uVar9 & 0xfffffffc)) == -1)) {
                  if ((iStack_3c == 1) || ((iStack_3c == 2 || (iStack_3c == 3)))) {
                    sVar4 = 4;
                  }
                  else {
                    sVar4 = 0;
                  }
                  sVar2 = (short)uStack_38;
                  sVar1 = (short)uStack_34;
                  uVar11 = FUN_0103ae60(uVar7);
                  uVar7 = FUN_00af09a0(uVar7,0,uVar11,0);
                  puVar10 = (undefined4 *)(param_4 + *(int *)(param_4 + 0x800) * 8);
                  uStack_58 = CONCAT22((short)uVar3,sVar4 * sVar2 * sVar1);
                  *(int *)(param_4 + 0x800) = *(int *)(param_4 + 0x800) + 1;
                  if (puVar10 != (undefined4 *)0x0) {
                    *puVar10 = uVar7;
                    puVar10[1] = uStack_58;
                  }
                }
                uStack_74 = uStack_74 + 1;
                piVar14 = piStack_64;
              } while (uStack_74 < uStack_c);
            }
            uStack_70 = uStack_70 + 1;
            piVar12 = piVar5;
          } while (uStack_70 < uStack_4c);
        }
      }
    }
    piVar12 = (int *)((int)piVar12 + 1);
    if (*(int **)(param_2 + 0xc) <= piVar12) {
      *param_3 = *param_3 | uVar13;
      return local_68;
    }
  } while( true );
}

