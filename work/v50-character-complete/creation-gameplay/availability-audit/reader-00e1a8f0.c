// 00e1a8f0 FUN_00e1a8f0

void FUN_00e1a8f0(undefined4 param_1,int *param_2,int *param_3,int param_4)

{
  undefined2 *puVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  undefined1 local_c [12];
  
  if (param_4 != 0) {
    iVar3 = FUN_00e15330(param_1,0x28,param_4);
    *param_3 = iVar3;
    if (param_4 != 0) {
      iVar3 = 0;
      do {
        iVar2 = *param_3;
        FUN_00af0570();
        FUN_00a8b4f0(param_2,local_c);
        *(undefined1 *)(iVar2 + 0x18 + iVar3) = 0x23;
        puVar1 = (undefined2 *)(iVar2 + 0x1a + iVar3);
        (**(code **)(*param_2 + 4))(puVar1,2);
        uVar4 = FUN_00afdf70(0x1e,*puVar1);
        *(undefined4 *)(iVar2 + 0x20 + iVar3) = uVar4;
        (**(code **)(*param_2 + 4))(uVar4,*puVar1);
        FUN_00af2060();
        iVar3 = iVar3 + 0x28;
        param_4 = param_4 + -1;
      } while (param_4 != 0);
    }
  }
  return;
}

