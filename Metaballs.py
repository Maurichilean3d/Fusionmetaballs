# Fusion 360 Metaballs Add-in
# Description: Generates metaball-like isosurfaces via marching cubes.
# Version: 0.4.0

import adsk.core
import adsk.fusion
import adsk.cam
import math
import os
import traceback

APP_NAME = 'Metaballs'
ADDIN_VERSION = '0.4.0'
CMD_ID = 'metaballs_command'
CMD_NAME = 'Metaballs'
CMD_DESC = 'Generate metaball-style isosurfaces with parametric controls.'

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
BUTTON_ID = 'MetaballsButton'

# Input IDs
INPUT_COUNT = 'metaball_count'
INPUT_RADIUS = 'metaball_radius'
INPUT_SPACING = 'metaball_spacing'
INPUT_LAYOUT = 'metaball_layout'
INPUT_THRESHOLD = 'metaball_threshold'
INPUT_GRID = 'metaball_grid'
INPUT_KERNEL = 'metaball_kernel'
INPUT_MARGIN = 'metaball_margin'
INPUT_PARAMETRIC = 'metaball_parametric'
INPUT_PREVIEW = 'metaball_preview'
INPUT_CLEAR = 'metaball_clear_previous'
INPUT_HELP = 'metaball_help'
INPUT_HELP_BUTTON = 'metaball_help_button'

_handlers = []

EDGE_TABLE = [
    0x0, 0x109, 0x203, 0x30a, 0x406, 0x50f, 0x605, 0x70c,
    0x80c, 0x905, 0xa0f, 0xb06, 0xc0a, 0xd03, 0xe09, 0xf00,
    0x190, 0x99, 0x393, 0x29a, 0x596, 0x49f, 0x795, 0x69c,
    0x99c, 0x895, 0xb9f, 0xa96, 0xd9a, 0xc93, 0xf99, 0xe90,
    0x230, 0x339, 0x33, 0x13a, 0x636, 0x73f, 0x435, 0x53c,
    0xa3c, 0xb35, 0x83f, 0x936, 0xe3a, 0xf33, 0xc39, 0xd30,
    0x3a0, 0x2a9, 0x1a3, 0xaa, 0x7a6, 0x6af, 0x5a5, 0x4ac,
    0xbac, 0xaa5, 0x9af, 0x8a6, 0xfaa, 0xea3, 0xda9, 0xca0,
    0x460, 0x569, 0x663, 0x76a, 0x66, 0x16f, 0x265, 0x36c,
    0xc6c, 0xd65, 0xe6f, 0xf66, 0x86a, 0x963, 0xa69, 0xb60,
    0x5f0, 0x4f9, 0x7f3, 0x6fa, 0x1f6, 0xff, 0x3f5, 0x2fc,
    0xdfc, 0xcf5, 0xfff, 0xef6, 0x9fa, 0x8f3, 0xbf9, 0xaf0,
    0x650, 0x759, 0x453, 0x55a, 0x256, 0x35f, 0x55, 0x15c,
    0xe5c, 0xf55, 0xc5f, 0xd56, 0xa5a, 0xb53, 0x859, 0x950,
    0x7c0, 0x6c9, 0x5c3, 0x4ca, 0x3c6, 0x2cf, 0x1c5, 0xcc,
    0xfcc, 0xec5, 0xdcf, 0xcc6, 0xbca, 0xac3, 0x9c9, 0x8c0,
    0x8c0, 0x9c9, 0xac3, 0xbca, 0xcc6, 0xdcf, 0xec5, 0xfcc,
    0xcc, 0x1c5, 0x2cf, 0x3c6, 0x4ca, 0x5c3, 0x6c9, 0x7c0,
    0x950, 0x859, 0xb53, 0xa5a, 0xd56, 0xc5f, 0xf55, 0xe5c,
    0x15c, 0x55, 0x35f, 0x256, 0x55a, 0x453, 0x759, 0x650,
    0xaf0, 0xbf9, 0x8f3, 0x9fa, 0xef6, 0xfff, 0xcf5, 0xdfc,
    0x2fc, 0x3f5, 0xff, 0x1f6, 0x6fa, 0x7f3, 0x4f9, 0x5f0,
    0xb60, 0xa69, 0x963, 0x86a, 0xf66, 0xe6f, 0xd65, 0xc6c,
    0x36c, 0x265, 0x16f, 0x66, 0x76a, 0x663, 0x569, 0x460,
    0xca0, 0xda9, 0xea3, 0xfaa, 0x8a6, 0x9af, 0xaa5, 0xbac,
    0x4ac, 0x5a5, 0x6af, 0x7a6, 0xaa, 0x1a3, 0x2a9, 0x3a0,
    0xd30, 0xc39, 0xf33, 0xe3a, 0x936, 0x83f, 0xb35, 0xa3c,
    0x53c, 0x435, 0x73f, 0x636, 0x13a, 0x33, 0x339, 0x230,
    0xe90, 0xf99, 0xc93, 0xd9a, 0xa96, 0xb9f, 0x895, 0x99c,
    0x69c, 0x795, 0x49f, 0x596, 0x29a, 0x393, 0x99, 0x190,
    0xf00, 0xe09, 0xd03, 0xc0a, 0xb06, 0xa0f, 0x905, 0x80c,
    0x70c, 0x605, 0x50f, 0x406, 0x30a, 0x203, 0x109, 0x0,
]

TRI_TABLE = [
    [], [0, 8, 3], [0, 1, 9], [1, 8, 3, 9, 8, 1], [1, 2, 10], [0, 8, 3, 1, 2, 10],
    [9, 2, 10, 0, 2, 9], [2, 8, 3, 2, 10, 8, 10, 9, 8], [3, 11, 2], [0, 11, 2, 8, 11, 0],
    [1, 9, 0, 2, 3, 11], [1, 11, 2, 1, 9, 11, 9, 8, 11], [3, 10, 1, 11, 10, 3],
    [0, 10, 1, 0, 8, 10, 8, 11, 10], [3, 9, 0, 3, 11, 9, 11, 10, 9], [9, 8, 10, 10, 8, 11],
    [4, 7, 8], [4, 3, 0, 7, 3, 4], [0, 1, 9, 8, 4, 7], [4, 1, 9, 4, 7, 1, 7, 3, 1],
    [1, 2, 10, 8, 4, 7], [3, 4, 7, 3, 0, 4, 1, 2, 10], [9, 2, 10, 9, 0, 2, 8, 4, 7],
    [2, 10, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4], [8, 4, 7, 3, 11, 2],
    [11, 4, 7, 11, 2, 4, 2, 0, 4], [9, 0, 1, 8, 4, 7, 2, 3, 11],
    [4, 7, 11, 9, 4, 11, 9, 11, 2, 9, 2, 1], [3, 10, 1, 3, 11, 10, 7, 8, 4],
    [1, 11, 10, 1, 4, 11, 1, 0, 4, 7, 11, 4], [4, 7, 8, 9, 0, 11, 9, 11, 10, 11, 0, 3],
    [4, 7, 11, 4, 11, 9, 9, 11, 10], [9, 5, 4], [9, 5, 4, 0, 8, 3], [0, 5, 4, 1, 5, 0],
    [8, 5, 4, 8, 3, 5, 3, 1, 5], [1, 2, 10, 9, 5, 4], [3, 0, 8, 1, 2, 10, 4, 9, 5],
    [5, 2, 10, 5, 4, 2, 4, 0, 2], [2, 10, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8],
    [9, 5, 4, 2, 3, 11], [0, 11, 2, 0, 8, 11, 4, 9, 5], [0, 5, 4, 0, 1, 5, 2, 3, 11],
    [2, 1, 5, 2, 5, 8, 2, 8, 11, 4, 8, 5], [10, 3, 11, 10, 1, 3, 9, 5, 4],
    [4, 9, 5, 0, 8, 1, 8, 10, 1, 8, 11, 10], [5, 4, 0, 5, 0, 11, 5, 11, 10, 11, 0, 3],
    [5, 4, 8, 5, 8, 10, 10, 8, 11], [9, 7, 8, 5, 7, 9], [9, 3, 0, 9, 5, 3, 5, 7, 3],
    [0, 7, 8, 0, 1, 7, 1, 5, 7], [1, 5, 3, 3, 5, 7], [9, 7, 8, 9, 5, 7, 10, 1, 2],
    [10, 1, 2, 9, 5, 0, 5, 3, 0, 5, 7, 3], [8, 0, 2, 8, 2, 5, 8, 5, 7, 10, 5, 2],
    [2, 10, 5, 2, 5, 3, 3, 5, 7], [7, 9, 5, 7, 8, 9, 3, 11, 2],
    [9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 11], [2, 3, 11, 0, 1, 8, 1, 7, 8, 1, 5, 7],
    [11, 2, 1, 11, 1, 7, 7, 1, 5], [9, 5, 8, 8, 5, 7, 10, 1, 3, 10, 3, 11],
    [5, 7, 0, 5, 0, 9, 7, 11, 0, 1, 0, 10, 11, 10, 0], [11, 10, 0, 11, 0, 3, 10, 5, 0, 8, 0, 7, 5, 7, 0],
    [11, 10, 5, 7, 11, 5], [10, 6, 5], [0, 8, 3, 5, 10, 6], [9, 0, 1, 5, 10, 6],
    [1, 8, 3, 1, 9, 8, 5, 10, 6], [1, 6, 5, 2, 6, 1], [1, 6, 5, 1, 2, 6, 3, 0, 8],
    [9, 6, 5, 9, 0, 6, 0, 2, 6], [5, 9, 8, 5, 8, 2, 5, 2, 6, 3, 2, 8], [2, 3, 11, 10, 6, 5],
    [11, 0, 8, 11, 2, 0, 10, 6, 5], [0, 1, 9, 2, 3, 11, 5, 10, 6],
    [5, 10, 6, 1, 9, 2, 9, 11, 2, 9, 8, 11], [6, 3, 11, 6, 5, 3, 5, 1, 3],
    [0, 8, 11, 0, 11, 5, 0, 5, 1, 5, 11, 6], [3, 11, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9],
    [6, 5, 9, 6, 9, 11, 11, 9, 8], [5, 10, 6, 4, 7, 8], [4, 3, 0, 4, 7, 3, 6, 5, 10],
    [1, 9, 0, 5, 10, 6, 8, 4, 7], [10, 6, 5, 1, 9, 7, 1, 7, 3, 7, 9, 4],
    [6, 1, 2, 6, 5, 1, 4, 7, 8], [1, 2, 5, 5, 2, 6, 3, 0, 4, 3, 4, 7],
    [8, 4, 7, 9, 0, 5, 0, 6, 5, 0, 2, 6], [7, 3, 9, 7, 9, 4, 3, 2, 9, 5, 9, 6, 2, 6, 9],
    [3, 11, 2, 7, 8, 4, 10, 6, 5], [5, 10, 6, 4, 7, 2, 4, 2, 0, 2, 7, 11],
    [0, 1, 9, 4, 7, 8, 2, 3, 11, 5, 10, 6],
    [9, 2, 1, 9, 11, 2, 9, 4, 11, 7, 11, 4, 5, 10, 6],
    [8, 4, 7, 3, 11, 5, 3, 5, 1, 5, 11, 6], [5, 1, 11, 5, 11, 6, 1, 0, 11, 7, 11, 4, 0, 4, 11],
    [0, 5, 9, 0, 6, 5, 0, 3, 6, 11, 6, 3, 8, 4, 7],
    [6, 5, 9, 6, 9, 11, 4, 7, 9, 7, 11, 9],
]

EDGE_INDEXES = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]

while len(TRI_TABLE) < 256:
    TRI_TABLE.append([])


def _ui_message(title, message):
    app = adsk.core.Application.get()
    if not app:
        return
    ui = app.userInterface
    if ui:
        ui.messageBox(message, title)


def _help_text():
    return (
        'Metaballs en Fusion 360\n\n'
        '1) Elige cantidad, radio y separación.\n'
        '2) Selecciona un arreglo (Línea o Círculo).\n'
        '3) Ajusta umbral, resolución y kernel.\n'
        '4) Ejecuta para generar la malla metaball.\n\n'
        'Consejo: umbral 1.0 y grid 28 suelen ir bien.'
    )


def _help_popup_text():
    return (
        'Guía detallada\n\n'
        '• El comando genera una isosuperficie metaball con marching cubes.\n'
        '• Aumenta la resolución para más detalle (más lento).\n'
        '• El umbral y el kernel controlan la unión entre blobs.\n'
        '• Usa "Limpiar preview" para reemplazar resultados anteriores.'
    )


def _ensure_parameters(design, params):
    user_params = design.userParameters

    def add_or_update(name, value, units, comment):
        existing = user_params.itemByName(name)
        if existing:
            existing.value = value
            existing.comment = comment
        else:
            user_params.add(name, adsk.core.ValueInput.createByReal(value), units, comment)

    add_or_update('metaball_count', params['count'], '', 'Cantidad de metaballs')
    add_or_update('metaball_radius', params['radius'], 'cm', 'Radio base de cada metaball')
    add_or_update('metaball_spacing', params['spacing'], 'cm', 'Separación entre metaballs')
    add_or_update('metaball_threshold', params['threshold'], '', 'Umbral de isosuperficie')
    add_or_update('metaball_grid', params['grid'], '', 'Resolución del grid')
    add_or_update('metaball_margin', params['margin'], 'cm', 'Margen del bounding box')


class MetaballsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            inputs.addIntegerSpinnerCommandInput(INPUT_COUNT, 'Cantidad de metaballs', 1, 50, 1, 6)
            inputs.addValueInput(INPUT_RADIUS, 'Radio base', 'cm', adsk.core.ValueInput.createByString('2 cm'))
            inputs.addValueInput(INPUT_SPACING, 'Separación', 'cm', adsk.core.ValueInput.createByString('1.2 cm'))

            layout_input = inputs.addDropDownCommandInput(
                INPUT_LAYOUT,
                'Arreglo',
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            layout_input.listItems.add('Línea', True, '')
            layout_input.listItems.add('Círculo', False, '')

            inputs.addValueInput(INPUT_THRESHOLD, 'Umbral (iso)', '', adsk.core.ValueInput.createByReal(1.0))
            inputs.addIntegerSpinnerCommandInput(INPUT_GRID, 'Resolución (grid)', 8, 80, 2, 28)
            kernel_input = inputs.addDropDownCommandInput(
                INPUT_KERNEL,
                'Kernel',
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            kernel_input.listItems.add('Inverse Square', True, '')
            kernel_input.listItems.add('Poly6', False, '')
            inputs.addValueInput(INPUT_MARGIN, 'Margen', 'cm', adsk.core.ValueInput.createByString('2 cm'))
            inputs.addBoolValueInput(INPUT_PREVIEW, 'Crear preview de metaballs', True, '', True)
            inputs.addBoolValueInput(INPUT_CLEAR, 'Limpiar preview anterior', True, '', True)
            inputs.addBoolValueInput(INPUT_PARAMETRIC, 'Guardar como parámetros', True, '', True)
            inputs.addTextBoxCommandInput(INPUT_HELP, 'Guía rápida', _help_text(), 10, True)
            inputs.addBoolValueInput(INPUT_HELP_BUTTON, 'Mostrar ayuda emergente', False, '', False)

            on_execute = MetaballsCommandExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

            on_input_changed = MetaballsCommandInputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            _handlers.append(on_input_changed)

        except Exception:
            _ui_message(APP_NAME, 'Error al crear el comando:\n{}'.format(traceback.format_exc()))


class MetaballsCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            input_changed = args.input
            if input_changed.id == INPUT_HELP_BUTTON:
                _ui_message(APP_NAME, _help_popup_text())
                input_changed.value = False
        except Exception:
            _ui_message(APP_NAME, 'Error en la ayuda:\n{}'.format(traceback.format_exc()))


class MetaballsCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('No hay un diseño activo.', APP_NAME)
                return

            inputs = args.command.commandInputs
            count_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(INPUT_COUNT))
            radius_input = adsk.core.ValueCommandInput.cast(inputs.itemById(INPUT_RADIUS))
            spacing_input = adsk.core.ValueCommandInput.cast(inputs.itemById(INPUT_SPACING))
            layout_input = adsk.core.DropDownCommandInput.cast(inputs.itemById(INPUT_LAYOUT))
            threshold_input = adsk.core.ValueCommandInput.cast(inputs.itemById(INPUT_THRESHOLD))
            grid_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(INPUT_GRID))
            kernel_input = adsk.core.DropDownCommandInput.cast(inputs.itemById(INPUT_KERNEL))
            margin_input = adsk.core.ValueCommandInput.cast(inputs.itemById(INPUT_MARGIN))
            preview_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_PREVIEW))
            clear_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_CLEAR))
            parametric_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_PARAMETRIC))

            params = {
                'count': count_input.value,
                'radius': radius_input.value,
                'spacing': spacing_input.value,
                'layout': layout_input.selectedItem.name,
                'threshold': threshold_input.value,
                'grid': grid_input.value,
                'kernel': kernel_input.selectedItem.name,
                'margin': margin_input.value,
                'preview': preview_input.value,
                'clear': clear_input.value,
                'parametric': parametric_input.value,
            }

            if params['parametric']:
                _ensure_parameters(design, params)

            _create_metaballs(design, params)

            ui.messageBox(
                'Metaballs completadas.\n\n'
                'Parámetros usados:\n'
                f"- Cantidad: {params['count']}\n"
                f"- Radio: {params['radius']:.2f} cm\n"
                f"- Separación: {params['spacing']:.2f} cm\n"
                f"- Arreglo: {params['layout']}\n"
                f"- Umbral: {params['threshold']:.2f}\n"
                f"- Resolución: {params['grid']}\n"
                f"- Kernel: {params['kernel']}\n"
                f"- Margen: {params['margin']:.2f} cm\n"
                f"- Preview: {'Sí' if params['preview'] else 'No'}",
                APP_NAME,
            )
        except Exception:
            _ui_message(APP_NAME, 'Error al ejecutar el comando:\n{}'.format(traceback.format_exc()))


def _find_existing_preview(root):
    for occ in root.occurrences:
        if occ.component and occ.component.name == 'Metaballs Preview':
            return occ
    return None


def _clear_preview(root):
    existing = _find_existing_preview(root)
    if existing:
        existing.deleteMe()


def _create_preview_component(root):
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occurrence.component.name = 'Metaballs Preview'
    return occurrence.component


def _layout_positions(count, radius, spacing, layout):
    points = []
    if layout == 'Círculo' and count > 1:
        radius_circle = (radius + spacing) * count / (2 * math.pi)
        for index in range(count):
            angle = (2 * math.pi / count) * index
            x = radius_circle * math.cos(angle)
            y = radius_circle * math.sin(angle)
            points.append((x, y, 0))
    else:
        for index in range(count):
            x = index * (radius + spacing)
            points.append((x, 0, 0))
    return points


def _bounds_from_centers(centers, radius, margin):
    if not centers:
        return (-radius, -radius, -radius, radius, radius, radius)
    xs = [c[0] for c in centers]
    ys = [c[1] for c in centers]
    zs = [c[2] for c in centers]
    min_x = min(xs) - radius - margin
    max_x = max(xs) + radius + margin
    min_y = min(ys) - radius - margin
    max_y = max(ys) + radius + margin
    min_z = min(zs) - radius - margin
    max_z = max(zs) + radius + margin
    return (min_x, min_y, min_z, max_x, max_y, max_z)


def _field_value(x, y, z, metaballs, kernel):
    value = 0.0
    for center, radius in metaballs:
        dx = x - center[0]
        dy = y - center[1]
        dz = z - center[2]
        dist_sq = dx * dx + dy * dy + dz * dz
        if dist_sq > 0.000001:
            if kernel == 'Poly6':
                dist = math.sqrt(dist_sq)
                if dist < radius:
                    t = 1.0 - (dist / radius)
                    value += t * t * t
            else:
                value += (radius * radius) / dist_sq
    return value


def _interpolate(p1, p2, v1, v2, iso):
    if abs(iso - v1) < 1e-6:
        return p1
    if abs(iso - v2) < 1e-6:
        return p2
    if abs(v1 - v2) < 1e-6:
        return p1
    t = (iso - v1) / (v2 - v1)
    return (
        p1[0] + t * (p2[0] - p1[0]),
        p1[1] + t * (p2[1] - p1[1]),
        p1[2] + t * (p2[2] - p1[2]),
    )


def _marching_cubes(metaballs, bounds, grid, iso, kernel):
    xmin, ymin, zmin, xmax, ymax, zmax = bounds
    step_x = (xmax - xmin) / grid
    step_y = (ymax - ymin) / grid
    step_z = (zmax - zmin) / grid

    vertices = []
    triangles = []

    for i in range(grid):
        for j in range(grid):
            for k in range(grid):
                cube = []
                values = []
                for dx, dy, dz in [
                    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
                ]:
                    x = xmin + (i + dx) * step_x
                    y = ymin + (j + dy) * step_y
                    z = zmin + (k + dz) * step_z
                    cube.append((x, y, z))
                    values.append(_field_value(x, y, z, metaballs, kernel))

                cube_index = 0
                for idx, val in enumerate(values):
                    if val > iso:
                        cube_index |= 1 << idx

                edges = EDGE_TABLE[cube_index]
                if edges == 0:
                    continue

                vert_list = [None] * 12
                for edge in range(12):
                    if edges & (1 << edge):
                        a, b = EDGE_INDEXES[edge]
                        vert_list[edge] = _interpolate(cube[a], cube[b], values[a], values[b], iso)

                tri_edges = TRI_TABLE[cube_index]
                for t in range(0, len(tri_edges), 3):
                    idx_a = tri_edges[t]
                    idx_b = tri_edges[t + 1]
                    idx_c = tri_edges[t + 2]
                    va = vert_list[idx_a]
                    vb = vert_list[idx_b]
                    vc = vert_list[idx_c]
                    if va and vb and vc:
                        base = len(vertices)
                        vertices.extend([va, vb, vc])
                        triangles.append((base, base + 1, base + 2))

    return vertices, triangles


def _create_mesh(component, vertices, triangles):
    points = adsk.core.ObjectCollection.create()
    for vx, vy, vz in vertices:
        points.add(adsk.core.Point3D.create(vx, vy, vz))

    index_array_cls = getattr(adsk.core, 'UInt32Array', None) or getattr(adsk.core, 'Int32Array', None)
    if not index_array_cls:
        raise RuntimeError('No se encontró UInt32Array/Int32Array en adsk.core.')
    tri_indices = index_array_cls.create([idx for tri in triangles for idx in tri])
    mesh = adsk.fusion.TriangleMesh.create(points, tri_indices)
    component.meshBodies.add(mesh)


def _create_metaballs(design, params):
    root = design.rootComponent
    if params['clear']:
        _clear_preview(root)

    if not params['preview']:
        return

    component = _create_preview_component(root)
    centers = _layout_positions(params['count'], params['radius'], params['spacing'], params['layout'])
    metaballs = [(center, params['radius']) for center in centers]

    bounds = _bounds_from_centers(centers, params['radius'], params['margin'])
    vertices, triangles = _marching_cubes(
        metaballs,
        bounds,
        params['grid'],
        params['threshold'],
        params['kernel'],
    )
    if not vertices:
        raise RuntimeError('No se generó malla, ajusta el umbral o resolución.')

    _create_mesh(component, vertices, triangles)


class MetaballsAddIn:
    def __init__(self):
        self.ui = None

    def run(self, context):
        app = adsk.core.Application.get()
        self.ui = app.userInterface
        resource_dir = os.path.join(os.path.dirname(__file__), 'resources')
        os.makedirs(resource_dir, exist_ok=True)

        cmd_def = self.ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = self.ui.commandDefinitions.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                CMD_DESC,
                resource_dir,
            )

        on_created = MetaballsCommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)

        workspace = self.ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        button = panel.controls.itemById(BUTTON_ID)
        if not button:
            button = panel.controls.addCommand(cmd_def)
            button.id = BUTTON_ID
            button.isPromoted = True

    def stop(self, context):
        app = adsk.core.Application.get()
        self.ui = app.userInterface

        panel = self.ui.workspaces.itemById(WORKSPACE_ID).toolbarPanels.itemById(PANEL_ID)
        control = panel.controls.itemById(BUTTON_ID)
        if control:
            control.deleteMe()

        cmd_def = self.ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()


add_in = MetaballsAddIn()


def run(context):
    add_in.run(context)


def stop(context):
    add_in.stop(context)
