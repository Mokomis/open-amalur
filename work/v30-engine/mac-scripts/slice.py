import sys; sys.path.insert(0, sys.argv[1]); import sheet, os
P=sys.argv[2]; A=sys.argv[3]
def cut(src,name,x,y,w,h):
    c=sheet.crop(src,x,y,w,h); sheet.wr(f"{A}/{name}.png",*c)
hud=sheet.rd(f"{P}/ui_hud.png"); pz=sheet.rd(f"{P}/ui_pause_menu.png")
cut(hud,"hud_hilt",580,192,346,100); cut(hud,"hud_ring",330,2,190,194); cut(hud,"hud_socket",132,186,86,90); cut(hud,"hud_orb",2,172,114,114)
cut(hud,"hud_red",583,391,200,14); cut(hud,"hud_fate",583,405,236,14); cut(hud,"hud_mana",632,493,200,15); cut(hud,"hud_skull",905,65,46,50)
cut(pz,"knot_band",0,0,640,47); cut(pz,"knot_corner",0,50,516,84); cut(pz,"diamond",128,333,34,30); cut(pz,"coin_gold",772,480,32,32); cut(pz,"coin_silver",772,445,32,32); cut(pz,"anvil",784,230,64,66); cut(pz,"hourglass",884,362,54,58)
thin=sheet.rd(f"{P}/ui_expander_thin.png")
fw,fh,fd=sheet.crop(thin,14,14,386,470)
for gx in (156,157,158,224,225,226,227):
    for y in range(fh): fd[(y*fw+gx)*4:(y*fw+gx)*4+4]=fd[(y*fw+gx-6)*4:(y*fw+gx-6)*4+4]
for gy in (162,163,164,165,301,302,303,304):
    fd[gy*fw*4:(gy+1)*fw*4]=fd[(gy-7)*fw*4:(gy-6)*fw*4]
sheet.wr(f"{A}/frame_iron.png",fw,fh,fd)
for i in range(3): pass
cv=sheet.rd(f"{P}/ui_conversation_radial.png")
for i,n in enumerate(["gl_swords","gl_armor","gl_coins","gl_dragon"]): cut(cv,n,257+63*i,0,62,63)
for i,n in enumerate(["gl_hammer","gl_mortar"]): cut(cv,n,257+63*i,64,62,63)
wc=sheet.rd(f"{P}/ui_icons_inv_weapons_armor.png"); ar=sheet.rd(f"{P}/ui_icons_inv_armor_01.png"); it=sheet.rd(f"{P}/ui_icons_inv_items.png"); co=sheet.rd(f"{P}/ui_icons_inv_weapons_common.png"); c2=sheet.rd(f"{P}/ui_icons_inv_weapons_common_02.png")
ic={"i_sword":(wc,4,2),"i_fallen":(wc,3,2),"i_kellerac":(wc,7,0),"i_greatsw":(wc,2,2),"i_hammer":(wc,6,2),"i_chakram":(wc,4,5),"i_bow":(wc,0,4),"i_faeblade":(co,0,0),"i_staff":(co,2,1),"i_kite":(c2,0,2),"i_buckler":(c2,3,1),
"i_hood":(ar,0,0),"i_cuirass":(ar,6,0),"i_cuirass2":(ar,3,4),"i_gaunt":(ar,5,5),"i_gaunt2":(ar,0,5),"i_legs":(ar,7,1),"i_greaves":(ar,0,3),"i_boots":(ar,2,7),"i_helm":(ar,1,3),
"i_redpot":(it,2,3),"i_bluepot":(it,0,4),"i_goldpile":(it,6,0),"i_ring":(it,1,13),"i_ring2":(it,3,13),"i_gem":(it,0,13)}
for n,(s,cx,cy) in ic.items(): cut(s,n,cx*64,cy*64,64,64)
