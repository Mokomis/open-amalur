// 00e1c750 BHG_ConditionalExpressionTable__xtor

undefined4 * BHG_ConditionalExpressionTable__xtor(uint param_1)

{
  int iVar1;
  uint uVar2;
  undefined4 *puVar3;
  int extraout_ECX;
  int local_4;
  
  FUN_00de4f60(param_1,&local_4,&param_1);
  uVar2 = param_1;
  if ((local_4 != -1) && ((short)param_1 != -1)) {
    iVar1 = *(int *)(extraout_ECX + 0x1e4);
    puVar3 = (undefined4 *)FUN_00afdf70(0x37,0x10);
    if (puVar3 != (undefined4 *)0x0) {
      *puVar3 = BHG::ConditionalExpressionTable::vftable;
      puVar3[1] = 0;
      puVar3[2] = 0;
      puVar3[3] = 0x37;
    }
    *(undefined4 **)(*(int *)(local_4 * 0x20 + iVar1 + 0x10) + (uVar2 & 0xffff) * 4) = puVar3;
    return puVar3;
  }
  return (undefined4 *)0x0;
}


