// 00dd9a10 FUN_00dd9a10

void __fastcall FUN_00dd9a10(int param_1)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  uint uVar5;
  int iVar6;
  undefined4 uVar7;
  uint local_1c;
  
  uVar7 = 1;
  uVar4 = FUN_00af4d70("bundles\\start_up_conditional_expression_tables.bundle",0xbecaa16,0xbecaa16,
                       1);
  FUN_00a9e230(0x26,uVar4,uVar7);
  FUN_00af2060();
  FUN_01045430(0);
  local_1c = 0;
  if (*(int *)(param_1 + 0x194) != 0) {
    do {
      piVar1 = *(int **)(*(int *)(param_1 + 400) + local_1c * 4);
      if (((char)piVar1[6] != '#') && ((char)piVar1[6] == '\x02')) {
        iVar6 = piVar1[7];
        FUN_00ab47e0(iVar6);
        FUN_00aa07c0(iVar6);
        uVar5 = 0;
        piVar1[7] = -2;
        *(undefined1 *)(piVar1 + 6) = 0x23;
        if (piVar1[1] != 0) {
          do {
            iVar6 = uVar5 * 4;
            uVar4 = FUN_00a6fe10();
            FUN_00a6c280();
            iVar2 = *piVar1;
            iVar3 = *(int *)(iVar2 + iVar6);
            if (1 < iVar3) {
              (**(code **)(*DAT_019f4d34 + 0xa8))(iVar3);
            }
            *(undefined4 *)(iVar2 + iVar6) = 0;
            uVar5 = uVar5 + 1;
            *(undefined4 *)(*piVar1 + iVar6) = uVar4;
          } while (uVar5 < (uint)piVar1[1]);
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

