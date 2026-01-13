# Metaballs.py
# Fusion 360 Add-in: Metaballs reales (isosuperficie) -> MeshBody (STL import).
#
# ✅ “Modo Blender” (IMPORTANTE):
# - Puedes ejecutar “Metaballs” varias veces y NO crea objetos separados.
# - Si activas “Añadir al existente”, el nuevo set de bolas se SUMA a las anteriores
#   y se regenera UNA sola malla que “se derrite / conecta” (puente líquido).
# - Soporta “Familia” (A/B/C...) para tener blobs separados (como Blender).
# - Botones: Convertir a BRep / Convertir a Quad Mesh (dispara comandos nativos).
#
# Requiere:
#   from .lib import fusion360utils as futil
#   from . import config
#   config.CMD_ID, config.WORKSPACE_ID, config.PANEL_ID

import adsk.core
import adsk.fusion
import math
import os
import struct
import tempfile
import json

from .lib import fusion360utils as futil
from . import config

_handlers = []

# ---------------------------
# IDs del add-in
# ---------------------------
CMD_ID_MAIN = config.CMD_ID
CMD_ID_CONVERT_BREP = f"{config.CMD_ID}_convert_brep"
CMD_ID_QUAD_MESH = f"{config.CMD_ID}_convert_quad"

# ---------------------------
# Persistencia/identidad
# ---------------------------
ATTR_GROUP = "MetaballsPlugin"
ATTR_KEY_TAG = "tag"
ATTR_VAL_TAG = "metaballs_root"
ATTR_KEY_FAMILY = "family"
ATTR_KEY_BALLS_JSON = "balls_json"

METABALLS_COMP_NAME = "Metaballs Result"
METABALLS_BASEFEATURE_NAME = "Metaballs Base"
METABALLS_MESH_NAME = "Metaballs Mesh"


# =========================================================
#  Metaballs: campo + marching tetrahedra + STL
# =========================================================

def field_value(x, y, z, balls, eps=1e-9):
    """
    Campo metaball (simple y efectivo):
      F(p) = sum( (r_i^2) / (|p-ci|^2 + eps) )
    """
    s = 0.0
    for b in balls:
        dx = x - b["x"]
        dy = y - b["y"]
        dz = z - b["z"]
        d2 = dx*dx + dy*dy + dz*dz + eps
        r2 = b["r"] * b["r"]
        s += r2 / d2
    return s


def lerp_point(p1, v1, p2, v2, iso):
    if abs(v2 - v1) < 1e-12:
        t = 0.5
    else:
        t = (iso - v1) / (v2 - v1)
    return (
        p1[0] + t * (p2[0] - p1[0]),
        p1[1] + t * (p2[1] - p1[1]),
        p1[2] + t * (p2[2] - p1[2]),
    )


def tri_normal(a, b, c):
    ux, uy, uz = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
    vx, vy, vz = (c[0]-a[0], c[1]-a[1], c[2]-a[2])
    nx = uy*vz - uz*vy
    ny = uz*vx - ux*vz
    nz = ux*vy - uy*vx
    ln = math.sqrt(nx*nx + ny*ny + nz*nz)
    if ln > 1e-12:
        nx /= ln
        ny /= ln
        nz /= ln
    return (nx, ny, nz)


# 6 tetra por cubo (marching tetrahedra)
CUBE_TETS = [
    (0, 5, 1, 6),
    (0, 1, 2, 6),
    (0, 2, 3, 6),
    (0, 3, 7, 6),
    (0, 7, 4, 6),
    (0, 4, 5, 6),
]

TET_EDGES = [
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 2),
    (1, 3),
    (2, 3),
]


def polygonise_tetra(p, val, iso):
    inside = [v >= iso for v in val]
    n_inside = sum(1 for b in inside if b)

    if n_inside == 0 or n_inside == 4:
        return []

    inter_pts = []
    for (i, j) in TET_EDGES:
        if inside[i] != inside[j]:
            inter_pts.append(lerp_point(p[i], val[i], p[j], val[j], iso))

    # 1 o 3 dentro -> 1 tri
    if n_inside == 1 or n_inside == 3:
        if len(inter_pts) >= 3:
            return [(inter_pts[0], inter_pts[1], inter_pts[2])]
        return []

    # 2 dentro -> 2 tris (quad)
    if len(inter_pts) >= 4:
        return [
            (inter_pts[0], inter_pts[1], inter_pts[2]),
            (inter_pts[0], inter_pts[2], inter_pts[3]),
        ]
    return []


def write_binary_stl(path, triangles, name=b"metaballs"):
    header = name.ljust(80, b" ")[:80]
    with open(path, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for (a, b, c) in triangles:
            n = tri_normal(a, b, c)
            f.write(struct.pack("<3f", n[0], n[1], n[2]))
            f.write(struct.pack("<3f", a[0], a[1], a[2]))
            f.write(struct.pack("<3f", b[0], b[1], b[2]))
            f.write(struct.pack("<3f", c[0], c[1], c[2]))
            f.write(struct.pack("<H", 0))


def generate_metaball_mesh_from_balls(balls, iso, resolution):
    """
    Genera triángulos para UNA isosuperficie a partir de MUCHAS bolas (modo Blender).
    resolution: más alto -> más smooth, más pesado.
    """
    if not balls:
        return []

    max_r = max(b["r"] for b in balls)
    margin = max_r * 2.5

    xs = [b["x"] for b in balls]
    ys = [b["y"] for b in balls]
    zs = [b["z"] for b in balls]

    minx, maxx = min(xs) - margin, max(xs) + margin
    miny, maxy = min(ys) - margin, max(ys) + margin
    minz, maxz = min(zs) - margin, max(zs) + margin

    sx = maxx - minx
    sy = maxy - miny
    sz = maxz - minz
    maxs = max(sx, sy, sz)

    n = max(10, int(resolution))
    step = maxs / n

    nx = max(2, int(sx / step))
    ny = max(2, int(sy / step))
    nz = max(2, int(sz / step))

    def grid_point(ix, iy, iz):
        return (minx + ix*step, miny + iy*step, minz + iz*step)

    triangles = []
    layer0 = [[0.0]*(ny+1) for _ in range(nx+1)]
    layer1 = [[0.0]*(ny+1) for _ in range(nx+1)]

    z0 = minz
    for ix in range(nx+1):
        x = minx + ix*step
        for iy in range(ny+1):
            y = miny + iy*step
            layer0[ix][iy] = field_value(x, y, z0, balls)

    for iz in range(nz):
        z_next = minz + (iz+1)*step
        for ix in range(nx+1):
            x = minx + ix*step
            for iy in range(ny+1):
                y = miny + iy*step
                layer1[ix][iy] = field_value(x, y, z_next, balls)

        for ix in range(nx):
            for iy in range(ny):
                p = [None]*8
                v = [0.0]*8

                # z = iz
                p[0] = grid_point(ix,   iy,   iz)
                p[1] = grid_point(ix+1, iy,   iz)
                p[2] = grid_point(ix+1, iy+1, iz)
                p[3] = grid_point(ix,   iy+1, iz)

                v[0] = layer0[ix][iy]
                v[1] = layer0[ix+1][iy]
                v[2] = layer0[ix+1][iy+1]
                v[3] = layer0[ix][iy+1]

                # z = iz+1
                p[4] = grid_point(ix,   iy,   iz+1)
                p[5] = grid_point(ix+1, iy,   iz+1)
                p[6] = grid_point(ix+1, iy+1, iz+1)
                p[7] = grid_point(ix,   iy+1, iz+1)

                v[4] = layer1[ix][iy]
                v[5] = layer1[ix+1][iy]
                v[6] = layer1[ix+1][iy+1]
                v[7] = layer1[ix][iy+1]

                for tet in CUBE_TETS:
                    tp = [p[tet[0]], p[tet[1]], p[tet[2]], p[tet[3]]]
                    tv = [v[tet[0]], v[tet[1]], v[tet[2]], v[tet[3]]]
                    triangles.extend(polygonise_tetra(tp, tv, iso))

        layer0, layer1 = layer1, layer0

    return triangles


# =========================================================
#  Fusion helpers: componente + atributos + reemplazo mesh
# =========================================================

def _get_app_ui():
    app = adsk.core.Application.get()
    return app, app.userInterface


def _get_design():
    app, ui = _get_app_ui()
    return adsk.fusion.Design.cast(app.activeProduct)


def _component_has_tag(comp: adsk.fusion.Component) -> bool:
    try:
        a = comp.attributes.itemByName(ATTR_GROUP, ATTR_KEY_TAG)
        return (a is not None) and (a.value == ATTR_VAL_TAG)
    except:
        return False


def _find_metaballs_component(root: adsk.fusion.Component):
    for i in range(root.occurrences.count):
        occ = root.occurrences.item(i)
        if not occ:
            continue
        c = occ.component
        if c and _component_has_tag(c):
            return occ, c
    return None, None


def _ensure_metaballs_component(root: adsk.fusion.Component):
    occ, comp = _find_metaballs_component(root)
    if comp:
        return occ, comp

    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = METABALLS_COMP_NAME
    comp.attributes.add(ATTR_GROUP, ATTR_KEY_TAG, ATTR_VAL_TAG)
    # defaults
    comp.attributes.add(ATTR_GROUP, ATTR_KEY_FAMILY, "A")
    comp.attributes.add(ATTR_GROUP, ATTR_KEY_BALLS_JSON, json.dumps({"A": []}))
    return occ, comp


def _load_family_map(comp):
    """
    Devuelve dict: { "A": [balls...], "B": [balls...], ... }
    """
    a = comp.attributes.itemByName(ATTR_GROUP, ATTR_KEY_BALLS_JSON)
    if not a or not a.value:
        return {"A": []}
    try:
        d = json.loads(a.value)
        if isinstance(d, dict):
            return d
        return {"A": []}
    except:
        return {"A": []}


def _save_family_map(comp, fam_map):
    comp.attributes.add(ATTR_GROUP, ATTR_KEY_BALLS_JSON, json.dumps(fam_map))


def _get_family(comp):
    a = comp.attributes.itemByName(ATTR_GROUP, ATTR_KEY_FAMILY)
    return a.value if a and a.value else "A"


def _set_family(comp, fam):
    comp.attributes.add(ATTR_GROUP, ATTR_KEY_FAMILY, fam)


def _delete_existing_mesh_and_basefeature(comp: adsk.fusion.Component):
    # Borra mesh bodies
    try:
        for i in range(comp.meshBodies.count - 1, -1, -1):
            mb = comp.meshBodies.item(i)
            if mb:
                mb.deleteMe()
    except:
        pass

    # Borra basefeatures anteriores (solo los nuestros)
    try:
        bfs = comp.features.baseFeatures
        for i in range(bfs.count - 1, -1, -1):
            bf = bfs.item(i)
            if bf and bf.name == METABALLS_BASEFEATURE_NAME:
                bf.deleteMe()
    except:
        pass


def _import_mesh(comp: adsk.fusion.Component, stl_path: str):
    base_feat = comp.features.baseFeatures.add()
    base_feat.name = METABALLS_BASEFEATURE_NAME
    base_feat.startEdit()
    comp.meshBodies.add(stl_path, adsk.fusion.MeshUnits.CentimeterMeshUnit, base_feat)
    base_feat.finishEdit()

    try:
        mb = comp.meshBodies.item(comp.meshBodies.count - 1)
        if mb:
            mb.name = METABALLS_MESH_NAME
        return mb
    except:
        return None


def _select_entity(ui: adsk.core.UserInterface, entity):
    try:
        ui.activeSelections.clear()
        ui.activeSelections.add(entity)
    except:
        pass


def _compute_centers(cnt, rad, spc, lay):
    centers = []
    for i in range(cnt):
        if lay == 'Círculo' and cnt > 1:
            angle = (2 * math.pi / cnt) * i
            dist = (rad + spc) * cnt / (2 * math.pi)
            centers.append((dist * math.cos(angle), dist * math.sin(angle), 0.0))
        else:
            centers.append((i * (rad + spc), 0.0, 0.0))
    return centers


def _get_current_mesh_body():
    design = _get_design()
    if not design:
        return None, None, None
    root = design.rootComponent
    occ, comp = _find_metaballs_component(root)
    if not comp:
        return None, None, None

    for i in range(comp.meshBodies.count):
        mb = comp.meshBodies.item(i)
        if mb and mb.name == METABALLS_MESH_NAME:
            return occ, comp, mb

    if comp.meshBodies.count > 0:
        return occ, comp, comp.meshBodies.item(0)

    return occ, comp, None


# =========================================================
#  Lanzar comandos nativos (Convert Mesh / Convert to Quad Mesh)
# =========================================================

def _find_native_command_by_name(ui: adsk.core.UserInterface, candidates):
    cmd_defs = ui.commandDefinitions

    # exact match
    for i in range(cmd_defs.count):
        cd = cmd_defs.item(i)
        if not cd:
            continue
        nm = (cd.name or "").strip().lower()
        for c in candidates:
            if nm == c.lower():
                return cd

    # contains match
    for i in range(cmd_defs.count):
        cd = cmd_defs.item(i)
        if not cd:
            continue
        nm = (cd.name or "").strip().lower()
        for c in candidates:
            if c.lower() in nm:
                return cd

    return None


def _execute_native_command(ui: adsk.core.UserInterface, candidates):
    cd = _find_native_command_by_name(ui, candidates)
    if cd:
        cd.execute()
        return True
    return False


# =========================================================
#  Commands
# =========================================================

class MetaballsCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app, ui = _get_app_ui()
            design = _get_design()
            if not design:
                ui.messageBox("No hay un diseño activo.")
                return

            event_args = adsk.core.CommandEventArgs.cast(args)
            inputs = event_args.command.commandInputs

            cnt = inputs.itemById('count').value
            rad = inputs.itemById('radius').value
            spc = inputs.itemById('spacing').value
            lay = inputs.itemById('layout').selectedItem.name

            res = inputs.itemById('resolution').value
            iso = inputs.itemById('iso').value

            family = (inputs.itemById('family').value or "A").strip()
            if not family:
                family = "A"

            append_mode = inputs.itemById('append').value
            clear_family = inputs.itemById('clear').value

            root = design.rootComponent
            occ, comp = _ensure_metaballs_component(root)

            # persist family
            _set_family(comp, family)

            # Cargar mapa de familias y bolas
            fam_map = _load_family_map(comp)
            if family not in fam_map:
                fam_map[family] = []

            if clear_family:
                fam_map[family] = []

            # bolas nuevas (como “primitives” de Blender)
            new_centers = _compute_centers(cnt, rad, spc, lay)
            new_balls = [{"x": c[0], "y": c[1], "z": c[2], "r": rad} for c in new_centers]

            if append_mode:
                fam_map[family].extend(new_balls)  # ✅ modo Blender: sumar bolas
            else:
                fam_map[family] = new_balls        # reemplazar familia

            _save_family_map(comp, fam_map)

            # Regenerar UNA sola malla = campo sumado de todas las bolas de la familia
            balls = fam_map[family]
            if not balls:
                ui.messageBox(f"La familia '{family}' quedó vacía.")
                _delete_existing_mesh_and_basefeature(comp)
                return

            _delete_existing_mesh_and_basefeature(comp)

            tris = generate_metaball_mesh_from_balls(balls, iso, res)
            if not tris:
                ui.messageBox("No se generó malla.\nPrueba: bajar Iso (0.6–0.9) o subir Resolución (60–100).")
                return

            stl_path = os.path.join(tempfile.gettempdir(), "fusion_metaballs_tmp.stl")
            write_binary_stl(stl_path, tris)

            mb = _import_mesh(comp, stl_path)
            if mb:
                _select_entity(ui, mb)

        except:
            futil.handle_error('command_execute')


class MetaballsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            inputs = cmd.commandInputs

            inputs.addIntegerSpinnerCommandInput('count', 'Cantidad', 1, 120, 1, 8)
            inputs.addValueInput('radius', 'Radio', 'cm', adsk.core.ValueInput.createByReal(2.0))
            inputs.addValueInput('spacing', 'Separación', 'cm', adsk.core.ValueInput.createByReal(1.2))

            drop = inputs.addDropDownCommandInput('layout', 'Arreglo', adsk.core.DropDownStyles.TextListDropDownStyle)
            drop.listItems.add('Línea', True)
            drop.listItems.add('Círculo', False)

            # Control metaball
            inputs.addIntegerSpinnerCommandInput('resolution', 'Resolución', 10, 160, 1, 60)
            inputs.addValueInput('iso', 'Iso', '', adsk.core.ValueInput.createByReal(1.0))

            # Modo Blender
            inputs.addStringValueInput('family', 'Familia', 'A')
            inputs.addBoolValueInput('append', 'Añadir al existente', True, '', True)
            inputs.addBoolValueInput('clear', 'Limpiar familia', True, '', False)

            on_execute = MetaballsCommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

        except:
            futil.handle_error('command_created')


class ConvertToBRepExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app, ui = _get_app_ui()
            occ, comp, mb = _get_current_mesh_body()
            if not mb:
                ui.messageBox("No encontré la malla de Metaballs.\nPrimero ejecuta 'Metaballs'.")
                return

            _select_entity(ui, mb)

            candidates = [
                "Convert Mesh",
                "Convertir malla",
                "Convertir Mesh",
                "Mesh to BRep",
                "Convert",  # fallback
            ]

            ok = _execute_native_command(ui, candidates)
            if not ok:
                ui.messageBox(
                    "No pude encontrar el comando nativo 'Convert Mesh' automáticamente.\n"
                    "Usa: Mesh > Modify > Convert Mesh (con la malla seleccionada)."
                )

        except:
            futil.handle_error('convert_brep')


class ConvertToBRepCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            on_execute = ConvertToBRepExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)
        except:
            futil.handle_error('convert_brep_created')


class ConvertToQuadExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app, ui = _get_app_ui()
            occ, comp, mb = _get_current_mesh_body()
            if not mb:
                ui.messageBox("No encontré la malla de Metaballs.\nPrimero ejecuta 'Metaballs'.")
                return

            _select_entity(ui, mb)

            candidates = [
                "Convert to Quad Mesh",
                "Convertir a malla cuadrangular",
                "Convertir a Quad Mesh",
                "Quad Mesh",
                "Quad",
            ]

            ok = _execute_native_command(ui, candidates)
            if not ok:
                ui.messageBox(
                    "No pude encontrar el comando nativo 'Convert to Quad Mesh' automáticamente.\n"
                    "Usa: Mesh > Modify > Convert to Quad Mesh (con la malla seleccionada)."
                )

        except:
            futil.handle_error('convert_quad')


class ConvertToQuadCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            on_execute = ConvertToQuadExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)
        except:
            futil.handle_error('convert_quad_created')


# =========================================================
#  run/stop: crea 3 botones
# =========================================================

def _add_button(ui, cmd_id, name, desc, created_handler, panel):
    cmd_def = ui.commandDefinitions.itemById(cmd_id)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(cmd_id, name, desc, "")
    cmd_def.commandCreated.add(created_handler)
    _handlers.append(created_handler)

    if not panel.controls.itemById(cmd_id):
        panel.controls.addCommand(cmd_def).isPromoted = True


def run(context):
    try:
        app, ui = _get_app_ui()

        workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(config.PANEL_ID)

        _add_button(
            ui,
            CMD_ID_MAIN,
            "Metaballs",
            "Crea/actualiza metaballs como malla (modo Blender: suma bolas en una familia).",
            MetaballsCommandCreatedHandler(),
            panel
        )

        _add_button(
            ui,
            CMD_ID_CONVERT_BREP,
            "Convertir a BRep",
            "Convierte la malla de Metaballs a BRep usando el comando nativo.",
            ConvertToBRepCreatedHandler(),
            panel
        )

        _add_button(
            ui,
            CMD_ID_QUAD_MESH,
            "Convertir a Quad Mesh",
            "Convierte la malla de Metaballs a Quad Mesh usando el comando nativo.",
            ConvertToQuadCreatedHandler(),
            panel
        )

    except:
        futil.handle_error('run')


def stop(context):
    try:
        app, ui = _get_app_ui()
        workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(config.PANEL_ID)

        for cid in [CMD_ID_MAIN, CMD_ID_CONVERT_BREP, CMD_ID_QUAD_MESH]:
            ctrl = panel.controls.itemById(cid)
            if ctrl:
                ctrl.deleteMe()

            cmd_def = ui.commandDefinitions.itemById(cid)
            if cmd_def:
                cmd_def.deleteMe()

        _handlers.clear()
    except:
        pass
