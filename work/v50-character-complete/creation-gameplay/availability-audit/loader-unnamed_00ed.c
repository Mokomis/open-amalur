// 00edb430 FUN_00edb430

undefined4 __fastcall FUN_00edb430(int *param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  
  FUN_00ec6670();
  if (*param_1 != 0) {
    FUN_00afe180((int)(short)param_1[3],*param_1);
  }
  uVar2 = 2;
  *param_1 = 0;
  param_1[2] = 0;
  param_1[1] = 0;
  *(undefined2 *)((int)param_1 + 0xe) = 0xffff;
  uVar1 = FUN_00af4d70("all_worksheets.all_excel_workbooks",0x4c11b2f,0x4c11b2f,1);
  FUN_00ed6660(0xb97f12,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("world_map_data.bxml",&DAT_016c961b,&DAT_016c961b,1);
  FUN_00ed6660(0x4292de,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("SpaceMgr.bin",0x82c14d,0x82cc6b,1);
  FUN_00ed6660(0x8c0e64,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("dlcdestinations.koadlcdestinationslist",0x5e6d95e,0x5e6d95e,1);
  FUN_00ed6660(&DAT_00c53ee4,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("GlobalObjectReferenceDestinationMgr.bin",0x6271b86,0x63429c6,1);
  FUN_00ed6660(0xe7bea,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("QuestMgr.bin",0x7d3ddb,0x7d4b9d,1);
  FUN_00ed6660(0x868d96,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 1;
  uVar1 = FUN_00af4d70("BuffMgr.bin",&LAB_00686d06,0x6941e2,1);
  FUN_00ed6660(0x70bf65,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("behaviormgr.bin",&LAB_00c816c5,&LAB_00c816c5,1);
  FUN_00ed6660(&LAB_00d3479c,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("FastTravelLocationMgr.bin",0x260c2fb,0x264333b,1);
  FUN_00ed6660(&DAT_01577e08,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 1;
  uVar1 = FUN_00af4d70("PlayerCustomizationData.bin",0x2e19031,0x2ef30ad,1);
  FUN_00ed6660(0x2144866,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("SpaceGraph.bin",&LAB_00b58d60,&LAB_00b5b822,1);
  FUN_00ed6660(&DAT_00c0885f,uVar1,uVar2);
  FUN_00af2060();
  uVar2 = 2;
  uVar1 = FUN_00af4d70("SpaceGraphDlcOwnership.bin",0x28605de,0x2890906,1);
  FUN_00ed6660(0x1d33e13,uVar1,uVar2);
  FUN_00af2060();
  return 0;
}

