from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
p = host / "android_scene.c"
t = p.read_bytes().decode()
a = t.index("                    {static int64_t logged;if(now-logged>1000)")
b = t.index("\n", a) + 1
t = t[:a] + t[b:]
old = "if(f->foe==OA_FOE_CHASE&&(f->foe_vx!=0||f->foe_vy!=0)){if(opem_controller_step(c.world,&c.body_config,&c.foe_body,f->foe_vx,f->foe_vy,dt,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));}"
assert t.count(old) == 1
new = """if(f->foe==OA_FOE_CHASE&&(f->foe_vx!=0||f->foe_vy!=0)){
                        /* Authored steering: when progress stalls against an obstacle, veer aside for a moment. */
                        float vx=f->foe_vx,vy=f->foe_vy,before[2]={c.foe_body.feet[0],c.foe_body.feet[1]};
                        if(c.foe_detour>0){float a=c.foe_detour_side*1.2f,ca=cosf(a),sa=sinf(a),rx=vx*ca-vy*sa;vy=vx*sa+vy*ca;vx=rx;c.foe_detour-=dt;}
                        if(opem_controller_step(c.world,&c.body_config,&c.foe_body,vx,vy,dt,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));
                        {float mx=c.foe_body.feet[0]-before[0],my=c.foe_body.feet[1]-before[1],wanted=sqrtf(vx*vx+vy*vy)*dt;
                         c.foe_stuck=(wanted>.01f&&mx*mx+my*my<wanted*wanted*.09f)?c.foe_stuck+dt:0;
                         if(c.foe_stuck>.3f&&c.foe_detour<=0){c.foe_detour=1.1f;c.foe_detour_side=c.foe_detour_side>0?-1.f:1.f;c.foe_stuck=0;}}}"""
t = t.replace(old, new)
old = "    int foe_ready;\n"
assert t.count(old) == 1
t = t.replace(old, "    int foe_ready;\n    float foe_detour,foe_detour_side,foe_stuck;\n")
p.write_bytes(t.encode())
print("ok")
