// 00f6cd50 BHG_PartTarget__vf17

void __thiscall BHG_PartTarget__vf17(int param_1,uint *param_2)

{
  uint uVar1;
  uint uVar2;
  
  uVar1 = *param_2;
  if (uVar1 < 0xafaf37) {
    if (uVar1 != 0xafaf36) {
      if (uVar1 == 0x194c55) {
        uVar1 = *(uint *)(param_1 + 0x4c);
        uVar2 = 1;
        if (0 < (int)uVar1) {
          uVar2 = uVar1;
        }
        if (uVar2 < *(uint *)(param_1 + 0x48)) {
          if ((int)uVar1 < 1) {
            uVar1 = 1;
          }
          *(uint *)(param_1 + 0x48) = uVar1;
          if (-1 < *(int *)(param_1 + 0x98)) goto LAB_00f6cdec;
        }
        FUN_00f23ed0(1);
LAB_00f6cdec:
        FUN_00f6cb40();
        return;
      }
      if (uVar1 != 0x5d21d9) {
        return;
      }
      uVar1 = *(uint *)(param_1 + 0x68);
      if ((((int)uVar1 < 0) - 1 & uVar1) < *(uint *)(param_1 + 100)) {
        *(uint *)(param_1 + 100) = uVar1 & ((int)uVar1 < 0) - 1;
        if (-1 < *(int *)(param_1 + 0x9c)) {
          return;
        }
        FUN_00f23ed0(1);
        return;
      }
      goto LAB_00f6ce28;
    }
  }
  else if (uVar1 != 0x198f075) {
    if (uVar1 != 0x203d64a) {
      return;
    }
    if (*(uint *)(param_1 + 0x90) <= *(uint *)(param_1 + 0x3c)) {
      return;
    }
    FUN_00df7a80();
    return;
  }
  FUN_00f418a0();
LAB_00f6ce28:
  FUN_00f23ed0(1);
  return;
}


