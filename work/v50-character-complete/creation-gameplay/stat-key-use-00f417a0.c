// 00f417a0 BHG_PartTalent__vf17

void __thiscall BHG_PartTalent__vf17(int param_1,undefined4 *param_2)

{
  undefined *puVar1;
  uint uVar2;
  undefined4 uVar3;
  
  puVar1 = (undefined *)*param_2;
  if (puVar1 < (undefined *)0x72d624) {
    if ((puVar1 != (undefined *)0x72d623) && (puVar1 != (undefined *)0xefbb2)) {
      if (puVar1 != (undefined *)0x3fe1bf) {
        return;
      }
      uVar2 = *(uint *)(param_1 + 0x7c);
      if ((((int)uVar2 < 0) - 1 & uVar2) <= *(uint *)(param_1 + 0x84)) {
        return;
      }
      *(uint *)(param_1 + 0x84) = uVar2 & ((int)uVar2 < 0) - 1;
      return;
    }
    uVar2 = FUN_00f00960();
    if (uVar2 < *(uint *)(param_1 + 0x84)) {
      uVar3 = FUN_00f00960();
      *(undefined4 *)(param_1 + 0x84) = uVar3;
      if (-1 < *(int *)(param_1 + 0xa0)) {
        return;
      }
      FUN_00f23ed0(1);
      return;
    }
  }
  else {
    if ((puVar1 != (undefined *)0x96407b) && (puVar1 != &DAT_01709970)) {
      return;
    }
    FUN_00f411b0();
  }
  FUN_00f23ed0(1);
  return;
}


