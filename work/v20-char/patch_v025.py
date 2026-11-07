"""Version 0.25.0: Veil inventory, items, weapon models, potions and loot."""
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
def edit(path, pairs):
    f = Path(path) if Path(path).is_absolute() else host / path
    t = f.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (path, old[:90], t.count(old)))
        t = t.replace(old, new)
    f.write_bytes(t.encode("utf-8"))
# Earlier edits of this version were applied by the first, stopped run.
edit("oa_combat.c", [("c->player_hp-=FOE_DAMAGE", "c->player_hp-=c->foe_damage")])
edit("oa_character.h", [(" int ready;\n}oa_character;", " /* Parts not drawn, one bit each; used to swap weapon models. */\n uint32_t hidden;\n int ready;\n}oa_character;")])
edit("oa_character_gl.c", [("for(i=0;i<c->part_count;i++){const oa_char_part *p=c->parts+i;uint32_t n=oa_character_bones(c,p,rows);", "for(i=0;i<c->part_count;i++){const oa_char_part *p=c->parts+i;uint32_t n;if(c->hidden&(1u<<i))continue;n=oa_character_bones(c,p,rows);")])
# Bake all five material longswords. The first stays steel, so existing tests and the default look hold.
b = root / "work/v20-char/build_character.py"; t = b.read_text()
t = t.replace('def sword_part():\n    """Sword as a rigid part on RGTHAND_ATTACH. Its vertices are used directly in that joint\'s space."""\n    fid = 1327249\n', 'def sword_part(fid):\n    """Sword as a rigid part on RGTHAND_ATTACH. Its vertices are used directly in that joint\'s space."""\n')
a = t.index("sword_verts, sword_inds, sword_entries = sword_part()")
z = t.index('blob += struct.pack("<IIII", J, len(clips), len(parts), len(textures))')
block = t[a:z]
block = block.replace("sword_part()", "sword_part(next(int(k) for k, v in syms[\"fab\"].items() if v == sword_name))").replace('v == "02_steel_sword_1h"', "v == sword_name").replace('parts.append(("sword", ', 'parts.append((sword_name, ').replace('dict(label="sword", ', "dict(label=sword_name, ")
block = "# Order is oa_items.h's weapon model index; every model is hidden but the equipped one.\nfor sword_name in (\"02_steel_sword_1h\", \"01_iron_sword_1h\", \"03_azurite_sword_1h\", \"04_sylvanite_sword_1h\", \"05_prismere_sword_1h\"):\n" + "".join("    " + line + "\n" if line else "\n" for line in block.splitlines())
t = t[:a] + block + t[z:]
t = t.replace('colors = {"sword": (255, 40, 40), ', 'colors = {"02_steel_sword_1h": (255, 40, 40), "01_iron_sword_1h": (255, 40, 40), "03_azurite_sword_1h": (255, 40, 40), "04_sylvanite_sword_1h": (255, 40, 40), "05_prismere_sword_1h": (255, 40, 40), ')
b.write_text(t)
edit("android_scene.c", [
 ('#include "oa_menu.h"\n', '#include "oa_menu.h"\n#include "oa_items.h"\n'),
 ("        view.show_hud=!(__system_property_get", """        {static oa_reagent_row rows[OA_REAGENT_ROWS];static char names[OA_REAGENT_ROWS][64];size_t i;int n=0;
         if(menu->screen==OA_SCREEN_INVENTORY&&interaction)for(i=0;i<interaction->catalog.reagent_count&&n<OA_REAGENT_ROWS;i++){uint32_t have=oa_inventory_count(&interaction->inventory,interaction->catalog.reagents[i].id);if(have){reagent_display(interaction->catalog.reagents[i].symbol,names[n],sizeof(names[n]));rows[n].name=names[n];rows[n].count=have;n++;}}
         view.reagents=rows;view.reagent_count=n;}
        view.show_hud=!(__system_property_get"""),
 ("static int graphics_draw(graphics *g,", """enum{OA_REAGENT_ROWS=96};
/* Symbols are engine identifiers; shows them in words until they are matched to the game's text. */
static void reagent_display(const char *symbol,char *out,size_t cap){size_t i=0;int start=1;const char *s=symbol;if(!strncmp(s,"reagentsource_",14))s+=14;else if(!strncmp(s,"reagent_",8))s+=8;
    for(;*s&&i+1<cap;s++){char c=*s=='_'?' ':*s;if(c==' '){start=1;out[i++]=c;continue;}out[i++]=start?(char)toupper((unsigned char)c):c;start=0;}out[i]=0;}
static int graphics_draw(graphics *g,"""),
 ("                if(playing)oa_npcs_update(&c.npcs,dt);\n", """                /* Equipped items drive combat, the visible weapon and potion healing. */
                c.combat.player_damage=oa_bag_damage(&menu.bag);c.combat.foe_damage=9.f*oa_armor_scale(oa_bag_armor(&menu.bag));
                if(menu.heal_request>0){c.combat.player_hp=clampf(c.combat.player_hp+menu.heal_request,0,c.combat.player_max);menu.heal_request=0;}
                if(c.character.part_count>=OA_WEAPON_MODELS){unsigned base=c.character.part_count-OA_WEAPON_MODELS,m;c.character.hidden=0;for(m=0;m<OA_WEAPON_MODELS;m++)if((int)m!=oa_bag_weapon_model(&menu.bag))c.character.hidden|=1u<<(base+m);}
                if(c.foe_ready){int down=c.combat.foe==OA_FOE_DEAD;if(down&&!foe_down){static char loot[64];unsigned coin=12+(unsigned)(rand()%19);menu.bag.gold+=coin;if(rand()%2){oa_bag_add(&menu.bag,OA_ITEM_MINOR_POTION,1);snprintf(loot,sizeof(loot),"Bandit dropped %u gold and a Minor Healing Potion",coin);}else snprintf(loot,sizeof(loot),"Bandit dropped %u gold",coin);oa_menu_status(&menu,loot);LOGI("Loot %s",loot);}foe_down=down;}
                if(playing)oa_npcs_update(&c.npcs,dt);
"""),
 ("int pending_load=0,applied_rate=-1;", "int pending_load=0,applied_rate=-1,foe_down=0;"),
 ("                    case OA_ACTION_NEW_GAME:c.spawn_hint=NULL;pending_load=0;oa_menu_open(&menu,OA_SCREEN_GAME);", "                    case OA_ACTION_NEW_GAME:c.spawn_hint=NULL;pending_load=0;oa_bag_new(&menu.bag);oa_menu_open(&menu,OA_SCREEN_GAME);"),
 ("case OA_ACTION_LOAD:if(oa_save_read(&loaded,menu.save_path)){c.spawn_hint=loaded.feet;", "case OA_ACTION_LOAD:if(oa_save_read(&loaded,menu.save_path)){menu.bag=loaded.bag;c.spawn_hint=loaded.feet;"),
 ("save.health=c.combat.player_hp;", "save.health=c.combat.player_hp;save.bag=menu.bag;"),
])
t = (host / "android_scene.c").read_text()
if "#include <ctype.h>" not in t:
    (host / "android_scene.c").write_text(t.replace('#include "oa_menu.h"\n', '#include "oa_menu.h"\n#include <ctype.h>\n', 1))
print("patched")
