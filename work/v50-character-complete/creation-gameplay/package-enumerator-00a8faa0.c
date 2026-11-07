// 00a8faa0 FUN_00a8faa0

void __thiscall FUN_00a8faa0(int *param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  
  iVar1 = *param_1;
  iVar2 = 0;
  if (0 < *(int *)(iVar1 + 0x48)) {
    piVar3 = *(int **)(iVar1 + 0x44);
    while (*piVar3 != param_2) {
      iVar2 = iVar2 + 1;
      piVar3 = piVar3 + 1;
      if (*(int *)(iVar1 + 0x48) <= iVar2) {
        return;
      }
    }
    *(undefined1 *)(iVar2 + *(int *)(iVar1 + 0x84)) = 0;
  }
  return;
}


