// 00a8cbe0 FUN_00a8cbe0

void __thiscall FUN_00a8cbe0(int *param_1,uint *param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined4 *puVar5;
  
  iVar1 = *param_1;
  iVar2 = *(int *)(iVar1 + 0x48);
  iVar4 = 0;
  *param_2 = 0;
  if (0 < iVar2) {
    iVar3 = *(int *)(iVar1 + 0x84);
    puVar5 = *(undefined4 **)(iVar1 + 0x44);
    do {
      if (*(char *)(iVar3 + iVar4) != '\0') {
        *param_2 = *param_2 | 1 << ((byte)*puVar5 & 0x1f);
      }
      iVar4 = iVar4 + 1;
      puVar5 = puVar5 + 1;
    } while (iVar4 < iVar2);
  }
  return;
}


