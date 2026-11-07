// 00e1c000 FUN_00e1c000

void __thiscall FUN_00e1c000(undefined4 *param_1,int *param_2)

{
  undefined4 uVar1;
  
  uVar1 = param_1[2];
  (**(code **)(*param_2 + 4))(param_1,4);
  FUN_00e1a8f0(uVar1,param_2,param_1 + 1,*param_1);
  return;
}

