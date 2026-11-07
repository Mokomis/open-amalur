// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\BHG_TerrainObject.c
// 00d46f60 BHG_TerrainObject__vf3

undefined4 __thiscall BHG_TerrainObject__vf3(int param_1,undefined4 param_2,int param_3)

{
  int iVar1;
  undefined4 *puVar2;
  undefined4 uVar3;
  int unaff_EBP;
  int unaff_EDI;
  undefined **ppuStack_ac;
  undefined4 uStack_a8;
  int aiStack_a4 [3];
  int iStack_98;
  int iStack_94;
  undefined4 uStack_90;
  int iStack_8c;
  int *piStack_88;
  int iStack_84;
  undefined4 uStack_80;
  int iStack_7c;
  undefined4 uStack_78;
  int iStack_74;
  undefined4 uStack_70;
  int iStack_6c;
  undefined4 uStack_68;
  float *pfStack_64;
  undefined4 uStack_60;
  int iStack_5c;
  undefined4 uStack_58;
  int iStack_54;
  undefined4 uStack_50;
  int iStack_4c;
  undefined4 uStack_48;
  int iStack_44;
  undefined4 uStack_40;
  int iStack_3c;
  int iStack_38;
  
  iStack_38 = 0xd46f74;
  FUN_00d45e00();
  iStack_38 = 0xd46f7f;
  FUN_00cec950();
  *(int *)(param_1 + 0x27c) = param_1;
  iStack_38 = 0xd46fb6;
  FUN_00a87550();
  iStack_38 = param_3;
  iStack_3c = param_2;
  uStack_40 = 0xd46fc9;
  FUN_00a92bf0();
  iStack_38 = 4;
  iStack_3c = param_1 + 0x438;
  uStack_40 = 0xd46fdf;
  (*(code *)PTR_BHG_MemoryDataWalk__vf1_0172e47c)();
  uStack_40 = 4;
  iStack_44 = param_1 + 0x43c;
  uStack_48 = 0xd46ff5;
  (**(code **)(unaff_EBP + 4))();
  uStack_48 = 4;
  iStack_4c = param_1 + 0x440;
  uStack_50 = 0xd4700b;
  (**(code **)(unaff_EDI + 4))();
  uStack_50 = 4;
  iStack_54 = param_1 + 0x444;
  uStack_58 = 0xd47021;
  (**(code **)(iStack_3c + 4))();
  uStack_58 = 4;
  iStack_5c = param_1 + 0x448;
  uStack_60 = 0xd47037;
  (**(code **)(iStack_44 + 4))();
  uStack_60 = 4;
  uStack_68 = 0xd4704d;
  pfStack_64 = (float *)(param_1 + 0x44c);
  (**(code **)(iStack_4c + 4))();
  uStack_68 = 4;
  iStack_6c = param_1 + 0x450;
  uStack_70 = 0xd47063;
  (**(code **)(iStack_54 + 4))();
  iStack_74 = param_1 + 0x454;
  uStack_70 = 4;
  uStack_78 = 0xd47079;
  (**(code **)(iStack_5c + 4))();
  uStack_78 = 4;
  iStack_7c = param_1 + 0x458;
  uStack_80 = 0xd4708f;
  (*(code *)pfStack_64[1])();
  uStack_80 = 4;
  iStack_84 = param_1 + 0x45c;
  piStack_88 = (int *)0xd470a5;
  (**(code **)(iStack_6c + 4))();
  piStack_88 = &iStack_74;
  *(int *)(param_1 + 0x47c) = (int)(DAT_01740238 / (double)*(float *)(param_1 + 0x44c));
  iStack_8c = 0xd470ce;
  FUN_00c9d170();
  piStack_88 = (int *)0x4;
  iStack_8c = param_1 + 0x460;
  uStack_90 = 0xd470e4;
  (**(code **)(iStack_74 + 4))();
  uStack_90 = 4;
  iStack_94 = param_1 + 0x464;
  iStack_98 = 0xd470fa;
  (**(code **)(iStack_7c + 4))();
  iStack_98 = 4;
  aiStack_a4[2] = param_1 + 0x468;
  aiStack_a4[1] = 0xd47110;
  (**(code **)(iStack_84 + 4))();
  aiStack_a4[1] = 4;
  aiStack_a4[0] = param_1 + 0x46c;
  uStack_a8 = 0xd47126;
  (**(code **)(iStack_8c + 4))();
  uStack_68 = *(undefined4 *)(param_1 + 0x478);
  uStack_a8 = 4;
  ppuStack_ac = (undefined **)(param_1 + 0x470);
  (**(code **)(iStack_94 + 4))();
  FUN_00ca9e70(uStack_70,aiStack_a4 + 2,param_1 + 0x474,*(undefined **)(param_1 + 0x470));
  FUN_00d46dd0(aiStack_a4 + 2);
  FUN_00a8db50(aiStack_a4 + 2);
  uVar3 = *(undefined4 *)(param_1 + 0x370);
  (**(code **)(aiStack_a4[2] + 4))((undefined4 *)(param_1 + 0x368),4);
  FUN_00a467a0(uVar3,aiStack_a4,param_1 + 0x36c,*(undefined4 *)(param_1 + 0x368));
  uVar3 = *(undefined4 *)(param_1 + 0x37c);
  (**(code **)(aiStack_a4[0] + 4))((undefined4 *)(param_1 + 0x374),4);
  FUN_00a467a0(uVar3,&ppuStack_ac,param_1 + 0x378,*(undefined4 *)(param_1 + 0x374));
  iVar1 = FUN_00a875b0();
  param_3 = param_3 - iVar1;
  puVar2 = (undefined4 *)FUN_00afdf70(0x16,0x24);
  if (puVar2 != (undefined4 *)0x0) {
    *puVar2 = BHG::MemoryDataWalk::vftable;
    *(undefined2 *)((int)puVar2 + 0x22) = 0xffff;
    *(undefined2 *)(puVar2 + 8) = 0x1a;
    puVar2[5] = 0;
    puVar2[7] = 0;
    puVar2[6] = 0;
    FUN_00a87550();
  }
  *(undefined4 **)(param_1 + 0x484) = puVar2;
  uVar3 = FUN_00a875c0(param_3);
  FUN_00a92bf0(uVar3,param_3);
  ppuStack_ac = BHG::MemoryDataWalk::vftable;
  FUN_00a87560();
  if (iStack_98 != 0) {
    FUN_00afe180((int)(short)iStack_8c,iStack_98);
  }
  return 0;
}



// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00a4.c
// 00a467a0 FUN_00a467a0

void FUN_00a467a0(undefined4 param_1,int *param_2,int *param_3,int param_4)

{
  int iVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  int iVar4;
  int *piVar5;
  int local_4;
  
  local_4 = param_4;
  if (param_4 != 0) {
    puVar2 = (undefined4 *)FUN_00afdf70(param_1,param_4 * 0xc);
    puVar3 = puVar2;
    for (iVar4 = param_4; iVar4 != 0; iVar4 = iVar4 + -1) {
      if (puVar3 != (undefined4 *)0x0) {
        *puVar3 = 0;
        puVar3[1] = 0;
        puVar3[2] = param_1;
      }
      puVar3 = puVar3 + 3;
    }
    *param_3 = (int)puVar2;
    if (param_4 != 0) {
      param_4 = 0;
      do {
        piVar5 = (int *)(*param_3 + param_4);
        iVar4 = piVar5[2];
        (**(code **)(*param_2 + 4))(piVar5,4);
        if (*piVar5 != 0) {
          iVar1 = *piVar5 * 4;
          iVar4 = FUN_00afdf70(iVar4,iVar1);
          piVar5[1] = iVar4;
          (**(code **)(*param_2 + 4))(iVar4,iVar1);
        }
        param_4 = param_4 + 0xc;
        local_4 = local_4 + -1;
      } while (local_4 != 0);
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00a7.c
// 00a7edc0 FUN_00a7edc0

undefined4 __thiscall FUN_00a7edc0(int *param_1,int param_2,char param_3)

{
  int iVar1;
  
  if (param_3 == '\0') {
    if ((int)(param_2 + 7 + (param_2 + 7 >> 0x1f & 7U)) >> 3 == param_1[1]) {
      *param_1 = param_2;
      return 0;
    }
    if (*param_1 == param_2) goto LAB_00a7ee30;
  }
  if (param_1[4] != 0) {
    FUN_00afe180((int)(short)param_1[3],param_1[4]);
    param_1[4] = 0;
  }
  iVar1 = (int)(param_2 + 7 + (param_2 + 7 >> 0x1f & 7U)) >> 3;
  param_1[4] = 0;
  param_1[2] = 0;
  *param_1 = param_2;
  param_1[1] = iVar1;
  iVar1 = FUN_00afdf70((int)(short)param_1[3],iVar1);
  param_1[4] = iVar1;
LAB_00a7ee30:
  if (param_1[4] != 0) {
    FUN_00afca50(param_1[4],0,param_1[1]);
    param_1[2] = 0;
  }
  return 0;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00a8.c
// 00a8db50 FUN_00a8db50

void __thiscall FUN_00a8db50(int param_1,int *param_2)

{
  int iVar1;
  int *piVar2;
  int iVar3;
  
  piVar2 = param_2;
  (**(code **)(*param_2 + 4))(&param_2,4);
  (**(code **)(*piVar2 + 4))((int *)(param_1 + 0x54),0x14);
  iVar1 = *(int *)(param_1 + 0x54);
  *(int *)(param_1 + 0x74) = iVar1;
  *(undefined4 *)(param_1 + 0x6c) = 0;
  *(int *)(param_1 + 0x68) = (1 << ((byte)iVar1 & 0x1f)) + -1;
  iVar3 = iVar1 + *(int *)(param_1 + 0x5c);
  *(int *)(param_1 + 0x7c) = iVar3;
  *(int *)(param_1 + 0x70) =
       (1 << ((byte)*(int *)(param_1 + 0x5c) & 0x1f)) + -1 << ((byte)iVar1 & 0x1f);
  *(int *)(param_1 + 0x78) =
       (1 << ((byte)*(undefined4 *)(param_1 + 100) & 0x1f)) + -1 << ((byte)iVar3 & 0x1f);
  *(uint *)(param_1 + 0x80) = ~(*(int *)(param_1 + 0x60) - 1U);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00a8.c
// 00a876d0 FUN_00a876d0

int __thiscall FUN_00a876d0(int param_1,uint param_2)

{
  return ((*(uint *)(param_1 + 0x68) & param_2) >> ((byte)*(undefined4 *)(param_1 + 0x6c) & 0x1f)) *
         *(int *)(param_1 + 0x58);
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00a8.c
// 00a876f0 FUN_00a876f0

uint __thiscall FUN_00a876f0(int param_1,uint param_2)

{
  return (*(uint *)(param_1 + 0x78) & param_2) >> ((byte)*(undefined4 *)(param_1 + 0x7c) & 0x1f);
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00a9.c
// 00a92d10 FUN_00a92d10

uint __thiscall FUN_00a92d10(int param_1,uint param_2)

{
  uint uVar1;
  int iVar2;
  uint uVar3;
  
  iVar2 = ((*(uint *)(param_1 + 0x68) & param_2) >> ((byte)*(undefined4 *)(param_1 + 0x6c) & 0x1f))
          * *(int *)(param_1 + 0x58);
  uVar3 = (((*(uint *)(param_1 + 0x70) & param_2) >> ((byte)*(undefined4 *)(param_1 + 0x74) & 0x1f))
           * *(int *)(param_1 + 0x60) + iVar2 & *(uint *)(param_1 + 0x80)) - iVar2;
  if (*(int *)(param_1 + 0x50) == -1) {
    if ((*(int *)(param_1 + 0xc) == 0) && (*(int *)(param_1 + 0x10) == 0)) {
      if (*(int *)(param_1 + 0x4c) == -1) {
        if ((*(byte *)(param_1 + 0x4a) & 0x80) == 0) {
          FUN_00af14b0();
        }
        FUN_00a8fda0(*(undefined4 *)(param_1 + 0x44));
      }
      else {
        FUN_00a8fda0(*(int *)(param_1 + 0x4c));
      }
    }
    if (*(int *)(param_1 + 0x50) == -1) {
      *(undefined4 *)(param_1 + 0x50) = *(undefined4 *)(param_1 + 0x18);
    }
    FUN_00a8a1d0();
  }
  uVar1 = *(int *)(param_1 + 0x50) - iVar2;
  if (uVar3 < uVar1) {
    uVar1 = uVar3;
  }
  return uVar1;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00ca.c
// 00ca9e70 FUN_00ca9e70

void FUN_00ca9e70(undefined4 param_1,int *param_2,int *param_3,int param_4)

{
  int iVar1;
  undefined4 *puVar2;
  
  if (param_4 != 0) {
    iVar1 = FUN_00c85ea0(param_1,param_4);
    *param_3 = iVar1;
    if (param_4 != 0) {
      iVar1 = 0;
      do {
        puVar2 = (undefined4 *)(*param_3 + iVar1);
        (**(code **)(*param_2 + 4))(puVar2,4);
        FUN_00a7edc0(*puVar2,1);
        (**(code **)(*param_2 + 4))(puVar2 + 2,4);
        if (puVar2[1] != 0) {
          (**(code **)(*param_2 + 4))(puVar2[4],puVar2[1]);
        }
        iVar1 = iVar1 + 0x14;
        param_4 = param_4 + -1;
      } while (param_4 != 0);
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00cb.c
// 00cbb4c0 FUN_00cbb4c0

void __thiscall FUN_00cbb4c0(int param_1,int param_2,int param_3,int param_4,char param_5)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  undefined4 uVar6;
  int iVar7;
  float fVar8;
  
  iVar1 = param_3;
  if (param_5 == '\0') {
    iVar7 = *(int *)(*(int *)(param_2 + 0x48) + param_4 * 4);
  }
  else {
    iVar7 = -1;
  }
  fVar8 = (float)((double)*(int *)(param_1 + 0xd4) / DAT_014c95b8);
  iVar2 = FUN_00a71e80(*(undefined4 *)(param_1 + 4),1);
  if (param_5 == '\0') {
    iVar4 = *(int *)(*(int *)(param_2 + 0x48) + param_4 * 4) * 0x10;
    iVar3 = *(int *)(*(int *)(*(int *)(iVar2 + 4) + 8) + 8 + iVar4) + -1;
    iVar5 = 0;
    if (iVar3 < 1) {
      iVar5 = iVar3;
    }
    *(float *)(param_3 + 0x14) =
         *(float *)(**(int **)(iVar2 + 4) + 0xc +
                   *(int *)(*(int *)(iVar4 + 4 + (*(int **)(iVar2 + 4))[2]) + iVar5 * 4) * 0x1c) *
         fVar8;
    iVar3 = *(int *)(*(int *)(param_2 + 0x48) + param_4 * 4) * 0x10;
    iVar5 = *(int *)(*(int *)(*(int *)(iVar2 + 4) + 8) + 8 + iVar3) + -1;
    param_3 = 1;
    if (iVar5 < 2) {
      param_3 = iVar5;
    }
    *(float *)(iVar1 + 0x18) =
         *(float *)(**(int **)(iVar2 + 4) + 0xc +
                   *(int *)(*(int *)(iVar3 + 4 + (*(int **)(iVar2 + 4))[2]) + param_3 * 4) * 0x1c) *
         fVar8;
    iVar3 = *(int *)(*(int *)(param_2 + 0x48) + param_4 * 4) * 0x10;
    iVar5 = *(int *)(*(int *)(*(int *)(iVar2 + 4) + 8) + 8 + iVar3) + -1;
    param_3 = 2;
    if (iVar5 < 3) {
      param_3 = iVar5;
    }
    *(float *)(iVar1 + 0x1c) =
         *(float *)(**(int **)(iVar2 + 4) + 0xc +
                   *(int *)(*(int *)(iVar3 + 4 + (*(int **)(iVar2 + 4))[2]) + param_3 * 4) * 0x1c) *
         fVar8;
    iVar4 = *(int *)(*(int *)(param_2 + 0x48) + param_4 * 4) * 0x10;
    iVar3 = *(int *)(*(int *)(*(int *)(iVar2 + 4) + 8) + 8 + iVar4) + -1;
    iVar5 = 3;
    if (iVar3 < 4) {
      iVar5 = iVar3;
    }
    *(float *)(iVar1 + 0x20) =
         *(float *)(**(int **)(iVar2 + 4) + 0xc +
                   *(int *)(*(int *)(iVar4 + 4 + (*(int **)(iVar2 + 4))[2]) + iVar5 * 4) * 0x1c) *
         fVar8;
    uVar6 = *(undefined4 *)(*(int *)(*(int *)(iVar2 + 4) + 8) + 0xc + iVar7 * 0x10);
  }
  else {
    uVar6 = *(undefined4 *)(*(int *)(DAT_019fdfa0 + 0xb8) + *(int *)(DAT_019fdffc + 0x90) * 8);
  }
  *(undefined4 *)(iVar1 + 0x30) = uVar6;
  *(undefined2 *)(iVar1 + 0x24) = *(undefined2 *)(param_2 + 0x40);
  *(undefined2 *)(iVar1 + 0x26) = *(undefined2 *)(param_2 + 0x42);
  *(undefined2 *)(iVar1 + 0x2a) = *(undefined2 *)(param_2 + 0x46);
  *(undefined2 *)(iVar1 + 0x28) = *(undefined2 *)(param_2 + 0x44);
  *(char *)(iVar1 + 0x58) = param_5;
  *(int *)(iVar1 + 0x2c) = iVar7;
  iVar7 = 0;
  do {
    if (*(char *)(iVar1 + 0x58) == '\0') {
      iVar4 = *(int *)(*(int *)(iVar2 + 4) + 8) + *(int *)(iVar1 + 0x2c) * 0x10;
      iVar3 = *(int *)(iVar4 + 8) + -1;
      iVar5 = iVar7;
      if (iVar3 <= iVar7) {
        iVar5 = iVar3;
      }
      *(undefined1 *)(iVar1 + 0x59 + iVar7) = *(undefined1 *)(*(int *)(iVar4 + 4) + iVar5 * 4);
    }
    else {
      *(undefined1 *)(iVar1 + 0x59 + iVar7) = 0xff;
    }
    iVar7 = iVar7 + 1;
  } while (iVar7 < 4);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00cc.c
// 00cc6800 FUN_00cc6800

void FUN_00cc6800(undefined4 param_1,int *param_2)

{
  int *piVar1;
  uint uVar2;
  undefined4 uVar3;
  uint uVar4;
  undefined4 *unaff_EBX;
  uint unaff_retaddr;
  
  piVar1 = param_2;
  (**(code **)(*param_2 + 4))(&param_2,4);
  if ((uint)unaff_EBX[1] < unaff_retaddr) {
    uVar4 = unaff_EBX[2];
    if ((uVar4 < unaff_retaddr) && (uVar2 = unaff_retaddr - uVar4, 0 < (int)uVar2)) {
      if (-1 < *(short *)((int)unaff_EBX + 0xe)) {
        uVar4 = (uint)*(short *)((int)unaff_EBX + 0xe);
      }
      if ((int)uVar2 <= (int)uVar4) {
        uVar2 = uVar4;
      }
      FUN_00a67820(uVar2);
    }
    uVar4 = unaff_EBX[1];
    if ((uint)unaff_EBX[1] < unaff_retaddr) {
      uVar4 = unaff_retaddr;
    }
    unaff_EBX[1] = uVar4;
  }
  else {
    unaff_EBX[1] = unaff_retaddr;
  }
  uVar3 = 0;
  if (0 < (int)unaff_EBX[1]) {
    uVar3 = *unaff_EBX;
  }
  (**(code **)(*piVar1 + 4))(uVar3,unaff_retaddr * 4);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00cd.c
// 00cd8380 FUN_00cd8380

void __thiscall FUN_00cd8380(int *param_1,undefined4 *param_2,int param_3,int param_4)

{
  undefined4 *puVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int *piVar7;
  undefined4 uVar8;
  int iVar9;
  int iVar10;
  int iVar11;
  int iVar12;
  
  uVar2 = (param_3 - param_1[9]) / ((int)((param_1[7] >> 0x1f & 3U) + param_1[7]) >> 2);
  uVar3 = (param_4 - param_1[10]) / ((int)((param_1[8] >> 0x1f & 3U) + param_1[8]) >> 2);
  if (3 < uVar2) {
    return;
  }
  if (3 < uVar3) {
    return;
  }
  iVar4 = (**(code **)(*param_1 + 0xc))();
  iVar5 = (**(code **)(*param_1 + 0x10))();
  iVar9 = ((param_1[3] * param_3) / param_1[7]) % param_1[5];
  iVar10 = ((param_1[4] * param_4) / param_1[8]) % param_1[6];
  iVar11 = iVar10 + iVar5;
  if ((uint)param_1[0x16] <= (uint)param_1[0x15]) {
    FUN_00ca7950((int)*(short *)((int)param_1 + 0x5e));
  }
  param_1[0x15] = param_1[0x15] + 1;
  puVar1 = (undefined4 *)(param_1[0x15] * 0x94 + -0x94 + param_1[0x14]);
  iVar6 = param_1[5];
  iVar12 = iVar9 + iVar4;
  if (iVar6 < iVar12) {
    if (param_1[6] < iVar11) {
      iVar6 = (iVar6 - iVar12) + iVar4;
      iVar11 = (param_1[6] - iVar11) + iVar5;
      puVar1[5] = 0;
      puVar1[6] = 0;
      puVar1[7] = iVar6;
      puVar1[8] = iVar11;
      puVar1[9] = iVar6;
      puVar1[10] = 0;
      puVar1[0xb] = iVar4;
      puVar1[0xc] = iVar11;
      puVar1[0xd] = 0;
      puVar1[0xe] = iVar11;
      puVar1[0xf] = iVar6;
      puVar1[0x10] = iVar5;
      puVar1[0x11] = iVar6;
      puVar1[0x12] = iVar11;
      puVar1[0x13] = iVar4;
      puVar1[0x14] = iVar5;
      puVar1[4] = 4;
      goto LAB_00cd850c;
    }
    if (iVar12 <= iVar6) goto LAB_00cd84c8;
    iVar11 = (iVar6 - iVar12) + iVar4;
    puVar1[5] = 0;
    puVar1[6] = 0;
    puVar1[7] = iVar11;
    puVar1[9] = iVar11;
    puVar1[10] = 0;
    puVar1[0xb] = iVar4;
    puVar1[0xc] = iVar5;
    puVar1[4] = 2;
  }
  else {
LAB_00cd84c8:
    iVar6 = param_1[6];
    puVar1[7] = iVar4;
    if (iVar6 < iVar11) {
      iVar11 = (iVar6 - iVar11) + iVar5;
      puVar1[5] = 0;
      puVar1[6] = 0;
      puVar1[8] = iVar11;
      puVar1[9] = 0;
      puVar1[10] = iVar11;
      puVar1[0xb] = iVar4;
      puVar1[0xc] = iVar5;
      puVar1[4] = 2;
      goto LAB_00cd850c;
    }
    puVar1[5] = 0;
    puVar1[6] = 0;
    puVar1[4] = 1;
  }
  puVar1[8] = iVar5;
LAB_00cd850c:
  iVar4 = puVar1[4];
  if (0 < iVar4) {
    piVar7 = puVar1 + 0x16;
    do {
      piVar7[-1] = piVar7[-0x11] + iVar9;
      *piVar7 = piVar7[-0x10] + iVar10;
      piVar7[1] = piVar7[-0xf] + iVar9;
      piVar7[2] = piVar7[-0xe] + iVar10;
      if (piVar7[-1] == param_1[5]) {
        piVar7[-1] = piVar7[-1] - param_1[5];
        piVar7[1] = piVar7[1] - param_1[5];
      }
      if (*piVar7 == param_1[6]) {
        *piVar7 = *piVar7 - param_1[6];
        piVar7[2] = piVar7[2] - param_1[6];
      }
      piVar7 = piVar7 + 4;
      iVar4 = iVar4 + -1;
    } while (iVar4 != 0);
  }
  iVar4 = FUN_00a71e80(param_1[2],1);
  *puVar1 = *(undefined4 *)(iVar4 + 8);
  uVar8 = FUN_00afdf70(0x27,param_2[1] * 4);
  puVar1[1] = uVar8;
  puVar1[2] = param_2[1];
  uVar8 = (**(code **)(*param_1 + 0xc))();
  puVar1[3] = uVar8;
  uVar8 = 0;
  if (0 < (int)param_2[1]) {
    uVar8 = *param_2;
  }
  FUN_00afca30(puVar1[1],uVar8,param_2[1] * 4);
  *(ushort *)(param_1 + 1) =
       *(ushort *)(param_1 + 1) | 1 << ((char)uVar2 + (char)uVar3 * '\x04' & 0x1fU);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00cd.c
// 00cd81c0 FUN_00cd81c0

void __thiscall
FUN_00cd81c0(int *param_1,int param_2,int param_3,int param_4,int param_5,int param_6,int param_7,
            int param_8,int param_9,int param_10)

{
  code *pcVar1;
  int iVar2;
  undefined4 uVar3;
  int *piVar4;
  byte bVar5;
  int iVar6;
  undefined4 *puVar7;
  undefined2 uStack_3c;
  undefined2 uStack_3a;
  undefined2 uStack_38;
  undefined4 uStack_36;
  undefined4 uStack_32;
  undefined4 uStack_2e;
  undefined4 auStack_28 [2];
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  int iStack_14;
  int iStack_10;
  undefined4 uStack_c;
  undefined4 uStack_8;
  undefined4 uStack_4;
  
  FUN_00cbbb50();
  param_1[0xf] = param_2;
  param_1[0xe] = param_3;
  param_1[4] = param_5;
  param_1[3] = param_4;
  param_1[6] = param_5 + 1;
  param_1[5] = param_4 + 1;
  param_1[8] = param_7;
  param_1[7] = param_6;
  param_1[0xb] = param_8;
  param_1[0xc] = param_9;
  pcVar1 = *(code **)(*param_1 + 0x14);
  param_1[0xd] = param_10;
  param_1[9] = 0;
  param_1[10] = 0;
  iVar6 = 0;
  iVar2 = (*pcVar1)();
  if (0 < iVar2) {
    do {
      bVar5 = (byte)iVar6;
      iVar6 = iVar6 + 1;
      *(ushort *)(param_1 + 1) = *(ushort *)(param_1 + 1) & ~(1 << (bVar5 & 0x1f));
      iVar2 = (**(code **)(*param_1 + 0x14))();
    } while (iVar6 < iVar2);
  }
  iStack_14 = param_1[5];
  iStack_10 = param_1[6];
  puVar7 = auStack_28;
  uStack_8 = 0;
  uStack_4 = 0;
  uStack_c = 0;
  auStack_28[0] = 0x8000;
  uStack_20 = 2;
  uStack_1c = 1;
  uStack_18 = 1;
  uVar3 = FUN_00af4d70("rings_blend_texture",&DAT_014414f9,&DAT_014414f9,1);
  piVar4 = (int *)FUN_00cbc5c0(&param_2,uVar3,puVar7);
  iVar2 = param_1[2];
  if (iVar2 != *piVar4) {
    if (1 < iVar2) {
      (**(code **)(*DAT_019f4d3c + 0xa8))(iVar2);
    }
    iVar2 = *piVar4;
    param_1[2] = iVar2;
    if (1 < iVar2) {
      (**(code **)(*DAT_019f4d3c + 0xa4))(iVar2);
    }
  }
  iVar2 = param_2;
  if (1 < param_2) {
    param_2 = 0;
    (**(code **)(*DAT_019f4d3c + 0xa8))(iVar2);
  }
  FUN_00af2060();
  uStack_3c = (undefined2)param_1[5];
  uStack_3a = (undefined2)param_1[6];
  uStack_32 = 0;
  uStack_38 = 1;
  uStack_2e = 0x1030100;
  uStack_36 = 0x27010000;
  FUN_0106ab50(param_1 + 0x18,*DAT_019fdfb4,DAT_019fdfb4[2],&uStack_3c,0,0,
               "Staging rings_blend_texture");
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00cd.c
// 00cd7d40 FUN_00cd7d40

undefined4 FUN_00cd7d40(undefined4 *param_1,int *param_2)

{
  int iVar1;
  undefined4 *puVar2;
  int iVar3;
  int *piVar4;
  undefined4 uVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  undefined4 local_20 [4];
  undefined4 local_10 [4];
  
  FUN_00a71e80(*param_1,1);
  FUN_00b09e60();
  FUN_00b09e60();
  piVar4 = param_2;
  iVar8 = param_2[1];
  iVar7 = iVar8 + -1;
  if (-1 < iVar7) {
    iVar6 = **(int **)(*param_2 + iVar7 * 4);
    if (1 < iVar6) {
      (**(code **)(*DAT_019f4d3c + 0xa4))(iVar6);
    }
    param_1 = (undefined4 *)iVar6;
    FUN_00cd0340(0x11,&param_1);
    if (1 < iVar6) {
      (**(code **)(*DAT_019f4d3c + 0xa8))(iVar6);
    }
    puVar2 = *(undefined4 **)(*(int *)(*piVar4 + iVar7 * 4) + 4);
    if (1 < (int)puVar2) {
      (**(code **)(*DAT_019f4d3c + 0xa4))(puVar2);
    }
    param_1 = puVar2;
    FUN_00cd0340(0x14,&param_1);
    if (1 < (int)puVar2) {
      (**(code **)(*DAT_019f4d3c + 0xa8))(puVar2);
    }
    iVar8 = iVar8 + -2;
    iVar7 = *piVar4;
    local_10[3] = *(undefined4 *)(*(int *)(iVar7 + 4 + iVar8 * 4) + 0x14);
    local_20[3] = *(undefined4 *)(*(int *)(iVar7 + 4 + iVar8 * 4) + 0x18);
    if (-1 < iVar8) {
      iVar6 = iVar8 * -4;
      do {
        iVar7 = **(int **)(iVar7 + iVar8 * 4);
        if (1 < iVar7) {
          (**(code **)(*DAT_019f4d3c + 0xa4))(iVar7);
        }
        param_1 = (undefined4 *)iVar7;
        FUN_00cd0340(*(undefined4 *)(&DAT_0173dc78 + iVar6),&param_1);
        if (1 < iVar7) {
          (**(code **)(*DAT_019f4d3c + 0xa8))(iVar7);
        }
        puVar2 = *(undefined4 **)(*(int *)(*param_2 + iVar8 * 4) + 4);
        if (1 < (int)puVar2) {
          (**(code **)(*DAT_019f4d3c + 0xa4))(puVar2);
        }
        param_1 = puVar2;
        FUN_00cd0340(*(undefined4 *)(&DAT_0173dc68 + iVar6),&param_1);
        if (1 < (int)puVar2) {
          (**(code **)(*DAT_019f4d3c + 0xa8))(puVar2);
        }
        iVar7 = *param_2;
        iVar3 = *(int *)(&DAT_0173dc58 + iVar6);
        local_10[iVar3] = *(undefined4 *)(*(int *)(iVar7 + iVar8 * 4) + 0x14);
        iVar1 = iVar8 * 4;
        iVar6 = iVar6 + 4;
        iVar8 = iVar8 + -1;
        local_20[iVar3] = *(undefined4 *)(*(int *)(iVar7 + iVar1) + 0x18);
      } while (-1 < iVar8);
    }
  }
  FUN_00cd0410(0xa8e87b,local_10);
  FUN_00cd0410(0xaf0b02,local_20);
  uVar5 = FUN_00cb2ad0();
  iVar8 = DAT_019fdfb4;
  iVar7 = FUN_00c40640();
  *(undefined4 *)(*(int *)(iVar8 + 0x350) + iVar7 * 4) = uVar5;
  uVar5 = *(undefined4 *)(*(int *)(iVar8 + 0x300) + iVar7 * 4);
  FUN_00b09e80();
  FUN_00b09e80();
  return uVar5;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00ce.c
// 00ce03b0 FUN_00ce03b0

/* WARNING: Removing unreachable block (ram,0x00ce0431) */
/* WARNING: Removing unreachable block (ram,0x00ce0444) */
/* WARNING: Removing unreachable block (ram,0x00ce044b) */
/* WARNING: Removing unreachable block (ram,0x00ce047f) */
/* WARNING: Removing unreachable block (ram,0x00ce048e) */
/* WARNING: Removing unreachable block (ram,0x00ce0490) */

void FUN_00ce03b0(undefined4 param_1,int *param_2,undefined4 *param_3,int *param_4)

{
  undefined4 uVar1;
  undefined4 local_4;
  
  if (param_4 != (int *)0x0) {
    uVar1 = FUN_00afdf70(param_1,(int)param_4 * 4);
    *param_3 = uVar1;
    local_4 = 0;
    (**(code **)(*param_2 + 4))(&local_4,4);
    while (param_4 != (int *)0x0) {
      (**(code **)(*param_2 + 4))(&stack0xfffffff0,4);
      param_4 = param_2;
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d0.c
// 00d0e2e0 FUN_00d0e2e0

void __thiscall FUN_00d0e2e0(int param_1,int *param_2)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 unaff_EBP;
  undefined4 unaff_EDI;
  
  (**(code **)(*param_2 + 4))((int *)(param_1 + 4),4);
  iVar1 = *(int *)(param_1 + 4);
  if (iVar1 != 0) {
    iVar1 = iVar1 * 0x18;
    uVar2 = FUN_00afdf70(unaff_EBP,iVar1);
    *(undefined4 *)(param_1 + 8) = uVar2;
    (**(code **)(*param_2 + 4))(uVar2,iVar1);
  }
  (**(code **)(*param_2 + 4))((int *)(param_1 + 0x10),4);
  iVar1 = *(int *)(param_1 + 0x10);
  if (iVar1 != 0) {
    iVar1 = iVar1 * 2;
    uVar2 = FUN_00afdf70(unaff_EBP,iVar1);
    *(undefined4 *)(param_1 + 0x14) = uVar2;
    (**(code **)(*param_2 + 4))(uVar2,iVar1);
  }
  (**(code **)(*param_2 + 4))((int *)(param_1 + 0x1c),4);
  iVar1 = *(int *)(param_1 + 0x1c);
  if (iVar1 != 0) {
    iVar1 = iVar1 * 0xc;
    uVar2 = FUN_00afdf70(unaff_EDI,iVar1);
    *(undefined4 *)(param_1 + 0x20) = uVar2;
    (**(code **)(*param_2 + 4))(uVar2,iVar1);
  }
  (**(code **)(*param_2 + 4))(param_1 + 0x28,0x18);
  (**(code **)(*param_2 + 4))(param_1 + 0x40,4);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d1.c
// 00d15990 FUN_00d15990

void __thiscall FUN_00d15990(int param_1,int param_2)

{
  int iVar1;
  uint uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  int iVar5;
  int *piVar6;
  uint uVar7;
  int local_34 [3];
  short local_28;
  undefined2 local_26;
  undefined **local_24 [5];
  int local_10;
  undefined4 local_c;
  undefined4 local_8;
  short local_4;
  undefined2 local_2;
  
  iVar5 = param_2;
  if ((*(int *)(param_2 + 0xc) != 2) && (*(int *)(param_2 + 0xc) != 3)) {
    FUN_00b00060(&param_2);
    uVar2 = 0;
    uVar7 = 0xffffffff;
    if (0 < *(int *)(param_1 + 0x44)) {
      piVar6 = (int *)(*(int *)(param_1 + 0x40) + 8);
      do {
        uVar7 = uVar2;
        if (*piVar6 == param_2) break;
        uVar2 = uVar2 + 1;
        piVar6 = piVar6 + 3;
        uVar7 = 0xffffffff;
      } while ((int)uVar2 < *(int *)(param_1 + 0x44));
    }
    uVar2 = *(uint *)(iVar5 + 0xcc);
    if (*(int *)(iVar5 + 0xc) == 0) {
      local_28 = 0x27;
      local_26 = 0xffff;
      local_4 = 0x1a;
      local_34[0] = 0;
      local_34[2] = 0;
      local_34[1] = 0;
      local_24[0] = BHG::MemoryDataWalk::vftable;
      local_10 = 0;
      local_8 = 0;
      local_c = 0;
      local_2 = 0xffff;
      FUN_00a87550();
      uVar3 = FUN_00b00330();
      uVar4 = FUN_00b00320(uVar3);
      FUN_00a92bf0(uVar4,uVar3);
      FUN_00cc6800(local_34,local_24);
      if ((-1 < (int)uVar7) && (uVar7 < *(uint *)(param_1 + 0x44))) {
        iVar5 = (*(uint *)(param_1 + 0x44) - uVar7) + -1;
        if (iVar5 != 0) {
          iVar1 = *(int *)(param_1 + 0x40) + uVar7 * 0xc;
          FUN_00afc9d0(iVar1,iVar1 + 0xc,iVar5 * 0xc);
        }
        *(int *)(param_1 + 0x44) = *(int *)(param_1 + 0x44) + -1;
      }
      FUN_00cd8380(local_34,uVar2 >> 0x10,uVar2 & 0xffff);
      local_24[0] = BHG::MemoryDataWalk::vftable;
      FUN_00a87560();
      if (local_10 != 0) {
        FUN_00afe180((int)local_4,local_10);
      }
      local_10 = 0;
      local_8 = 0;
      local_c = 0;
      local_2 = 0xffff;
      if (local_34[0] != 0) {
        FUN_00afe180((int)local_28,local_34[0]);
        return;
      }
    }
    else {
      *(undefined4 *)(*(int *)(param_1 + 0x40) + 8 + uVar7 * 0xc) = 0;
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d1.c
// 00d15490 FUN_00d15490

void __thiscall FUN_00d15490(short *param_1,int *param_2)

{
  short *psVar1;
  short sVar2;
  uint uVar3;
  int iVar4;
  byte *pbStack_74;
  int *piStack_70;
  short *psStack_6c;
  undefined4 uStack_68;
  short *psStack_64;
  undefined4 uStack_60;
  short *psStack_5c;
  undefined4 uStack_58;
  short *psStack_54;
  undefined4 uStack_50;
  byte *pbStack_4c;
  undefined4 uStack_48;
  short *psStack_44;
  undefined4 uStack_40;
  short *psStack_3c;
  undefined4 uStack_38;
  short *psStack_34;
  undefined4 uStack_30;
  short *psStack_2c;
  undefined4 uStack_28;
  short *psStack_24;
  undefined4 uStack_20;
  short *psStack_1c;
  undefined4 uStack_18;
  
  uStack_18 = 0xd154a1;
  FUN_00cddd30();
  uStack_18 = 0xd154a9;
  FUN_00cddd30();
  uStack_18 = 2;
  psVar1 = param_1 + 4;
  uStack_20 = 0xd154bc;
  psStack_1c = psVar1;
  (**(code **)(*param_2 + 4))();
  uStack_20 = 2;
  psStack_24 = param_1 + 5;
  uStack_28 = 0xd154cb;
  (**(code **)(*param_2 + 4))();
  uStack_28 = 2;
  psStack_2c = param_1 + 6;
  uStack_30 = 0xd154da;
  (**(code **)(*param_2 + 4))();
  uStack_30 = 2;
  psStack_34 = param_1 + 7;
  uStack_38 = 0xd154e9;
  (**(code **)(*param_2 + 4))();
  psStack_3c = param_1 + 0x20;
  uStack_38 = 2;
  uStack_40 = 0xd154f8;
  (**(code **)(*param_2 + 4))();
  uStack_40 = 2;
  psStack_44 = param_1 + 0x21;
  uStack_48 = 0xd15507;
  (**(code **)(*param_2 + 4))();
  uStack_48 = 2;
  pbStack_4c = (byte *)(param_1 + 0x22);
  uStack_50 = 0xd15516;
  (**(code **)(*param_2 + 4))();
  uStack_50 = 2;
  psStack_54 = param_1 + 0x23;
  uStack_58 = 0xd15525;
  (**(code **)(*param_2 + 4))();
  uStack_58 = 0x30;
  psStack_5c = param_1 + 8;
  uStack_60 = 0xd15534;
  (**(code **)(*param_2 + 4))();
  psStack_44 = *(short **)(param_1 + 0x30);
  psStack_64 = param_1 + 0x2c;
  uStack_60 = 4;
  uStack_68 = 0xd1554a;
  (**(code **)(*param_2 + 4))();
  uStack_68 = *(undefined4 *)(param_1 + 0x2c);
  psStack_6c = param_1 + 0x2e;
  piStack_70 = param_2;
  pbStack_74 = pbStack_4c;
  FUN_00ca9ef0();
  pbStack_4c = *(byte **)(param_1 + 0x36);
  uStack_68 = 4;
  piStack_70 = (int *)0xd15573;
  psStack_6c = param_1 + 0x32;
  (**(code **)(*param_2 + 4))();
  piStack_70 = *(int **)(param_1 + 0x32);
  pbStack_74 = (byte *)(param_1 + 0x34);
  FUN_00ca9ef0(psStack_54,param_2);
  piStack_70 = (int *)0x1;
  pbStack_74 = (byte *)(param_1 + 0x3d);
  (**(code **)(*param_2 + 4))();
  if ((*(byte *)(param_1 + 0x3d) & 2) == 0) {
    FUN_00a1b0c0(param_1 + 0x24,param_2);
  }
  FUN_00cf02e0(param_1 + 0x3e,param_2);
  FUN_00cf0360(param_1 + 0x46,param_2);
  (**(code **)(*param_2 + 4))(param_1 + 0x4e,4);
  FUN_00a7ee90(*(undefined4 *)(param_1 + 0x4e),1);
  (**(code **)(*param_2 + 4))(param_1 + 0x52,4);
  if (*(int *)(param_1 + 0x50) != 0) {
    (**(code **)(*param_2 + 4))(*(undefined4 *)(param_1 + 0x56),*(int *)(param_1 + 0x50));
  }
  if ((int)(short)(param_1[5] - *psVar1) == *(int *)(param_1 + 0x3a)) {
    (**(code **)(*param_2 + 4))(param_1 + 0x58,4);
    FUN_00a7edc0(*(undefined4 *)(param_1 + 0x58),1);
    (**(code **)(*param_2 + 4))(param_1 + 0x5c,4);
    if (*(int *)(param_1 + 0x5a) != 0) {
      (**(code **)(*param_2 + 4))(*(undefined4 *)(param_1 + 0x60),*(int *)(param_1 + 0x5a));
    }
    (**(code **)(*param_2 + 4))(param_1 + 0x62,2);
    (**(code **)(*param_2 + 4))(param_1 + 99,2);
    (**(code **)(*param_2 + 4))(param_1 + 100,2);
    (**(code **)(*param_2 + 4))(param_1 + 0x65,2);
    FUN_00cf0360(param_1 + 0x66,param_2);
  }
  pbStack_74 = (byte *)0x0;
  uVar3 = FUN_00ab8220((int)(short)(param_1[5] - *psVar1),&pbStack_74);
  uVar3 = uVar3 / *(uint *)(param_1 + 0x3a);
  if ((int)uVar3 < 1) {
    uVar3 = 1;
  }
  *param_1 = *psVar1;
  param_1[1] = param_1[5];
  param_1[3] = param_1[7];
  sVar2 = (short)uVar3;
  *param_1 = *param_1 - sVar2;
  param_1[1] = param_1[1] + sVar2;
  param_1[3] = param_1[3] + sVar2;
  param_1[2] = param_1[6];
  param_1[2] = param_1[2] - sVar2;
  iVar4 = 0;
  while (uVar3 = uVar3 >> 1, uVar3 != 0) {
    iVar4 = iVar4 + 1;
  }
  *(int *)(param_1 + 0x6e) = iVar4;
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d1.c
// 00d15250 FUN_00d15250

void __fastcall FUN_00d15250(int param_1)

{
  uint uVar1;
  uint uVar2;
  undefined4 uVar3;
  uint uVar4;
  int iVar5;
  uint uVar6;
  int iVar7;
  int iVar8;
  int local_24;
  int local_20;
  uint local_1c;
  int local_14;
  int local_10;
  uint local_c;
  uint local_8;
  undefined2 local_4;
  undefined2 local_2;
  
  uVar6 = 0;
  local_4 = 0x27;
  iVar5 = *(int *)(param_1 + 4);
  local_10 = 0;
  local_8 = 0;
  local_2 = 0xffff;
  local_1c = 0;
  if (*(int *)(iVar5 + 0xc) != 0) {
    local_24 = 0;
    iVar7 = 0;
    do {
      iVar5 = *(int *)(iVar5 + 8) + local_24;
      uVar4 = 0;
      local_c = 0;
      local_20 = 0;
      iVar8 = iVar7;
      uVar2 = local_c;
      uVar1 = local_8;
      if (0 < *(int *)(iVar5 + 8)) {
        do {
          local_14 = **(int **)(param_1 + 4) + *(int *)(*(int *)(iVar5 + 4) + local_20 * 4) * 0x1c;
          iVar8 = iVar7;
          if (uVar6 <= uVar4) {
            if (uVar6 == 0) {
              uVar2 = 4;
            }
            else {
              uVar2 = uVar6;
              if (0x400 < (int)uVar6) {
                uVar2 = 0x400;
              }
            }
            uVar6 = uVar6 + uVar2;
            local_10 = FUN_00afdf70(0x27,uVar6 * 4);
            iVar8 = local_10;
            if (iVar7 != 0) {
              if (uVar4 != 0) {
                FUN_00afc9d0(local_10,iVar7,uVar4 * 4);
              }
              FUN_00afe180(0x27,iVar7);
              iVar8 = local_10;
            }
          }
          *(int *)(iVar8 + uVar4 * 4) = local_14;
          local_20 = local_20 + 1;
          uVar4 = uVar4 + 1;
          iVar7 = iVar8;
          uVar2 = uVar4;
          uVar1 = uVar6;
        } while (local_20 < *(int *)(iVar5 + 8));
      }
      local_8 = uVar1;
      local_c = uVar2;
      iVar7 = *(int *)(DAT_019fdffc + 0x8c);
      local_14 = iVar7;
      if (1 < iVar7) {
        (**(code **)(*DAT_019f4d78 + 0xa4))(iVar7);
      }
      uVar3 = FUN_00cd7d40(&local_14,&local_10);
      *(undefined4 *)(iVar5 + 0xc) = uVar3;
      if (1 < iVar7) {
        (**(code **)(*DAT_019f4d78 + 0xa8))(iVar7);
      }
      iVar5 = *(int *)(param_1 + 4);
      local_24 = local_24 + 0x10;
      local_1c = local_1c + 1;
      iVar7 = iVar8;
    } while (local_1c < *(uint *)(iVar5 + 0xc));
    if (iVar8 != 0) {
      FUN_00afe180(0x27,iVar8);
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d2.c
// 00d21bb0 FUN_00d21bb0

void __thiscall FUN_00d21bb0(int param_1,uint param_2)

{
  undefined8 *puVar1;
  int iVar2;
  int *piVar3;
  uint uVar4;
  int iVar5;
  int iVar6;
  undefined4 local_10;
  int local_c;
  uint uStack_8;
  
  uVar4 = param_2 & 0x80000003;
  if ((int)uVar4 < 0) {
    uVar4 = (uVar4 - 1 | 0xfffffffc) + 1;
  }
  iVar6 = ((int)((*(int *)(param_1 + 0x1c) >> 0x1f & 3U) + *(int *)(param_1 + 0x1c)) >> 2) * uVar4 +
          *(int *)(param_1 + 0x24);
  iVar5 = (int)((*(int *)(param_1 + 0x20) >> 0x1f & 3U) + *(int *)(param_1 + 0x20)) >> 2;
  uVar4 = iVar5 * ((int)(((int)param_2 >> 0x1f & 3U) + param_2) >> 2) + *(int *)(param_1 + 0x28);
  iVar2 = 0;
  if (0 < *(int *)(param_1 + 0x44)) {
    piVar3 = *(int **)(param_1 + 0x40);
    do {
      if ((iVar6 == *piVar3) && (uVar4 == piVar3[1])) {
        return;
      }
      iVar2 = iVar2 + 1;
      piVar3 = piVar3 + 3;
    } while (iVar2 < *(int *)(param_1 + 0x44));
  }
  iVar2 = (int)((*(int *)(param_1 + 0x1c) >> 0x1f & 3U) + *(int *)(param_1 + 0x1c)) >> 2;
  iVar2 = ((*(int *)(param_1 + 0x2c) + -1 + iVar2) / iVar2) * ((int)uVar4 / iVar5) + iVar6 / iVar2;
  iVar5 = FUN_00afdf70(0x1a,0x100);
  if (iVar5 != 0) {
    BHG_StreamingRequestFromMultiEntryFile__xtor();
  }
  FUN_00b03200(param_1,FUN_00d15990,0,0,*(int *)(param_1 + 0x3c) + 0x380,
               *(undefined4 *)
                (*(int *)(*(int *)(*(int *)(param_1 + 0x3c) + 0x378) + 4 +
                         *(int *)(param_1 + 0x38) * 0xc) + iVar2 * 4),iVar6 * 0x10000 | uVar4,iVar2)
  ;
  FUN_00b06990(&local_10,iVar5,5);
  local_c = iVar6;
  uStack_8 = uVar4;
  if (*(uint *)(param_1 + 0x48) <= *(uint *)(param_1 + 0x44)) {
    FUN_00cc6680((int)*(short *)(param_1 + 0x4e));
  }
  puVar1 = (undefined8 *)(*(int *)(param_1 + 0x40) + *(int *)(param_1 + 0x44) * 0xc);
  *puVar1 = CONCAT44(uStack_8,local_c);
  *(undefined4 *)(puVar1 + 1) = local_10;
  *(int *)(param_1 + 0x44) = *(int *)(param_1 + 0x44) + 1;
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d3.c
// 00d3ccb0 FUN_00d3ccb0

void FUN_00d3ccb0(undefined4 param_1,undefined4 param_2,int *param_3,uint param_4)

{
  int iVar1;
  undefined4 *puVar2;
  uint uVar3;
  
  if (param_4 != 0) {
    iVar1 = FUN_00afdf70(param_1,param_4 * 4);
    uVar3 = 0;
    *param_3 = iVar1;
    if (param_4 != 0) {
      do {
        puVar2 = (undefined4 *)FUN_00afdf70(param_1,0x34);
        if (puVar2 != (undefined4 *)0x0) {
          puVar2[2] = 0x17;
          *puVar2 = 0;
          puVar2[1] = 0;
          puVar2[6] = 0x17;
          puVar2[4] = 0;
          puVar2[5] = 0;
          FUN_00ab6580();
          puVar2[3] = 0xffffffff;
        }
        *(undefined4 **)(*param_3 + uVar3 * 4) = puVar2;
        FUN_00d3a810(param_2);
        uVar3 = uVar3 + 1;
      } while (uVar3 < param_4);
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d3.c
// 00d3a810 FUN_00d3a810

void __thiscall FUN_00d3a810(undefined4 *param_1,int *param_2)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 *puVar3;
  
  uVar2 = param_1[2];
  puVar3 = param_1;
  (**(code **)(*param_2 + 4))(param_1,4);
  FUN_00d24140(uVar2,param_2,param_1 + 1,*param_1);
  (**(code **)(*param_2 + 4))(param_1 + 3,4);
  (**(code **)(*param_2 + 4))(param_1 + 4,4);
  iVar1 = param_1[4];
  if (iVar1 != 0) {
    iVar1 = iVar1 * 4;
    uVar2 = FUN_00afdf70(puVar3,iVar1);
    param_1[5] = uVar2;
    (**(code **)(*param_2 + 4))(uVar2,iVar1);
  }
  (**(code **)(*param_2 + 4))(param_1 + 7,0x18);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d3.c
// 00d33860 FUN_00d33860

void __thiscall FUN_00d33860(int param_1,short *param_2,undefined4 param_3)

{
  uint uVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  int iVar5;
  
  uVar1 = (int)(short)(param_2[1] - *param_2) / *(int *)(param_1 + 0xd0);
  iVar2 = 0;
  while (uVar1 = uVar1 >> 1, uVar1 != 0) {
    iVar2 = iVar2 + 1;
  }
  iVar3 = *(int *)(param_1 + 0xd0) << ((byte)iVar2 & 0x1f);
  iVar5 = ((*(int *)(param_1 + 0xcc) + iVar3) / iVar3) * ((int)param_2[2] / iVar3) +
          (int)*param_2 / iVar3;
  iVar3 = 0;
  if (0 < *(int *)(param_1 + 0x1c)) {
    piVar4 = *(int **)(param_1 + 0x18);
    do {
      if (*piVar4 ==
          *(int *)(*(int *)(*(int *)(*(int *)(param_1 + 8) + 4) + 4 + iVar2 * 0xc) + iVar5 * 4)) {
        if (iVar3 != -1) {
          iVar2 = *(int *)(param_1 + 0x18);
          piVar4 = (int *)(iVar2 + 8 + iVar3 * 0x18);
          if (*(uint *)(iVar2 + 0x10 + iVar3 * 0x18) <= *(uint *)(iVar2 + 0xc + iVar3 * 0x18)) {
            FUN_00ca7d70((int)*(short *)((int)piVar4 + 0xe));
          }
          *(short **)(*piVar4 + piVar4[1] * 4) = param_2;
          piVar4[1] = piVar4[1] + 1;
          if (*(uint *)(param_1 + 0x40) <= *(uint *)(param_1 + 0x3c)) {
            FUN_00ca7d70((int)*(short *)(param_1 + 0x46));
          }
          *(short **)(*(int *)(param_1 + 0x38) + *(int *)(param_1 + 0x3c) * 4) = param_2;
          *(int *)(param_1 + 0x3c) = *(int *)(param_1 + 0x3c) + 1;
          return;
        }
        break;
      }
      iVar3 = iVar3 + 1;
      piVar4 = piVar4 + 6;
    } while (iVar3 < *(int *)(param_1 + 0x1c));
  }
  iVar3 = FUN_00d33670(iVar2,iVar5,param_3);
  iVar2 = *(int *)(param_1 + 0x18);
  piVar4 = (int *)(iVar2 + 8 + iVar3 * 0x18);
  if (*(uint *)(iVar2 + 0x10 + iVar3 * 0x18) <= *(uint *)(iVar2 + 0xc + iVar3 * 0x18)) {
    FUN_00ca7d70((int)*(short *)((int)piVar4 + 0xe));
  }
  *(short **)(*piVar4 + piVar4[1] * 4) = param_2;
  piVar4[1] = piVar4[1] + 1;
  if (*(uint *)(param_1 + 0x40) <= *(uint *)(param_1 + 0x3c)) {
    FUN_00ca7d70((int)*(short *)(param_1 + 0x46));
  }
  *(short **)(*(int *)(param_1 + 0x38) + *(int *)(param_1 + 0x3c) * 4) = param_2;
  *(int *)(param_1 + 0x3c) = *(int *)(param_1 + 0x3c) + 1;
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d3.c
// 00d33670 FUN_00d33670

int __thiscall FUN_00d33670(int param_1,int param_2,int param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  
  iVar1 = *(int *)(*(int *)(*(int *)(*(int *)(param_1 + 8) + 4) + 4 + param_2 * 0xc) + param_3 * 4);
  iVar2 = 0;
  if (0 < *(int *)(param_1 + 0x1c)) {
    piVar4 = *(int **)(param_1 + 0x18);
    do {
      if (*piVar4 == iVar1) {
        if (iVar2 != -1) {
          return -1;
        }
        break;
      }
      iVar2 = iVar2 + 1;
      piVar4 = piVar4 + 6;
    } while (iVar2 < *(int *)(param_1 + 0x1c));
  }
  iVar2 = FUN_00afdf70(0x1a,0x100);
  if (iVar2 != 0) {
    BHG_StreamingRequestFromMultiEntryFile__xtor();
  }
  FUN_00b03200(param_1,&LAB_00d21240,0,0,*(undefined4 *)(param_1 + 0xc),iVar1,0,0);
  FUN_00b06990(&param_2,iVar2,param_4);
  if (*(uint *)(param_1 + 0x20) <= *(uint *)(param_1 + 0x1c)) {
    FUN_00d23c10((int)*(short *)(param_1 + 0x26));
  }
  *(int *)(param_1 + 0x1c) = *(int *)(param_1 + 0x1c) + 1;
  iVar3 = *(int *)(param_1 + 0x1c) + -1;
  iVar2 = iVar3 * 0x18;
  *(int *)(iVar2 + 4 + *(int *)(param_1 + 0x18)) = param_2;
  *(int *)(iVar2 + *(int *)(param_1 + 0x18)) = iVar1;
  *(undefined4 *)(iVar2 + 0xc + *(int *)(param_1 + 0x18)) = 0;
  return iVar3;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d4.c
// 00d46dd0 FUN_00d46dd0

void __thiscall FUN_00d46dd0(int param_1,int *param_2)

{
  undefined4 uVar1;
  
  (**(code **)(*param_2 + 4))(param_1 + 0xa0,4);
  (**(code **)(*param_2 + 4))(param_1 + 0x10c,4);
  (**(code **)(*param_2 + 4))(param_1 + 0x110,4);
  (**(code **)(*param_2 + 4))(param_1 + 0x114,4);
  (**(code **)(*param_2 + 4))(param_1 + 0x118,0x2d);
  (**(code **)(*param_2 + 4))(param_1 + 0x14c,4);
  (**(code **)(*param_2 + 4))(param_1 + 0x150,4);
  (**(code **)(*param_2 + 4))(param_1 + 0xcc,4);
  uVar1 = *(undefined4 *)(param_1 + 0xd8);
  (**(code **)(*param_2 + 4))((undefined4 *)(param_1 + 0xd0),4);
  FUN_00d45f10(uVar1,param_2,param_1 + 0xd4,*(undefined4 *)(param_1 + 0xd0));
  (**(code **)(*param_2 + 4))(param_1 + 0x148,4);
  FUN_00a8db50(param_2);
  uVar1 = *(undefined4 *)(param_1 + 0x10);
  (**(code **)(*param_2 + 4))((undefined4 *)(param_1 + 8),4);
  FUN_00ce03b0(uVar1,param_2,param_1 + 0xc,*(undefined4 *)(param_1 + 8));
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d4.c
// 00d45f10 FUN_00d45f10

void FUN_00d45f10(undefined4 param_1,int *param_2,int *param_3,uint param_4)

{
  undefined4 uVar1;
  int iVar2;
  undefined4 *puVar3;
  uint uVar4;
  
  if (param_4 != 0) {
    iVar2 = FUN_00afdf70(param_1,param_4 * 4);
    uVar4 = 0;
    *param_3 = iVar2;
    if (param_4 != 0) {
      do {
        puVar3 = (undefined4 *)FUN_00afdf70(param_1,0xc);
        if (puVar3 != (undefined4 *)0x0) {
          *puVar3 = 0;
          puVar3[1] = 0;
          puVar3[2] = 0x17;
        }
        *(undefined4 **)(*param_3 + uVar4 * 4) = puVar3;
        puVar3 = *(undefined4 **)(*param_3 + uVar4 * 4);
        uVar1 = puVar3[2];
        (**(code **)(*param_2 + 4))(puVar3,4);
        FUN_00d3ccb0(uVar1,param_2,puVar3 + 1,*puVar3);
        uVar4 = uVar4 + 1;
      } while (uVar4 < param_4);
    }
  }
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_0105.c
// 0105ade0 FUN_0105ade0

char FUN_0105ade0(undefined4 param_1,char param_2)

{
  switch(param_1) {
  default:
    return '\0';
  case 1:
    return 'G';
  case 2:
    return 'H';
  case 3:
    return 'J';
  case 4:
    return 'K';
  case 5:
    return 'M';
  case 6:
    return 'N';
  case 0x12:
    return 'A';
  case 0x13:
    return '=';
  case 0x17:
    return (param_2 == '\0') + '0';
  case 0x1f:
    return ')';
  case 0x20:
    return '#';
  case 0x27:
    return (param_2 == '\0') + '\x1b';
  case 0x28:
    return (param_2 == '\0') * '\x02' + '\x1b';
  case 0x2a:
    return '\n';
  case 0x2b:
    return '\x02';
  case 0x2d:
    return '5';
  case 0x2e:
    return ',';
  case 0x37:
    return '\'';
  case 0x39:
    return '\x1a';
  }
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_0106.c
// 0106ab50 FUN_0106ab50

void FUN_0106ab50(undefined8 *param_1,int param_2,undefined4 param_3,ushort *param_4,int param_5,
                 uint param_6,undefined4 param_7)

{
  ushort uVar1;
  byte bVar2;
  uint uVar3;
  undefined4 *puVar4;
  uint uVar5;
  int iVar6;
  undefined1 uVar7;
  uint extraout_ECX;
  undefined4 *puVar8;
  uint uVar9;
  undefined4 uVar10;
  int local_3ec;
  undefined4 local_3e8;
  int *local_3e4;
  uint local_3e0;
  undefined8 *local_3dc;
  ulonglong local_3d8;
  undefined8 local_3d0;
  undefined8 local_3c8;
  undefined8 local_3c0;
  uint local_3b8;
  undefined4 local_3b4;
  undefined4 local_3b0;
  undefined4 local_3ac [234];
  uint local_4;
  
  local_4 = DAT_0197713c ^ (uint)&local_3ec;
  *param_1 = *(undefined8 *)param_4;
  param_1[1] = *(undefined8 *)(param_4 + 4);
  local_3e8 = param_7;
  local_3ec = param_2;
  *(ushort *)(param_1 + 2) = param_4[8];
  *(undefined4 *)((int)param_1 + 0x14) = 0;
  *(undefined4 *)(param_1 + 3) = 0;
  local_3e4 = *(int **)(param_2 + 600);
  uVar1 = param_4[3];
  local_3dc = param_1;
  bVar2 = (byte)(uVar1 >> 8);
  if (((uVar1 & 2) == 0) || ((uVar1 & 0x100) == 0)) {
    iVar6 = (uint)bVar2 << 8;
  }
  else {
    iVar6 = CONCAT31((uint3)bVar2,1);
  }
  uVar3 = FUN_0105ade0(*(undefined1 *)((int)param_4 + 9),iVar6);
  *(uint *)((int)param_1 + 0x1c) = uVar3;
  if (uVar3 == extraout_ECX) {
    puVar4 = (undefined4 *)FUN_01194c10(*(undefined1 *)((int)param_4 + 9));
    FUN_01050e90("Unsupported pixel format \'%0x\' (%s) in allocateTextureData()\n",
                 *(undefined1 *)((int)param_4 + 9),*puVar4);
    goto LAB_0106b0bc;
  }
  if (extraout_ECX < param_6) {
    puVar8 = local_3ac + 1;
    puVar4 = (undefined4 *)(param_5 + 8);
    local_3e0 = param_6;
    do {
      puVar8[-1] = puVar4[-2];
      *puVar8 = puVar4[-1];
      *(undefined4 *)(((int)local_3ac - param_5) + (int)puVar4) = *puVar4;
      puVar8 = puVar8 + 3;
      puVar4 = puVar4 + 3;
      local_3e0 = local_3e0 - 1;
    } while (local_3e0 != 0);
    local_3e0 = 0;
    param_1 = local_3dc;
  }
  switch((char)param_4[4]) {
  case '\0':
    uVar7 = (undefined1)param_4[8];
    local_3c8 = 0;
    local_3c0 = 0;
    local_3d8 = (ulonglong)CONCAT14(*(undefined1 *)((int)param_4 + 0xf),(uint)*param_4);
    local_3d0 = CONCAT44(uVar3,1);
    switch(uVar7) {
    case 0:
      uVar3 = 0;
      break;
    case 1:
    case 3:
      uVar3 = 3;
      break;
    case 2:
      uVar3 = 2;
      break;
    default:
      goto switchD_0106b039_default;
    }
    break;
  case '\x01':
    _memset(&local_3d8,0,0x2c);
    uVar1 = param_4[3];
    local_3d0 = CONCAT44(1,(uint)*(byte *)((int)param_4 + 0xf));
    local_3b8 = 0;
    local_3d8 = (ulonglong)CONCAT24(param_4[1],(uint)*param_4);
    local_3c8 = CONCAT44(1,uVar3);
    if ((uVar1 & 2) == 0) {
      if ((uVar1 & 0xc) != 0) {
        local_3b8 = 0x40;
      }
    }
    else {
      local_3b8 = 0x20;
    }
    if ((uVar1 & 1) != 0) {
      local_3b8 = local_3b8 | 8;
    }
    uVar7 = (undefined1)param_4[8];
    switch(uVar7) {
    case 1:
    case 3:
      goto switchD_0106ade4_caseD_1;
    case 2:
      goto switchD_0106ade4_caseD_2;
    }
switchD_0106ade4_caseD_0:
    local_3b4 = 0;
    goto LAB_0106adfb;
  case '\x02':
    local_3d8 = (ulonglong)CONCAT24(param_4[1],(uint)*param_4);
    uVar1 = param_4[3];
    local_3d0 = (ulonglong)CONCAT14(*(undefined1 *)((int)param_4 + 0xf),(uint)param_4[2]);
    uVar9 = 0;
    local_3c8 = (ulonglong)uVar3;
    if ((uVar1 & 2) == 0) {
      if ((uVar1 & 0xc) != 0) {
        uVar9 = 0x40;
      }
    }
    else {
      uVar9 = 0x20;
    }
    if ((uVar1 & 1) != 0) {
      uVar9 = uVar9 | 8;
    }
    uVar3 = (uint)(byte)param_4[8];
    local_3c0 = (ulonglong)uVar9;
    local_3b8 = 0;
    switch(uVar3) {
    case 1:
    case 3:
      goto switchD_0106aeeb_caseD_1;
    case 2:
      goto switchD_0106aeeb_caseD_2;
    }
switchD_0106aeeb_caseD_0:
    uVar10 = 0;
    goto LAB_0106af02;
  case '\x03':
    if (param_6 != (param_6 / 6) * 6) {
      FUN_01050e90("[graphics] You have to specify all 6 cube faces!\n");
      goto LAB_0106b0bc;
    }
    _memset(&local_3d8,0,0x2c);
    uVar1 = param_4[3];
    local_3b8 = 0;
    local_3d8 = (ulonglong)CONCAT24(param_4[1],(uint)*param_4);
    local_3d0 = CONCAT44(6,(uint)*(byte *)((int)param_4 + 0xf));
    local_3c8 = CONCAT44(1,uVar3);
    if ((uVar1 & 2) == 0) {
      if ((uVar1 & 0xc) != 0) {
        local_3b8 = 0x40;
      }
    }
    else {
      local_3b8 = 0x20;
    }
    if ((uVar1 & 1) != 0) {
      local_3b8 = local_3b8 | 8;
    }
    uVar7 = (undefined1)param_4[8];
    switch(uVar7) {
    case 1:
    case 3:
      goto switchD_0106b015_caseD_1;
    case 2:
      goto switchD_0106b015_caseD_2;
    }
switchD_0106b015_caseD_0:
    local_3b4 = 0;
    goto LAB_0106b02c;
  default:
    goto switchD_0106ac63_default;
  }
  local_3c8 = (ulonglong)uVar3;
                    /* WARNING (jumptable): Sanity check requires truncation of jumptable */
                    /* WARNING: Could not find normalized switch variable to match jumptable */
  switch(uVar7) {
  case 0:
    uVar9 = 0;
    break;
  default:
    uVar9 = 0x30000;
    break;
  case 2:
    uVar9 = 0x10000;
    break;
  case 4:
    goto switchD_0106ade4_caseD_0;
  case 5:
  case 7:
switchD_0106ade4_caseD_1:
    local_3b4 = 0x30000;
    goto LAB_0106adfb;
  case 6:
switchD_0106ade4_caseD_2:
    local_3b4 = 0x10000;
LAB_0106adfb:
    switch(uVar7) {
    case 0:
switchD_0106ae08_caseD_0:
      uVar10 = 0;
      break;
    case 1:
    case 3:
switchD_0106ae08_caseD_1:
      uVar10 = 3;
      break;
    case 2:
switchD_0106ae08_caseD_2:
      uVar10 = 2;
      break;
    default:
switchD_0106b039_default:
                    /* WARNING: Subroutine does not return */
      _exit(1);
    }
    local_3c0 = CONCAT44(uVar10,(undefined4)local_3c0);
    iVar6 = (**(code **)(*local_3e4 + 0x14))
                      (local_3e4,&local_3d8,-(uint)(param_5 != 0) & (uint)local_3ac,
                       (int)param_1 + 0x14);
    if (iVar6 < 0) {
      FUN_01050e90("[graphics] Failed to create 2D Texture \'%s\'\n",local_3e8);
      FUN_010609d0(local_3ec,iVar6,"CreateTexture2D");
      goto LAB_0106b0bc;
    }
    goto switchD_0106ac63_default;
  case 8:
    goto switchD_0106ae08_caseD_0;
  case 9:
  case 0xb:
    goto switchD_0106ae08_caseD_1;
  case 10:
    goto switchD_0106ae08_caseD_2;
  case 0xc:
    goto switchD_0106aeeb_caseD_0;
  case 0xd:
  case 0xf:
switchD_0106aeeb_caseD_1:
    uVar10 = 0x30000;
    goto LAB_0106af02;
  case 0xe:
switchD_0106aeeb_caseD_2:
    uVar10 = 0x10000;
LAB_0106af02:
    local_3c0 = CONCAT44(uVar10,(undefined4)local_3c0);
    switch(uVar3) {
    case 0:
switchD_0106af0f_caseD_0:
      uVar10 = 0;
      break;
    case 1:
    case 3:
switchD_0106af0f_caseD_1:
      uVar10 = 3;
      break;
    case 2:
switchD_0106af0f_caseD_2:
      uVar10 = 2;
      break;
    default:
      goto switchD_0106b039_default;
    }
    local_3c8 = CONCAT44(uVar10,(undefined4)local_3c8);
    iVar6 = (**(code **)(*local_3e4 + 0x18))
                      (local_3e4,&local_3d8,-(uint)(param_5 != 0) & (uint)local_3ac,
                       (int)param_1 + 0x14);
    if (iVar6 < 0) {
      FUN_01050e90("[graphics] Failed to create 3D Texture \'%s\'\n",local_3e8);
      FUN_010609d0(local_3ec,iVar6,"CreateTexture3D");
      goto LAB_0106b0bc;
    }
    goto switchD_0106ac63_default;
  case 0x10:
    goto switchD_0106af0f_caseD_0;
  case 0x11:
  case 0x13:
    goto switchD_0106af0f_caseD_1;
  case 0x12:
    goto switchD_0106af0f_caseD_2;
  case 0x14:
    goto switchD_0106b015_caseD_0;
  case 0x15:
  case 0x17:
switchD_0106b015_caseD_1:
    local_3b4 = 0x30000;
    goto LAB_0106b02c;
  case 0x16:
switchD_0106b015_caseD_2:
    local_3b4 = 0x10000;
LAB_0106b02c:
    switch(uVar7) {
    case 0:
switchD_0106b039_caseD_0:
      uVar10 = 0;
      break;
    case 1:
    case 3:
switchD_0106b039_caseD_1:
      uVar10 = 3;
      break;
    case 2:
switchD_0106b039_caseD_2:
      uVar10 = 2;
      break;
    default:
      goto switchD_0106b039_default;
    }
    local_3c0 = CONCAT44(uVar10,(undefined4)local_3c0);
    local_3b0 = 4;
    iVar6 = (**(code **)(*local_3e4 + 0x14))
                      (local_3e4,&local_3d8,-(uint)(param_5 != 0) & (uint)local_3ac,
                       (int)param_1 + 0x14);
    if (iVar6 < 0) {
      FUN_01050e90("[graphics] Failed to create Cube Texture \'%s\'\n",local_3e8);
      FUN_010609d0(local_3ec,iVar6,"Create Cube Texture");
      goto LAB_0106b0bc;
    }
    goto switchD_0106ac63_default;
  case 0x18:
    goto switchD_0106b039_caseD_0;
  case 0x19:
  case 0x1b:
    goto switchD_0106b039_caseD_1;
  case 0x1a:
    goto switchD_0106b039_caseD_2;
  }
  uVar1 = param_4[3];
  uVar5 = 0;
  if ((uVar1 & 2) == 0) {
    if ((uVar1 & 0xc) != 0) {
      uVar5 = 0x40;
    }
  }
  else {
    uVar5 = 0x20;
  }
  if ((uVar1 & 1) == 1) {
    uVar5 = uVar5 | 8;
  }
  local_3c8 = CONCAT44(uVar5,uVar3);
  local_3c0 = (ulonglong)uVar9;
  if ((uVar1 & 1) == 1) {
    local_3c8 = CONCAT44(uVar5,uVar3) | 0x800000000;
  }
  iVar6 = (**(code **)(*local_3e4 + 0x10))
                    (local_3e4,&local_3d8,-(uint)(param_5 != 0) & (uint)local_3ac,
                     (int)param_1 + 0x14);
  if (iVar6 < 0) {
    FUN_01050e90("[graphics] Failed to create 1D Texture \'%s\'\n",local_3e8);
    FUN_010609d0(local_3ec,iVar6,"CreateTexture1D");
  }
  else {
switchD_0106ac63_default:
    FUN_01061890(param_1,local_3ec,param_4,local_3e8);
  }
LAB_0106b0bc:
  __security_check_cookie(local_4 ^ (uint)&local_3ec);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00ce.c
// 00ceae80 FUN_00ceae80

void FUN_00ceae80(int param_1,short *param_2,int param_3,short *param_4,int *param_5)

{
  byte bVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  short *psVar5;
  int iVar6;
  int *local_50;
  int local_4c;
  int local_48;
  int local_44;
  int local_40;
  int local_3c;
  int local_38;
  short local_34;
  short sStack_32;
  short sStack_30;
  short local_2e;
  int local_28;
  int local_24;
  int local_20;
  int *local_1c;
  int local_18;
  int local_14 [4];
  uint local_4;
  
  local_4 = DAT_0197713c ^ (uint)&local_50;
  local_1c = param_5;
  local_44 = 0;
  local_24 = 0;
  local_40 = 0;
  local_3c = 0;
  local_34 = 0;
  local_38 = 1;
  sStack_32 = 0;
  sStack_30 = 0;
  local_2e = 0;
  FUN_00cd8720(param_2 + 4,0,param_1);
  local_18 = (int)(short)(local_2e - sStack_30);
  iVar3 = local_38 * local_40;
  if (iVar3 - local_18 == 0 || iVar3 < local_18) {
    local_20 = param_3 * 0x14;
    local_28 = (int)(short)(sStack_32 - local_34);
    do {
      local_14[0] = local_40 * (param_1 + 1) + local_3c;
      local_14[1] = local_14[0] + 1;
      local_14[3] = local_3c + (local_40 + 1) * (param_1 + 1);
      local_14[2] = local_14[3] + 1;
      iVar2 = (local_38 * local_3c + (int)local_34) - (int)*param_2;
      iVar6 = (int)(short)(param_2[1] - *param_2);
      iVar4 = (sStack_30 + iVar3) - (int)param_2[2];
      bVar1 = (byte)*(undefined4 *)(param_2 + 0x6e);
      local_50 = (int *)&DAT_0173e014;
      iVar3 = ((iVar6 >> (bVar1 & 0x1f)) + 1) * (iVar4 >> (bVar1 & 0x1f)) +
              (iVar2 >> (bVar1 & 0x1f));
      if (((*(byte *)((iVar3 >> 3) + *(int *)(param_2 + 0x56)) & (byte)(1 << ((byte)iVar3 & 7))) ==
           0) || (bVar1 = (byte)*(undefined4 *)(param_2 + 0x6e),
                 iVar3 = ((iVar6 >> (bVar1 & 0x1f)) + 1) * (iVar4 + local_38 >> (bVar1 & 0x1f)) +
                         (iVar2 + local_38 >> (bVar1 & 0x1f)),
                 (*(byte *)(*(int *)(param_2 + 0x56) + (iVar3 >> 3)) &
                 (byte)(1 << ((byte)iVar3 & 7))) == 0)) {
        local_50 = &DAT_0173dffc;
      }
      local_4c = *(int *)(*(int *)(param_2 + 0x2e) + 0x10 + local_20);
      iVar3 = (local_40 * param_1 + local_3c) * 2;
      bVar1 = *(byte *)((iVar3 + 1 >> 3) + local_4c);
      if ((*(byte *)((iVar3 >> 3) + local_4c) & (byte)(1 << ((byte)iVar3 & 7))) != 0) {
        *param_4 = (short)local_14[*local_50];
        param_4[1] = (short)local_14[local_50[1]];
        param_4[2] = (short)local_14[local_50[2]];
        param_4 = param_4 + 3;
        local_44 = local_44 + 3;
      }
      if ((bVar1 & (byte)(1 << ((byte)(iVar3 + 1) & 7))) != 0) {
        *param_4 = (short)local_14[local_50[3]];
        param_4[1] = (short)local_14[local_50[4]];
        param_4[2] = (short)local_14[local_50[5]];
        param_4 = param_4 + 3;
        local_44 = local_44 + 3;
      }
      local_3c = local_3c + 1;
      if (local_38 * local_3c - local_28 != 0 && local_28 <= local_38 * local_3c) {
        local_40 = local_40 + 1;
        local_3c = 0;
      }
      iVar3 = local_38 * local_40;
    } while (iVar3 - local_18 == 0 || iVar3 < local_18);
  }
  local_50 = (int *)((param_1 + 2) * param_1 + 1);
  local_48 = 0;
  do {
    psVar5 = &DAT_0173dfe4;
    if ((local_48 == 2) || (local_48 == 3)) {
      psVar5 = (short *)&DAT_0173dfcc;
    }
    if (0 < param_1) {
      local_20 = param_3 * 0x14;
      local_28 = param_1;
      local_4c = local_48;
      do {
        if ((*(byte *)(*(int *)(*(int *)(param_2 + 0x34) + 0x10 + local_20) + (local_4c >> 3)) &
            (byte)(1 << ((byte)local_4c & 7))) != 0) {
          *param_4 = *psVar5 + (short)local_50;
          param_4[1] = psVar5[2] + (short)local_50;
          param_4[2] = psVar5[4] + (short)local_50;
          param_4[3] = psVar5[6] + (short)local_50;
          param_4[4] = psVar5[8] + (short)local_50;
          param_4[5] = psVar5[10] + (short)local_50;
          param_4 = param_4 + 6;
          local_24 = local_24 + 6;
        }
        local_50 = (int *)((int)local_50 + 2);
        local_4c = local_4c + 4;
        local_28 = local_28 + -1;
      } while (local_28 != 0);
      local_28 = 0;
    }
    local_50 = (int *)((int)local_50 + 2);
    local_48 = local_48 + 1;
  } while (local_48 < 4);
  *local_1c = local_24 + local_44;
  __security_check_cookie(local_4 ^ (uint)&local_50);
  return;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d0.c
// 00d02bd0 FUN_00d02bd0

undefined4 * __thiscall
FUN_00d02bd0(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,undefined4 param_5
            ,int param_6)

{
  undefined4 *puVar1;
  undefined4 uVar2;
  
  if (DAT_019fbf60 == (int *)0x0) {
    puVar1 = __aligned_malloc(0x28,0x10);
    FUN_00afbc30(puVar1,0x16,0x28);
    if (DAT_019fbff8 != 0) {
      FUN_00afc4e0(0x16,puVar1,0x10);
    }
  }
  else {
    puVar1 = (undefined4 *)(**(code **)(*DAT_019fbf60 + 4))(0x28,0x10,0,0);
  }
  puVar1[8] = param_6;
  puVar1[6] = param_4;
  puVar1[7] = param_5;
  *(undefined1 *)(puVar1 + 5) = 0;
  if (*(int *)(param_1 + 0x6c) < 1) {
    uVar2 = FUN_00a7ac00(0x16,*(int *)(*(int *)(param_1 + 0x7c) + 0x10) * 2,0x10);
  }
  else {
    if (*(int *)(param_1 + 0x6c) == 0) {
      *(undefined4 *)(param_1 + 0x6c) = 1;
    }
    *(int *)(param_1 + 0x6c) = *(int *)(param_1 + 0x6c) + -1;
    uVar2 = *(undefined4 *)(*(int *)(param_1 + 0x68) + *(int *)(param_1 + 0x6c) * 4);
  }
  puVar1[4] = uVar2;
  puVar1[2] = uVar2;
  *puVar1 = param_3;
  puVar1[1] = param_2;
  puVar1[3] = 0;
  uVar2 = FUN_00b027f0(0xffffffff,0xffffffff,&LAB_00ceb3c0,puVar1,1,1);
  puVar1[9] = uVar2;
  if (*(uint *)(param_1 + 0x60) <= *(uint *)(param_1 + 0x5c)) {
    FUN_00ca7ef0((int)*(short *)(param_1 + 0x66));
  }
  *(undefined4 **)(*(int *)(param_1 + 0x58) + *(int *)(param_1 + 0x5c) * 4) = puVar1;
  *(int *)(param_1 + 0x5c) = *(int *)(param_1 + 0x5c) + 1;
  *(int *)(param_6 + 0x44) = *(int *)(param_6 + 0x44) + 1;
  return puVar1;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d0.c
// 00d02a80 FUN_00d02a80

undefined4 * __thiscall FUN_00d02a80(int param_1,undefined4 param_2,undefined4 param_3)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 *puVar3;
  undefined4 uVar4;
  undefined4 unaff_EBX;
  int iVar5;
  int iVar6;
  undefined4 unaff_EDI;
  
  if (DAT_019fbf60 == (int *)0x0) {
    puVar3 = __aligned_malloc(0x4c,0x10);
    FUN_00afbc30(puVar3,0x16,0x4c);
    if (DAT_019fbff8 != 0) {
      FUN_00afc4e0(0x16,puVar3,0x10);
    }
  }
  else {
    puVar3 = (undefined4 *)(**(code **)(*DAT_019fbf60 + 4))(0x4c,0x10,0,0);
  }
  puVar3[0xf] = param_2;
  puVar3[0x11] = 1;
  puVar3[0x10] = param_3;
  *(undefined1 *)(puVar3 + 0xe) = 0;
  iVar6 = (*(int *)(param_1 + 0xd0) + 9) * (*(int *)(param_1 + 0xd0) + 1);
  iVar5 = *(int *)(*(int *)(param_1 + 0x80) + 0xd8) * iVar6;
  uVar4 = (**(code **)(**(int **)(DAT_019fdfb4 + 0x10) + 4))(iVar5,0x10,0,0);
  puVar3[10] = uVar4;
  puVar3[0xb] = iVar5;
  puVar3[0xc] = iVar6;
  puVar3[0xd] = unaff_EDI;
  puVar3[5] = puVar3[10];
  uVar1 = *(undefined4 *)(param_1 + 0xd0);
  uVar4 = *(undefined4 *)(param_1 + 0xc4);
  puVar3[2] = *(undefined4 *)(param_1 + 0xc0);
  uVar2 = DAT_0173b064;
  *puVar3 = unaff_EBX;
  puVar3[1] = uVar1;
  puVar3[3] = uVar4;
  puVar3[4] = uVar2;
  puVar3[6] = 0;
  *(undefined8 *)(puVar3 + 7) = DAT_019f4e88;
  puVar3[9] = DAT_019f4e90;
  uVar4 = FUN_00b027f0(0xffffffff,0xffffffff,&LAB_00cebc10,puVar3,1,1);
  puVar3[0x12] = uVar4;
  if (*(uint *)(param_1 + 0x50) <= *(uint *)(param_1 + 0x4c)) {
    FUN_00ca7e70((int)*(short *)(param_1 + 0x56));
  }
  *(undefined4 **)(*(int *)(param_1 + 0x48) + *(int *)(param_1 + 0x4c) * 4) = puVar3;
  *(int *)(param_1 + 0x4c) = *(int *)(param_1 + 0x4c) + 1;
  return puVar3;
}


// SOURCE C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp\unnamed_00d2.c
// 00d21050 FUN_00d21050

void __thiscall FUN_00d21050(int param_1,int param_2)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  int *piVar4;
  int iVar5;
  undefined4 *puVar6;
  int iVar7;
  uint local_8;
  
  iVar3 = param_2;
  *(undefined1 *)(param_2 + 0x79) = 1;
  piVar4 = (int *)FUN_00afdf70(0x16,0x54);
  if (piVar4 != (int *)0x0) {
    *(undefined2 *)(piVar4 + 3) = 0x16;
    *piVar4 = 0;
    piVar4[2] = 0;
    piVar4[1] = 0;
    *(undefined2 *)((int)piVar4 + 0xe) = 0xffff;
    piVar4[4] = 0;
    piVar4[5] = 0;
    *(undefined2 *)(piVar4 + 0x14) = 0xffff;
    *(undefined1 *)((int)piVar4 + 0x52) = 0;
    *(undefined1 *)((int)piVar4 + 0x52) = 0;
  }
  *(byte *)((int)piVar4 + 0x52) = *(byte *)((int)piVar4 + 0x52) & 0xfb;
  *(undefined2 *)(piVar4 + 6) = *(undefined2 *)(param_2 + 8);
  *(undefined2 *)((int)piVar4 + 0x1a) = *(undefined2 *)(param_2 + 10);
  *(undefined2 *)((int)piVar4 + 0x1e) = *(undefined2 *)(param_2 + 0xe);
  *(undefined2 *)(piVar4 + 7) = *(undefined2 *)(param_2 + 0xc);
  *(byte *)((int)piVar4 + 0x52) = *(byte *)((int)piVar4 + 0x52) & 0xfb;
  *(undefined8 *)(piVar4 + 8) = *(undefined8 *)(param_2 + 0x10);
  *(undefined8 *)(piVar4 + 10) = *(undefined8 *)(param_2 + 0x18);
  *(undefined8 *)(piVar4 + 0xc) = *(undefined8 *)(param_2 + 0x20);
  *(undefined8 *)(piVar4 + 0xe) = *(undefined8 *)(param_2 + 0x28);
  *(undefined8 *)(piVar4 + 0x10) = *(undefined8 *)(param_2 + 0x30);
  iVar1 = *(int *)(param_2 + 0x3c);
  piVar4[0x12] = *(int *)(param_2 + 0x38);
  piVar4[0x13] = iVar1;
  iVar5 = FUN_00d02a80(param_2,piVar4);
  local_8 = CONCAT31(local_8._1_3_,*(byte *)(param_2 + 0x7a) >> 1) & 0xffffff01;
  iVar1 = *(int *)(param_2 + 0x58);
  iVar7 = 0;
  if (0 < iVar1) {
    param_2 = 0;
    do {
      if ((*(int *)(*(int *)(iVar3 + 0x5c) + 8 + param_2) != 0) ||
         (*(int *)(*(int *)(iVar3 + 0x68) + 8 + param_2) != 0)) {
        puVar6 = (undefined4 *)FUN_00afdf70(0x16,0x60);
        uVar2 = DAT_013be4a0;
        if (puVar6 != (undefined4 *)0x0) {
          *puVar6 = 0;
          puVar6[1] = 0;
          puVar6[2] = 0;
          puVar6[3] = 0;
          puVar6[4] = 0;
          puVar6[8] = uVar2;
          puVar6[0xb] = 0;
          puVar6[0xc] = 0;
          puVar6[0xd] = 0;
          puVar6[0xe] = 0;
          puVar6[0x12] = uVar2;
          *(undefined1 *)(puVar6 + 0x16) = 0;
        }
        puVar6[4] = 0xffffffff;
        FUN_00cbb4c0(iVar3,puVar6,iVar7,local_8);
        if ((*(byte *)(iVar3 + 0x7a) & 1) == 0) {
          puVar6[2] = *(undefined4 *)(param_1 + 0x7c);
          if ((uint)piVar4[2] <= (uint)piVar4[1]) {
            FUN_00ca7890((int)*(short *)((int)piVar4 + 0xe));
          }
          *(undefined4 **)(*piVar4 + piVar4[1] * 4) = puVar6;
          piVar4[1] = piVar4[1] + 1;
        }
        else {
          FUN_00d02bd0(iVar7,iVar3,piVar4,puVar6,iVar5);
        }
      }
      iVar7 = iVar7 + 1;
      param_2 = param_2 + 0x14;
    } while (iVar7 < iVar1);
  }
  *(int *)(iVar5 + 0x44) = *(int *)(iVar5 + 0x44) + -1;
  return;
}

