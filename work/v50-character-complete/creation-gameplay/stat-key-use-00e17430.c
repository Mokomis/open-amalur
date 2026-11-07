// 00e17430 BHG_GamePlayer__vf15

void __thiscall BHG_GamePlayer__vf15(int param_1,undefined4 param_2)

{
  byte *pbVar1;
  int iVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  undefined1 *local_40;
  int local_3c;
  undefined **local_38;
  int local_34;
  undefined **local_30;
  int local_2c;
  undefined **local_28;
  int local_24;
  undefined **local_20;
  int local_1c;
  undefined **local_18;
  int local_14;
  undefined **local_10;
  int local_c;
  undefined **local_8;
  int local_4;
  
  iVar2 = FUN_00f23c10(*(undefined4 *)(param_1 + 0x1ec));
  if ((*(byte *)(iVar2 + 0x10c) & 1) != 0) {
    uVar4 = 0;
    FUN_00f23c10(*(undefined4 *)(param_1 + 0x1ec));
    FUN_00f91770(uVar4);
  }
  uVar4 = *(undefined4 *)(param_1 + 0x1ec);
  *(undefined4 *)(param_1 + 0x1ec) = param_2;
  FUN_00d977b0(param_2);
  *(uint *)(param_1 + 0x104) = *(uint *)(param_1 + 0x104) & 0xfffffffd;
  iVar2 = FUN_00f23c10(*(undefined4 *)(param_1 + 0x1ec));
  if ((*(byte *)(iVar2 + 0x10c) & 1) != 0) {
    uVar3 = 1;
    FUN_00f23c10(*(undefined4 *)(param_1 + 0x1ec));
    FUN_00f91770(uVar3);
    local_40 = &LAB_00ae1048;
    FUN_00e172a0(*(undefined4 *)(param_1 + 0x1ec),&local_40,1);
    local_40 = (undefined1 *)0x828e2a;
    FUN_00e172a0(*(undefined4 *)(param_1 + 0x1ec),&local_40,2);
    local_40 = (undefined1 *)0xaa73cc;
    FUN_00e172a0(*(undefined4 *)(param_1 + 0x1ec),&local_40,3);
    local_40 = (undefined1 *)0x7ef1ae;
    FUN_00e172a0(*(undefined4 *)(param_1 + 0x1ec),&local_40,4);
    local_10 = BHG::PartConstIndex::vftable;
    FUN_00f24ef0(*(undefined4 *)(param_1 + 0x1ec),8);
    local_10 = BHG::StatsConstIndex::vftable;
    if ((local_c != 0) && ((*(byte *)(local_c + 0x20) & 1) != 0)) {
      if (*(int *)(local_c + 0x28) == 0) {
        pbVar1 = (byte *)(*(int *)(DAT_019fb210 + 0xc) + 0x6c);
        *pbVar1 = *pbVar1 & 0xef;
      }
      else {
        pbVar1 = (byte *)(*(int *)(DAT_019fb210 + 0xc) + 0x6c);
        *pbVar1 = *pbVar1 | 0x10;
      }
    }
    local_18 = BHG::PartConstIndex::vftable;
    FUN_00f24ef0(*(undefined4 *)(param_1 + 0x1ec),0x10);
    local_18 = BHG::SenseMemoryIndex::vftable;
    if ((local_14 != 0) && ((*(byte *)(local_14 + 0x20) & 1) != 0)) {
      *(byte *)(local_14 + 0x188) = *(byte *)(local_14 + 0x188) | 2;
    }
    local_20 = BHG::PartConstIndex::vftable;
    FUN_00f24ef0(*(undefined4 *)(param_1 + 0x1ec),6);
    local_20 = BHG::LocationConstIndex::vftable;
    if ((local_1c != 0) && ((*(byte *)(local_1c + 0x20) & 1) != 0)) {
      *(undefined8 *)(param_1 + 0x23c) = *(undefined8 *)(local_1c + 0x24);
      *(undefined8 *)(param_1 + 0x244) = *(undefined8 *)(local_1c + 0x2c);
    }
    local_28 = BHG::PartConstIndex::vftable;
    FUN_00f24ef0(*(undefined4 *)(param_1 + 0x1ec),0x14);
    local_28 = BHG::BuffPartIndex::vftable;
    if ((local_24 != 0) && ((*(byte *)(local_24 + 0x20) & 1) != 0)) {
      local_40 = (undefined1 *)0x57bc72;
      local_3c = 0x194c55;
      FUN_00f5aca0(&local_3c,&local_40);
    }
    local_30 = BHG::PartConstIndex::vftable;
    FUN_00f24ef0(*(undefined4 *)(param_1 + 0x1ec),1);
    local_30 = BHG::TargetIndex::vftable;
    if ((local_2c != 0) && ((*(byte *)(local_2c + 0x20) & 1) != 0)) {
      iVar2 = *(int *)(local_2c + 0x4c);
      if (iVar2 < 1) {
        iVar2 = 1;
      }
      *(int *)(local_2c + 0x48) = iVar2;
    }
    local_38 = BHG::PartConstIndex::vftable;
    FUN_00f24ef0(*(undefined4 *)(param_1 + 0x1ec),7);
    local_38 = BHG::RenderingConstIndex::vftable;
    if (((local_34 != 0) && ((*(byte *)(local_34 + 0x20) & 1) != 0)) &&
       (local_40 = *(undefined1 **)(local_34 + 0x9c), 1 < (int)local_40)) {
      FUN_00c8ad60(&local_40);
      FUN_00ccc6c0(1);
      FUN_00ccc7a0(1);
      FUN_00f57e10(0,local_40);
    }
    local_38 = BHG::PartConstIndex::vftable;
    FUN_00ef71b0();
    local_30 = BHG::PartConstIndex::vftable;
    FUN_00ef71b0();
    local_28 = BHG::PartConstIndex::vftable;
    FUN_00ef71b0();
    local_20 = BHG::PartConstIndex::vftable;
    FUN_00ef71b0();
    local_18 = BHG::PartConstIndex::vftable;
    FUN_00ef71b0();
    local_10 = BHG::PartConstIndex::vftable;
    FUN_00ef71b0();
  }
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00f24ef0(uVar4,7);
  local_8 = BHG::RenderingConstIndex::vftable;
  if ((local_4 != 0) && ((*(byte *)(local_4 + 0x20) & 1) != 0)) {
    local_3c = *(int *)(local_4 + 0x9c);
    if (1 < local_3c) {
      FUN_00f57e90(0,local_3c);
      FUN_00c8ad60(&local_3c);
      FUN_00ccc940(1);
      FUN_00ccc730(1);
    }
  }
  local_8 = BHG::PartConstIndex::vftable;
  FUN_00ef71b0();
  return;
}


