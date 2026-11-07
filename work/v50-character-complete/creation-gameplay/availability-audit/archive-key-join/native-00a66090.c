// 00a66090 keen_koa_Application__vf7

void __thiscall keen_koa_Application__vf7(int param_1,undefined4 param_2)

{
  char cVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  int extraout_EDX;
  
  if (*(char *)(param_1 + 0x695) == '\0') {
    FUN_00a65bb0(param_2);
    if (*(char *)(param_1 + 0x695) != '\0') {
      FUN_010369a0();
      FUN_00afbaf0();
      return;
    }
  }
  else {
    uVar2 = FUN_010734a0(*(undefined4 *)(param_1 + 0x6c));
    FUN_0105a310(uVar2);
    FUN_00afbad0(param_2);
    if (*(char *)(param_1 + 0x694) == '\0') {
      uVar3 = FUN_01073650(*(undefined4 *)(param_1 + 0x6c),0,0);
      cVar1 = FUN_010783f0(uVar3);
      if (cVar1 != '\0') {
        uVar3 = FUN_01073480(*(undefined4 *)(param_1 + 0x6c));
        FUN_01054d20(uVar3,"/gamebuild","/data/data_0.pak",0);
        if (extraout_EDX != 0) {
          FUN_00a63810("/data/data_0.pak",extraout_EDX);
        }
        *(undefined1 *)(param_1 + 0x694) = 1;
      }
    }
    FUN_01045430(0);
    FUN_011acc30(*(undefined4 *)(param_1 + 0x70),*(undefined4 *)(param_1 + 0x18));
    FUN_01036bf0();
    cVar1 = FUN_01074730();
    FUN_00a74850(cVar1 == '\0');
    cVar1 = FUN_01074730();
    FUN_00a74ab0(cVar1 == '\0');
    FUN_00a74cf0();
    FUN_00afbab0();
    FUN_00afbaf0();
    FUN_0105a300(uVar2);
  }
  return;
}

