from pathlib import Path
r=Path.home()/"Documents/Opem Amalur/work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:70]
    return s.replace(a,b,1)
edit(r/"android_scene.cmake",lambda s:rep(s,"oa_actors.c oa_actor_ai.c","oa_actors.c oa_actor_ai.c oa_nav.c"))
edit(r/"CMakeLists.txt",lambda s:rep(s,"add_executable(oa-actor-ai-test oa_actor_ai_test.c oa_actor_ai.c)\nif(NOT WIN32)\n  target_link_libraries(oa-actor-ai-test PRIVATE m)\nendif()\n","add_executable(oa-actor-ai-test oa_actor_ai_test.c oa_actor_ai.c)\nadd_executable(oa-nav-test oa_nav_test.c oa_nav.c)\nif(NOT WIN32)\n  target_link_libraries(oa-actor-ai-test PRIVATE m)\n  target_link_libraries(oa-nav-test PRIVATE m)\nendif()\n"))
def val(s):
    s=rep(s,"oa-menu-test oa-actor-ai-test","oa-menu-test oa-actor-ai-test oa-nav-test")
    s=rep(s,"work\\v19-host\\build-windows\\oa-menu-test.exe","work\\v19-host\\build-windows\\oa-nav-test.exe > outputs\\scene-v19\\nav-tests.txt 2>&1\nif errorlevel 1 exit /b %errorlevel%\nwork\\v19-host\\build-windows\\oa-menu-test.exe")
    return s
edit(r/"build_validate.cmd",val)
def scene(s):
    return rep(s,'rays=%u capsules=%u update_ms=%.2f update_worst_ms=%.2f",as.total,as.near_count,as.moving,as.chasing,as.slots,as.drawn,as.models,as.rays,as.capsules,as.update_ms,as.update_worst','rays=%u capsules=%u paths=%u update_ms=%.2f update_worst_ms=%.2f",as.total,as.near_count,as.moving,as.chasing,as.slots,as.drawn,as.models,as.rays,as.capsules,as.paths,as.update_ms,as.update_worst')
edit(r/"android_scene.c",scene)
print("ok")
