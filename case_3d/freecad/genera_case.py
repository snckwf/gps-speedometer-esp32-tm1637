# -*- coding: utf-8 -*-
# genera_case.py - Case tachimetro GPS "pebble" a cuneo morbido (v4)
# ESP32 DevKit 51x28 + GY-GPSV3-NEO (scheda 36x26 + antenna 25x25 appese al coperchio) + TM1637 0.36" (PCB 45x23, spessore 9) + LED 5 mm
# Da FreeCAD:  exec(open(r"A:\FreeCAD\case_tachimetro_gps\genera_case.py", encoding="utf-8").read())
import math, os
import FreeCAD as App, Part
from FreeCAD import Vector as V

# ================= PARAMETRI (mm) =================
wall = 2.0; floor_t = 2.0; lid_t = 3.2
ox = 86.0; oy = 64.0; H = 38.0          # (alzato di 6 mm il 10/11/2026 per i Dupont) esterno: larghezza X, profondita' Y, altezza base (coperchio escluso)
tilt = 15.0                             # inclinazione pannello frontale (gradi verso dietro)
R = 12.0                                # raggio grande degli angoli in pianta
r_top = 2.2; r_bot = 1.5                # raccordi bordo superiore / inferiore
post_r = 4.6; post_emb = 1.2            # colonne viti coperchio: raggio, e quanto affondano nella parete
pilot_d = 2.6; screw_d = 3.4
clr = 0.3
# --- ESP32 DevKit (misurato 51 x 28) ---
esp_l, esp_w, esp_h = 51.0, 28.0, 3.0   # ESP32 DevKit 30 pin USB-C (HW-394) 51 x 28; esp_h = PCB dal fondo: senza pin (fili saldati) = 3
esp_x, esp_y = 3.0, 21.0               # scheda contro la parete sinistra: la USB-C esce dal foro nella parete
usb_w, usb_h = 12.0, 8.0
esp_hole_x, esp_hole_y = 47.4, 23.8        # interasse fori di fissaggio della scheda
esp_post_rb = 4.6; esp_post_r = 3.0; esp_pilot_d = 2.1        # colonnine d6, foro pilota per viti M2,5 autofilettanti
# --- GY-GPSV3-NEO: scheda 36x26 + antenna ceramica 25x25 separata ---
pcbg_l, pcbg_w, pcbg_t = 36.0, 26.0, 5.5
ant_l, ant_w, ant_t = 25.0, 25.0, 7.0   # spessore antenna: misura con il calibro
gps_x, gps_y = 6.0, 22.6; gps_gap = 0.4
rail_t = 2.4; rail_fl = 3.0             # guide GPS: spessore e svasatura 45 gradi alla radice (rinforzo)
lip_gps = 2.0; lip_t = 2.4              # labbri che reggono scheda e antenna
# --- TM1637 0.36" 4 cifre (misurato: PCB 45x23, corpo display 30x14, spessore totale 9) ---
pcb_w, pcb_h = 45.0, 23.0
mod_tot = 9.0
mod_x = 13.5; mod_z0 = 6.6          # modulo TM1637 in posizione originale (urta il pilone del coperchio se spostato); finestra spostata con win_dx. a destra (vista frontale) il 08/11/2026
win_dx = 12.0                           # finestra/cornice: posizione originale (disp_cx 20,1 = 14,1+6) + 6 mm a destra (vista frontale), 08/11/2026
disp_cx = 14.1; disp_dz = -2.2          # centro cifre dal lato sinistro del PCB (opposto ai fili) e scarto in basso
win_w, win_h = 29.6, 12.4               # finestra sulle cifre
lip = 1.8; lw = 1.2; pad = 5.0          # guide del PCB display
bezel_b = 4.0; bezel_h = 2.0; bezel_r = 7.5
led_x = 67.5; led_d = 5.1; led_flange_d = 6.1; led_ring_d = 12.0
vent_d = 4.4; vent_pitch = 7.0
engrave = 0.6

# ================= SUPPORTO =================
for n in list(App.listDocuments().keys()):
    if n.startswith("case_tachimetro_gps"):
        App.closeDocument(n)
doc = App.newDocument("case_tachimetro_gps")
a_ = math.radians(tilt); ta = math.tan(a_); ca = math.cos(a_)
def yf_in(z): return wall/ca + z*ta
def T(s):
    s = s.copy(); s.rotate(V(0,0,0), V(1,0,0), -tilt); return s
def prism_x(pts, x0, x1):
    p = [V(x0, y, z) for (y, z) in pts]; p.append(p[0])
    return Part.Face(Part.makePolygon(p)).extrude(V(x1-x0, 0, 0))
def bx(L, W, Hh, x, y, z): return Part.makeBox(L, W, Hh, V(x, y, z))
def rbox_y(x0, z0, w, h, ya, yb, r):
    b = Part.makeBox(w, yb-ya, h, V(x0, ya, z0))
    ed = [e for e in b.Edges if abs(e.Vertexes[0].Point.y - e.Vertexes[1].Point.y) > 1e-6]
    return b.makeFillet(r, ed)
def fuse(lst):
    return lst[0].multiFuse(lst[1:]) if len(lst) > 1 else lst[0]
def corner_edges(s, dz=0.5):
    return [e for e in s.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) > dz
            and abs(e.Vertexes[0].Point.x - e.Vertexes[-1].Point.x) < 1e-6]
def level_edges(s, z):
    return [e for e in s.Edges if all(abs(v.Z - z) < 1e-4 for v in e.Vertexes)]
def cav_prism(inset, z0, z1, r):
    pts = [(yf_in(z0)+inset/ca, z0), (oy-wall-inset, z0), (oy-wall-inset, z1), (yf_in(z1)+inset/ca, z1)]
    s = prism_x(pts, wall+inset, ox-wall-inset)
    return s.makeFillet(r, corner_edges(s))

# ================= CORPO ESTERNO MORBIDO =================
zt = H + lid_t
full = prism_x([(0,0), (oy,0), (oy,zt), (zt*ta,zt)], 0, ox)
full = full.makeFillet(R, corner_edges(full, 1.0))
full = full.makeFillet(r_top, level_edges(full, zt))
full = full.makeFillet(r_bot, level_edges(full, 0.0))
big = Part.makeBox(ox+2, oy+2, H, V(-1, -1, 0))
base_solid = full.common(big)
lid_outer = full.common(Part.makeBox(ox+2, oy+2, lid_t+1, V(-1, -1, H)))
cavity = cav_prism(0.0, floor_t, H+1, R-wall)
shell = base_solid.cut(cavity)

# colonne viti coperchio: piu' grosse e affondate nelle pareti (post_emb)
aa = R - wall; off = (aa - post_r + post_emb)*0.70710678
px_list = [wall + aa - off, ox - wall - aa + off]
py_list = [yf_in(H) + aa/ca - off/ca, oy - wall - aa + off]
adds = [Part.makeCylinder(post_r, H-floor_t+0.5, V(x, y, floor_t-0.5)) for x in px_list for y in py_list]
# colonne anteriori: cuneo di raccordo fino alla parete inclinata (la parete frontale e' inclinata, il cilindro da solo la tocca solo in cima)
for x in px_list:
    wdg = prism_x([(yf_in(floor_t)-0.3, floor_t), (py_list[0], floor_t), (py_list[0], H-2.8), (yf_in(H-2.8)-0.3, H-2.8)], x-post_r, x+post_r)
    adds.append(wdg.common(base_solid))

# ESP32 fissata a vite sui suoi 4 fori (47,4 x 23,8 mm, viti M2,5 autofilettanti): 4 colonnine con foro pilota,
# le colonnine a sinistra e dietro sono collegate con una costola alla parete
cxb = esp_x + clr + esp_l/2; cyb = esp_y + clr + esp_w/2
z_post = floor_t + esp_h                                  # faccia superiore delle colonnine = fondo del PCB
cuts = []
for sx in (-1, 1):
    for sy in (-1, 1):
        hx = cxb + sx*esp_hole_x/2; hy = cyb + sy*esp_hole_y/2
        z0p = floor_t - 0.5; hp_ = z_post - z0p
        adds.append(Part.makeCone(esp_post_rb, esp_post_r, hp_, V(hx, hy, z0p)))   # cono troncato: base larga, punta d6
        cuts.append(Part.makeCylinder(esp_pilot_d/2, z_post-0.8, V(hx, hy, 0.8)))
        if sx < 0:   # costola verso la parete sinistra
            adds.append(bx(hx-(wall-0.3), 3.0, hp_, wall-0.3, hy-1.5, z0p).common(base_solid))
        if sy > 0:   # costola verso la parete posteriore
            adds.append(bx(3.0, (oy-wall+0.3)-hy, hp_, hx-1.5, hy, z0p).common(base_solid))

# ================= PANNELLO FRONTALE (coordinate locali, poi inclinato) =================
wz = mod_z0 + pcb_h/2 + disp_dz
wx = mod_x + disp_cx + win_dx
slot_d = mod_tot + 0.3
fa = []; fc = []
bw = win_w + 2*bezel_b; bh = win_h + 2*bezel_b
fa.append(rbox_y(wx-bw/2, wz-bh/2, bw, bh, -bezel_h, 0.3, bezel_r))
fa.append(Part.makeCylinder(led_ring_d/2, bezel_h+0.3, V(led_x, -bezel_h, wz), V(0,1,0)))
col = Part.makeCylinder(4.5, 5.5, V(led_x, wall-0.5, wz), V(0,1,0))
fa.append(col.cut(Part.makeCylinder(led_flange_d/2, 6, V(led_x, wall, wz), V(0,1,0))))
rl = pcb_h + 1.0
for s_ in (0, 1):
    rx = mod_x-clr-lw if s_ == 0 else mod_x+pcb_w+clr
    lx = mod_x-clr if s_ == 0 else mod_x+pcb_w+clr-lip
    piece = bx(lw, slot_d+1.7, rl, rx, wall-0.5, mod_z0).fuse(bx(lip, 1.2, rl, lx, wall+slot_d, mod_z0))
    if s_ == 1:   # tacca per i fili sul lato destro
        piece = piece.cut(bx(lw+lip+0.4, 6.0, 12.0, mod_x+pcb_w+clr-lip-0.2, wall+mod_tot-2.5, mod_z0+pcb_h/2-6.0))
    fa.append(piece)
fc.append(rbox_y(wx-(win_w+3)/2, wz-(win_h+3)/2, win_w+3, win_h+3, -3, 0.0, 5.5))
fc.append(rbox_y(wx-win_w/2, wz-win_h/2, win_w, win_h, -3, 3, 3.0))
fc.append(Part.makeCylinder(led_d/2, 7, V(led_x, -3, wz), V(0,1,0)))

font = r"C:\Windows\Fonts\arialbd.ttf"
if not os.path.exists(font): font = r"C:\Windows\Fonts\arial.ttf"
def text_cut(txt, size, xc, zl):
    import Draft
    ss = Draft.make_shapestring(String=txt, FontFile=font, Size=size, Tracking=0)
    doc.recompute()
    sh = ss.Shape.copy(); doc.removeObject(ss.Name)
    bb = sh.BoundBox
    sh.translate(V(-(bb.XMin+bb.XMax)/2, -(bb.YMin+bb.YMax)/2, 0))
    sol = sh.extrude(V(0, 0, -engrave))
    sol.rotate(V(0,0,0), V(1,0,0), 90)
    sol.translate(V(xc, 0, zl))
    return sol
try:
    fc.append(text_cut("GPS", 4.5, led_x, wz + led_ring_d/2 + 2 + 2.25))
    fc.append(text_cut("km/h", 4.5, led_x, wz - led_ring_d/2 - 2 - 2.25))
except Exception as e:
    print("Testo non inciso:", e)
adds += [T(s) for s in fa]
cuts += [T(s) for s in fc]

# ================= FORI E GRIGLIE TONDE =================
for x in px_list:
    for y in py_list:
        cuts.append(Part.makeCylinder(pilot_d/2, 13, V(x, y, H-12)))
cuts.append(bx(wall+2, usb_w, usb_h, -1, esp_y+clr+esp_w/2-usb_w/2, floor_t+esp_h+1.6-1.5))
def vents(plane, a0, a1, z0, z1):
    out = []; row = 0; z = z0 + vent_d/2; pv = vent_pitch*0.866
    while z <= z1 - vent_d/2 + 1e-6:
        u = a0 + vent_d/2 + (vent_pitch/2 if row % 2 else 0)
        while u <= a1 - vent_d/2 + 1e-6:
            if plane == "x": out.append(Part.makeCylinder(vent_d/2, wall+2, V(ox-wall-1, u, z), V(1,0,0)))
            else:            out.append(Part.makeCylinder(vent_d/2, wall+2, V(u, oy-wall-1, z), V(0,1,0)))
            u += vent_pitch
        z += pv; row += 1
    return out
cuts += vents("x", 26, 50, 9, H-4)
cuts += vents("y", 16, 70, 9, H-4)

base = shell.multiFuse(adds)
base = base.cut(fuse(cuts))
try: base = base.removeSplitter()
except Exception: pass

# ================= COPERCHIO (con culla rinforzata per scheda GPS + antenna) =================
def ring_slab(ins, z0, z1, r):
    c = cav_prism(ins, z0-3.0, z1+3.0, r)
    return c.common(Part.makeBox(ox, oy, z1-z0, V(0, 0, z0)))
ring_o = ring_slab(0.2, H-1.6, H, R-wall-0.2)
ring_i = ring_slab(1.4, H-2.6, H+1, R-wall-1.4)
clears = [Part.makeCylinder(post_r+0.4, 4, V(x, y, H-2.6)) for x in px_list for y in py_list]
gw = pcbg_w + 2*clr
pl = pcbg_l + 2*clr; al = ant_l + 2*clr
x_p = gps_x; x_a = gps_x + pl + 0.6
Ltot = x_a + al - gps_x
zb_p = H - gps_gap - pcbg_t; zb_a = H - gps_gap - ant_t
zlow = min(zb_p, zb_a) - lip_t
Ztop = H + 0.4
gap = bx(6, gw+3, 4, ox-wall-3.5, gps_y-1.5, H-2.6)
ring = ring_o.cut(fuse([ring_i, gap] + clears))
lid = lid_outer.fuse(ring)
def rail_prism(front):
    if front: pts = [(gps_y, zlow), (gps_y, Ztop), (gps_y-rail_t-rail_fl, Ztop), (gps_y-rail_t, Ztop-rail_fl), (gps_y-rail_t, zlow)]
    else:     pts = [(gps_y+gw, zlow), (gps_y+gw, Ztop), (gps_y+gw+rail_t+rail_fl, Ztop), (gps_y+gw+rail_t, Ztop-rail_fl), (gps_y+gw+rail_t, zlow)]
    return prism_x(pts, gps_x-rail_t, gps_x+Ltot)
rails = [rail_prism(True), rail_prism(False),
         bx(rail_t, 8, Ztop-zlow, gps_x-rail_t, gps_y, zlow),
         bx(rail_t, 8, Ztop-zlow, gps_x-rail_t, gps_y+gw-8, zlow)]
for (xx, ll, zb) in ((x_p, pl, zb_p), (x_a, al, zb_a)):
    rails.append(bx(ll, lip_gps, lip_t, xx, gps_y, zb-lip_t))
    rails.append(bx(ll, lip_gps, lip_t, xx, gps_y+gw-lip_gps, zb-lip_t))
rail_clr = [Part.makeCylinder(post_r+0.4, H+1-zlow+1, V(x, y, zlow-1)) for x in px_list for y in py_list]
lid = lid.fuse(fuse(rails).cut(fuse(rail_clr)))
lt = []
for x in px_list:
    for y in py_list:
        lt.append(Part.makeCylinder(screw_d/2, lid_t+4, V(x, y, H-2)))
        lt.append(Part.makeCone(screw_d/2, 3.0, 1.5, V(x, y, zt-1.5)))
gcx = x_a + al/2; gcy = gps_y + gw/2
engrave_lid = 1.0                       # profondita' solchi sul coperchio (10/11/2026: prima 0,6 e troppo sottili)
for r1, r2 in ((3, 5), (7.5, 9.5), (12, 14)):   # solchi larghi 2 mm (5 linee da 0,4)
    ro = Part.makeCylinder(r2, engrave_lid+1, V(gcx, gcy, zt-engrave_lid))
    ri = Part.makeCylinder(r1, engrave_lid+1, V(gcx, gcy, zt-engrave_lid))
    lt.append(ro.cut(ri))
lt.append(bx(28, 1.6, engrave_lid+1, gcx-14, gcy-0.8, zt-engrave_lid))
lt.append(bx(1.6, 28, engrave_lid+1, gcx-0.8, gcy-14, zt-engrave_lid))
lid = lid.cut(fuse(lt))
try: lid = lid.removeSplitter()
except Exception: pass
lp = lid.copy(); lp.rotate(V(0,0,0), V(1,0,0), 180)
bb = lp.BoundBox; lp.translate(V(0, -bb.YMin, -bb.ZMin))

# ================= OGGETTI =================
ob = doc.addObject("Part::Feature", "Base"); ob.Shape = base
ol = doc.addObject("Part::Feature", "Coperchio"); ol.Shape = lid
op = doc.addObject("Part::Feature", "Coperchio_stampa"); op.Shape = lp
doc.recompute()
try:
    op.ViewObject.Visibility = False
except Exception: pass
print("Base  valido:", base.isValid(), "solidi:", len(base.Solids), "vol:", round(base.Volume), base.BoundBox)
print("Lid   valido:", lid.isValid(), "solidi:", len(lid.Solids), "vol:", round(lid.Volume), lid.BoundBox)
