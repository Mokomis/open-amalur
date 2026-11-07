// 00a94b90 FUN_00a94b90

void __fastcall FUN_00a94b90(int param_1)

{
  uint uVar1;
  undefined1 auStack_154 [3];
  undefined1 local_151;
  int local_150;
  int local_14c;
  int local_148;
  int *local_144;
  int local_140;
  int *local_13c;
  uint local_138;
  undefined1 local_134 [12];
  undefined1 local_128 [12];
  undefined1 local_11c [12];
  undefined1 local_110 [12];
  undefined1 local_104 [64];
  undefined1 local_c4 [64];
  undefined1 local_84 [64];
  undefined1 local_44 [64];
  uint local_4;
  
  local_4 = DAT_0197713c ^ (uint)auStack_154;
  local_140 = param_1 + 4;
  local_148 = param_1 + 0x14;
  local_150 = param_1 + 0x24;
  local_14c = param_1 + 0x34;
  local_144 = (int *)(param_1 + 0x54);
  local_13c = (int *)(param_1 + 100);
  uVar1 = 0;
  do {
    FUN_0104ef20(local_104,0x40,"/gamebuild/bigs/%03d/",*(undefined4 *)((int)&DAT_01961040 + uVar1))
    ;
    FUN_0104ef20(local_84,0x40,"/gamebuild/content/%03d/",
                 *(undefined4 *)((int)&DAT_01961040 + uVar1));
    FUN_0104ef20(local_c4,0x40,".\\%03d\\",*(undefined4 *)((int)&DAT_01961040 + uVar1));
    FUN_0104ef20(local_44,0x40,&DAT_017302c4,*(undefined4 *)((int)&DAT_01961040 + uVar1));
    FUN_00af4d40(local_104);
    if (*(uint *)(local_140 + 8) <= *(uint *)(local_140 + 4)) {
      FUN_00a915a0((int)*(short *)(local_140 + 0xe));
    }
    *(int *)(local_140 + 4) = *(int *)(local_140 + 4) + 1;
    FUN_00af3740(local_110);
    FUN_00af2060();
    FUN_00af4d40(local_84);
    if (*(uint *)(local_148 + 8) <= *(uint *)(local_148 + 4)) {
      FUN_00a915a0((int)*(short *)(local_148 + 0xe));
    }
    *(int *)(local_148 + 4) = *(int *)(local_148 + 4) + 1;
    FUN_00af3740(local_11c);
    FUN_00af2060();
    FUN_00af4d40(local_c4);
    if (*(uint *)(local_150 + 8) <= *(uint *)(local_150 + 4)) {
      FUN_00a915a0((int)*(short *)(local_150 + 0xe));
    }
    *(int *)(local_150 + 4) = *(int *)(local_150 + 4) + 1;
    FUN_00af3740(local_128);
    FUN_00af2060();
    FUN_00af4d40(local_44);
    if (*(uint *)(local_14c + 8) <= *(uint *)(local_14c + 4)) {
      FUN_00a915a0((int)*(short *)(local_14c + 0xe));
    }
    *(int *)(local_14c + 4) = *(int *)(local_14c + 4) + 1;
    FUN_00af3740(local_134);
    FUN_00af2060();
    if (*(uint *)(param_1 + 0x4c) <= *(uint *)(param_1 + 0x48)) {
      FUN_00a1aeb0((int)*(short *)(param_1 + 0x52));
    }
    *(undefined4 *)(*(int *)(param_1 + 0x44) + *(int *)(param_1 + 0x48) * 4) =
         *(undefined4 *)((int)&DAT_01961040 + uVar1);
    *(int *)(param_1 + 0x48) = *(int *)(param_1 + 0x48) + 1;
    local_138 = (uint)((&DAT_01961044)[uVar1] != '\0');
    if ((uint)local_144[2] <= (uint)local_144[1]) {
      FUN_00a67820((int)*(short *)((int)local_144 + 0xe));
    }
    *(uint *)(*local_144 + local_144[1] * 4) = local_138;
    local_144[1] = local_144[1] + 1;
    if ((uint)local_13c[2] <= (uint)local_13c[1]) {
      FUN_00a8bce0((int)*(short *)((int)local_13c + 0xe));
    }
    *(undefined1 *)(local_13c[1] + *local_13c) = (&DAT_01961045)[uVar1];
    local_13c[1] = local_13c[1] + 1;
    if (*(uint *)(param_1 + 0x7c) <= *(uint *)(param_1 + 0x78)) {
      FUN_00a1aeb0((int)*(short *)(param_1 + 0x82));
    }
    *(undefined4 *)(*(int *)(param_1 + 0x74) + *(int *)(param_1 + 0x78) * 4) =
         *(undefined4 *)((int)&DAT_01961048 + uVar1);
    *(int *)(param_1 + 0x78) = *(int *)(param_1 + 0x78) + 1;
    local_151 = *(int *)((int)&DAT_01961048 + uVar1) < 0;
    if (*(uint *)(param_1 + 0x8c) <= *(uint *)(param_1 + 0x88)) {
      FUN_00a8bce0((int)*(short *)(param_1 + 0x92));
    }
    *(undefined1 *)(*(int *)(param_1 + 0x84) + *(int *)(param_1 + 0x88)) = local_151;
    *(int *)(param_1 + 0x88) = *(int *)(param_1 + 0x88) + 1;
    uVar1 = uVar1 + 0xc;
  } while (uVar1 < 0x84);
  __security_check_cookie(local_4 ^ (uint)auStack_154);
  return;
}


