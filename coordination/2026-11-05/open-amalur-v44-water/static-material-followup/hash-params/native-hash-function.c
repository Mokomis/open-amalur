// 00af09a0 FUN_00af09a0

int FUN_00af09a0(int param_1,int param_2,int param_3,int param_4)

{
  uint uVar1;
  int iVar2;
  
  if (param_1 != 0) {
    iVar2 = param_3 + -1;
    if (-1 < iVar2) {
      do {
        uVar1 = _tolower((int)*(char *)(param_1 + param_2 + iVar2));
        param_4 = param_4 + *(int *)(&DAT_01721040 + (iVar2 % 0x32) * 4) * uVar1 +
                  *(int *)(&DAT_01721040 + (uVar1 % 0x32) * 4) * param_3;
        param_3 = param_3 + -1;
        iVar2 = iVar2 + -1;
      } while (-1 < iVar2);
    }
    return param_4;
  }
  return 0;
}

