from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
f = host / "oa_character_gl.c"; t = f.read_bytes().decode("utf-8")
old = 'if(g->mvp<0||g->bones<0||!opem_room_lighting_open(&g->lights,g->program,outdoor)){LOGE("Character uniforms unavailable");oa_character_gpu_close(g);return 0;}'
assert t.count(old) == 1
t = t.replace(old, old + '\n /* A shadow sampler sharing the base texture unit makes every draw invalid, even when shadows are off. */\n glUseProgram(g->program);glUniform1i(glGetUniformLocation(g->program,"room_shadow_map"),3);glUniform1i(glGetUniformLocation(g->program,"room_shadow_on"),0);')
f.write_bytes(t.encode("utf-8"))
f = host / "android_scene.c"; t = f.read_bytes().decode("utf-8")
old = "if(next_world){opem_collision_destroy(c.world);c.world=next_world;}}"
assert t.count(old) == 1
t = t.replace(old, 'if(next_world){int64_t swap_t=now_ns();opem_collision_destroy(c.world);c.world=next_world;LOGI("Stream collision swap feet=(%.0f %.0f) ms=%.2f",c.body.feet[0],c.body.feet[1],(now_ns()-swap_t)/1e6);}}')
f.write_bytes(t.encode("utf-8")); print("ok")
