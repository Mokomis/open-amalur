/* Link against the patched Lua 5.1 library used by the Android viewer.
 * Usage: lua_weak_mode_test path/to/lua_weak_mode_test.lua
 * This exercises library initialization and actual collector behavior. */
#include <stdio.h>
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"

int main(int argc, char **argv) {
  int pass;
  if (argc != 2) {
    fprintf(stderr, "usage: %s lua_weak_mode_test.lua\n", argv[0]);
    return 2;
  }
  for (pass = 0; pass < 8; ++pass) {
    lua_State *L = luaL_newstate();
    if (!L) { fprintf(stderr, "allocation failed\n"); return 2; }
    luaL_openlibs(L);
    if (luaL_loadfile(L, argv[1]) || lua_pcall(L, 0, 0, 0)) {
      fprintf(stderr, "pass %d: %s\n", pass, lua_tostring(L, -1));
      lua_close(L);
      return 1;
    }
    lua_close(L);
  }
  puts("Lua startup and weak-mode regression: 8 passes");
  return 0;
}
