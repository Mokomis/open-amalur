from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"
t = f.read_bytes().decode("utf-8")
old = 'if(rand()%2){oa_bag_add(&menu.bag,OA_ITEM_MINOR_POTION,1);snprintf(loot,sizeof(loot),"Bandit dropped %u gold and a Minor Healing Potion",coin);}else snprintf(loot,sizeof(loot),"Bandit dropped %u gold",coin);'
new = '''{int roll=rand()%100,item=-1;/* Authored loot odds, so every item can be earned. */
                    if(roll<30)item=OA_ITEM_IRON+rand()%(OA_ITEM_ZODIAC_BOOTS-OA_ITEM_IRON+1);else if(roll<70)item=OA_ITEM_MINOR_POTION+(roll<45?1:0);
                    if(item>=0){oa_bag_add(&menu.bag,item,1);snprintf(loot,sizeof(loot),"Bandit dropped %u gold and %s",coin,oa_item_get(item)->name);}else snprintf(loot,sizeof(loot),"Bandit dropped %u gold",coin);}'''
if t.count(old) != 1: raise SystemExit("loot match")
f.write_bytes(t.replace(old, new).encode("utf-8")); print("patched")
