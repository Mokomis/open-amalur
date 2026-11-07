// 00ce1360 BHG_SceneMgr__xtor

/* WARNING: Removing unreachable block (ram,0x00ce139d) */

void __fastcall BHG_SceneMgr__xtor(undefined4 *param_1)

{
  int *piVar1;
  
  piVar1 = param_1 + 1;
  *param_1 = BHG::SceneMgr::vftable;
  FUN_00c82330();
  if (*piVar1 != 0) {
    FUN_00afe180((int)*(short *)(param_1 + 4),*piVar1);
  }
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  *piVar1 = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *piVar1 = 0;
  param_1[3] = 0;
  param_1[2] = 0;
  *(undefined2 *)((int)param_1 + 0x12) = 0xffff;
  DAT_019fdff0 = 0;
  return;
}


// 00ce13d0 BHG_SceneMgr__vf0

undefined4 __thiscall BHG_SceneMgr__vf0(undefined4 param_1,byte param_2)

{
  BHG_SceneMgr__xtor();
  if ((param_2 & 1) != 0) {
    FUN_00aff1f0(param_1);
  }
  return param_1;
}


