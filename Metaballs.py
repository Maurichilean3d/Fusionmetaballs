# Fusion 360 Metaballs Add-in
# Description: Provides a UI command to generate metaball-like forms with parametric options.
# NOTE: This is a starter template focused on UI structure and parameter plumbing.

import adsk.core
import adsk.fusion
import adsk.cam
import os
import traceback

APP_NAME = 'Metaballs'
CMD_ID = 'metaballs_command'
CMD_NAME = 'Metaballs'
CMD_DESC = 'Create metaball-like forms with parametric control.'
CMD_TOOLTIP = 'Create metaball-style shapes and optionally make them parametric.'

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
BUTTON_ID = 'MetaballsButton'

# Input IDs
INPUT_COUNT = 'metaball_count'
INPUT_RADIUS = 'metaball_radius'
INPUT_THRESHOLD = 'metaball_threshold'
INPUT_RESOLUTION = 'metaball_resolution'
INPUT_PARAMETRIC = 'metaball_parametric'
INPUT_HELP = 'metaball_help'
INPUT_SPACING = 'metaball_spacing'
INPUT_PREVIEW = 'metaball_preview'
INPUT_HELP_BUTTON = 'metaball_help_button'

_handlers = []


def _ui_message(title, message):
    app = adsk.core.Application.get()
    if not app:
        return
    ui = app.userInterface
    if ui:
        ui.messageBox(message, title)


class MetaballsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            inputs.addIntegerSpinnerCommandInput(INPUT_COUNT, 'Metaballs', 1, 50, 1, 6)
            inputs.addValueInput(INPUT_RADIUS, 'Radio base', 'cm', adsk.core.ValueInput.createByString('2 cm'))
            inputs.addValueInput(INPUT_THRESHOLD, 'Umbral', '', adsk.core.ValueInput.createByReal(0.6))
            inputs.addIntegerSpinnerCommandInput(INPUT_RESOLUTION, 'Resolución', 8, 256, 4, 64)
            inputs.addValueInput(INPUT_SPACING, 'Separación inicial', 'cm', adsk.core.ValueInput.createByString('1.2 cm'))
            inputs.addBoolValueInput(INPUT_PARAMETRIC, 'Crear como modelo paramétrico', True, '', True)
            inputs.addBoolValueInput(INPUT_PREVIEW, 'Crear ejemplo de metaballs', True, '', True)
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
            threshold_input = adsk.core.ValueCommandInput.cast(inputs.itemById(INPUT_THRESHOLD))
            resolution_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById(INPUT_RESOLUTION))
            spacing_input = adsk.core.ValueCommandInput.cast(inputs.itemById(INPUT_SPACING))
            parametric_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_PARAMETRIC))
            preview_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_PREVIEW))

            params = {
                'count': count_input.value,
                'radius': radius_input.value,
                'threshold': threshold_input.value,
                'resolution': resolution_input.value,
                'spacing': spacing_input.value,
                'parametric': parametric_input.value,
                'preview': preview_input.value,
            }

            _create_metaballs(design, params)

            ui.messageBox(
                'Metaballs creadas (plantilla).\n\n'
                'Parámetros usados:\n'
                f"- Cantidad: {params['count']}\n"
                f"- Radio: {params['radius']:.2f} cm\n"
                f"- Umbral: {params['threshold']:.2f}\n"
                f"- Resolución: {params['resolution']}\n"
                f"- Separación: {params['spacing']:.2f} cm\n"
                f"- Ejemplo: {'Sí' if params['preview'] else 'No'}\n"
                f"- Paramétrico: {'Sí' if params['parametric'] else 'No'}",
                APP_NAME,
            )
        except Exception:
            _ui_message(APP_NAME, 'Error al ejecutar el comando:\n{}'.format(traceback.format_exc()))


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


def _help_text():
    return (
        'Metaballs en Fusion 360\n\n'
        '1) Ajusta la cantidad de metaballs y el radio base.\n'
        '2) Usa la separación inicial para controlar cuánto se superponen.\n'
        '3) Activa "Crear ejemplo" para generar esferas guía.\n'
        '4) Activa "modelo paramétrico" para conservar parámetros editables.\n\n'
        'Consejo: Empieza con 4-8 metaballs, radio 2 cm y separación 1.2 cm.'
    )


def _help_popup_text():
    return (
        'Guía detallada\n\n'
        '• El comando crea una fila de esferas como referencia de metaballs.\n'
        '• Ajusta separación y radio hasta ver la superposición deseada.\n'
        '• Luego reemplaza estas esferas por tu flujo de metaballs real.\n'
        '• Los parámetros quedan en "Modificar > Parámetros" si el modo\n'
        '  paramétrico está activado.\n'
    )


def _create_metaballs(design, params):
    # Placeholder for metaball generation logic.
    # In a full implementation you would:
    # 1) Create points or spheres for each metaball.
    # 2) Build an implicit surface and convert to a BRep/mesh.
    # 3) If parametric, store parameters in user parameters and link features.

    if params['parametric']:
        _ensure_parameters(design, params)

    if not params['preview']:
        return

    root = design.rootComponent
    spheres = root.features.sphereFeatures

    radius = params['radius']
    spacing = params['spacing']
    for index in range(params['count']):
        x_offset = index * (radius + spacing)
        center = adsk.core.Point3D.create(x_offset, 0, 0)
        sphere_input = spheres.createInput(center, adsk.core.ValueInput.createByReal(radius))
        spheres.add(sphere_input)



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
    add_or_update('metaball_threshold', params['threshold'], '', 'Umbral de superficie')
    add_or_update('metaball_resolution', params['resolution'], '', 'Resolución de la malla')
    add_or_update('metaball_spacing', params['spacing'], 'cm', 'Separación entre metaballs')


class MetaballsAddIn:
    def __init__(self):
        self.ui = None

    def run(self, context):
        app = adsk.core.Application.get()
        self.ui = app.userInterface
        # Fusion will look for icon files in this folder (e.g., metaballs_command.png).
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
