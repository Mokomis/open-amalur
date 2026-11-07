// 00dd9880 FUN_00dd9880

void __fastcall FUN_00dd9880(int param_1)

{
  ushort uVar1;
  int *piVar2;
  undefined4 uVar3;
  int iVar4;
  uint uVar5;
  int iVar6;
  uint uVar7;
  char *pcVar8;
  undefined1 *puVar9;
  uint local_1c;
  undefined1 local_c [12];
  
  uVar3 = FUN_00af4d70("bundles\\start_up_conditional_expression_tables.bundle",0xbecaa16,0xbecaa16,
                       1);
  FUN_00a94410(0x26,uVar3);
  FUN_00af2060();
  FUN_01045430(0);
  local_1c = 0;
  if (*(int *)(param_1 + 0x194) != 0) {
    do {
      piVar2 = *(int **)(*(int *)(param_1 + 400) + local_1c * 4);
      if ((char)piVar2[6] == '#') {
        pcVar8 = (char *)piVar2[8];
        uVar1 = *(ushort *)((int)piVar2 + 0x1a);
        uVar5 = (uint)uVar1;
        uVar7 = 0;
        if (piVar2[1] != 0) {
          do {
            iVar6 = *piVar2;
            iVar4 = FUN_00a70b80(*(undefined4 *)(iVar6 + uVar7 * 4));
            *(int *)(iVar6 + uVar7 * 4) = iVar4;
            if (1 < iVar4) {
              (**(code **)(*DAT_019f4d34 + 0xa4))(iVar4);
            }
            uVar7 = uVar7 + 1;
          } while (uVar7 < (uint)piVar2[1]);
        }
        if (*pcVar8 == '\x02') {
          FUN_00af4d40(&DAT_01742bf0);
          puVar9 = local_c;
          iVar6 = uVar5 - 5;
          pcVar8 = pcVar8 + 5;
          FUN_00ab47e0(pcVar8,iVar6,puVar9);
          iVar6 = FUN_00aa6890(pcVar8,iVar6,puVar9);
          FUN_00af2060();
          if (iVar6 == 0) {
            FUN_00ab47e0();
            iVar6 = FUN_00aa3b60();
            *(undefined1 *)(piVar2 + 6) = 2;
            piVar2[7] = iVar6;
          }
          else {
            *(undefined1 *)(piVar2 + 6) = 1;
          }
        }
        else if (uVar5 < 9) {
          FUN_00afca30(piVar2 + 6,pcVar8,uVar5);
        }
        else {
          *(undefined1 *)(piVar2 + 6) = 3;
          *(ushort *)((int)piVar2 + 0x1a) = uVar1;
          piVar2[8] = (int)pcVar8;
        }
      }
      local_1c = local_1c + 1;
    } while (local_1c < *(uint *)(param_1 + 0x194));
  }
  if (param_1 == -0x19c) {
    return;
  }
  FUN_01036bf0();
  return;
}

