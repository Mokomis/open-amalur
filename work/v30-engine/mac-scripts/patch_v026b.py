from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
old = 'c->collision_ready=0;c->walking=0;exploration_input_clear(input);LOGE("Exploration collision step stopped: %s",error);exploration_pose_log(c,"step_failure",1);'
assert t.count(old) == 1
new = '''{char retry[256];opem_controller safe;LOGE("Exploration collision step stopped: %s feet=(%.0f %.0f %.0f)",error,c->body.feet[0],c->body.feet[1],c->body.feet[2]);
                /* Rough terrain can fail validation. Stand again at the last safe spot rather than ending control. */
                if(opem_controller_spawn(c->world,&c->body_config,c->body.last_safe_feet,&safe,retry,sizeof(retry))){c->body=safe;}
                else{c->collision_ready=0;c->walking=0;exploration_input_clear(input);LOGE("Exploration recovery failed: %s",retry);exploration_pose_log(c,"step_failure",1);}}'''
t = t.replace(old, new)
f.write_bytes(t.encode("utf-8")); print("ok")
