// 00ef2ae0 BHG_PartStatsBlueprint__vf2

void __thiscall BHG_PartStatsBlueprint__vf2(int param_1,undefined4 param_2)

{
  *(undefined4 *)(param_1 + 4) = param_2;
  return;
}


// 00ef2af0 BHG_PartStatsBlueprint__vf3

undefined4 BHG_PartStatsBlueprint__vf3(void)

{
  return 8;
}


// 00ef2b00 BHG_PartStatsBlueprint__vf0

undefined4 * __thiscall BHG_PartStatsBlueprint__vf0(undefined4 *param_1,byte param_2)

{
  *param_1 = BHG::PartBlueprint::vftable;
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


// 00efc910 BHG_PartStatsBlueprint__xtor

void BHG_PartStatsBlueprint__xtor(undefined4 param_1,undefined4 param_2)

{
  undefined4 *puVar1;
  
  puVar1 = (undefined4 *)FUN_00afdf70(param_1,param_2);
  if (puVar1 != (undefined4 *)0x0) {
    *puVar1 = BHG::PartStatsBlueprint::vftable;
  }
  return;
}


// 00f1a8d0 BHG_PartStatsBlueprint__vf1

void __fastcall BHG_PartStatsBlueprint__vf1(int param_1)

{
  undefined4 *puVar1;
  undefined4 uVar2;
  int iVar3;
  uint uVar4;
  
  iVar3 = *(int *)(param_1 + 4);
  uVar2 = FUN_00a70b80(*(undefined4 *)(iVar3 + 0x14));
  *(undefined4 *)(iVar3 + 0x14) = uVar2;
  iVar3 = *(int *)(param_1 + 4);
  uVar2 = FUN_00a70b80(*(undefined4 *)(iVar3 + 0x18));
  *(undefined4 *)(iVar3 + 0x18) = uVar2;
  iVar3 = *(int *)(param_1 + 4);
  uVar2 = FUN_00a70b80(*(undefined4 *)(iVar3 + 0xc));
  *(undefined4 *)(iVar3 + 0xc) = uVar2;
  iVar3 = *(int *)(param_1 + 4);
  if (*(int *)(iVar3 + 0x50) != 0) {
    uVar4 = 0;
    do {
      puVar1 = (undefined4 *)(*(int *)(iVar3 + 0x4c) + uVar4 * 4);
      uVar2 = FUN_00a70b80(*puVar1);
      *puVar1 = uVar2;
      iVar3 = *(int *)(param_1 + 4);
      uVar4 = uVar4 + 1;
    } while (uVar4 < *(uint *)(iVar3 + 0x50));
  }
  return;
}


