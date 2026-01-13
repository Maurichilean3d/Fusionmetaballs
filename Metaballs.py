# Fusion 360 Metaballs Add-in
# Description: UI-driven metaball preview with parametric options and guided help.

import adsk.core
import adsk.fusion
import adsk.cam
import math
import os
import traceback

APP_NAME = 'Metaballs'
CMD_ID = 'metaballs_command'
CMD_NAME = 'Metaballs'
CMD_DESC = 'Create metaball-like previews with parametric controls.'

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
BUTTON_ID = 'MetaballsButton'

# Input IDs
INPUT_COUNT = 'metaball_count'
INPUT_RADIUS = 'metaball_radius'
INPUT_SPACING = 'metaball_spacing'
INPUT_LAYOUT = 'metaball_layout'
INPUT_PARAMETRIC = 'metaball_parametric'
INPUT_PREVIEW = 'metaball_preview'
INPUT_UNION = 'metaball_union'
INPUT_CLEAR = 'metaball_clear_previous'
INPUT_HELP = 'metaball_help'
INPUT_HELP_BUTTON = 'metaball_help_button'

_handlers = []


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
        '3) Activa "Crear preview" para ver las esferas.\n'
        '4) Si quieres un sólido único, activa "Unir cuerpos".\n\n'
        'Consejo: inicia con 6 metaballs, radio 2 cm y separación 1.2 cm.'
    )


def _help_popup_text():
    return (
        'Guía detallada\n\n'
        '• El preview crea esferas guía que simulan metaballs.\n'
        '• Ajusta radio y separación hasta ver la superposición deseada.\n'
        '• "Unir cuerpos" combina las esferas en un sólido único.\n'
        '• Puedes repetir el comando y limpiar previews anteriores.\n'
        '• En modo paramétrico, los parámetros quedan en Modificar > Parámetros.'
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

            inputs.addBoolValueInput(INPUT_PREVIEW, 'Crear preview de metaballs', True, '', True)
            inputs.addBoolValueInput(INPUT_UNION, 'Unir cuerpos', True, '', True)
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
            preview_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_PREVIEW))
            union_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_UNION))
            clear_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_CLEAR))
            parametric_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INPUT_PARAMETRIC))

            params = {
                'count': count_input.value,
                'radius': radius_input.value,
                'spacing': spacing_input.value,
                'layout': layout_input.selectedItem.name,
                'preview': preview_input.value,
                'union': union_input.value,
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
                f"- Preview: {'Sí' if params['preview'] else 'No'}\n"
                f"- Unir cuerpos: {'Sí' if params['union'] else 'No'}",
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
            points.append(adsk.core.Point3D.create(x, y, 0))
    else:
        for index in range(count):
            x = index * (radius + spacing)
            points.append(adsk.core.Point3D.create(x, 0, 0))
    return points


def _create_metaballs(design, params):
    root = design.rootComponent
    if params['clear']:
        _clear_preview(root)

    if not params['preview']:
        return

    component = _create_preview_component(root)
    spheres = component.features.sphereFeatures

    points = _layout_positions(params['count'], params['radius'], params['spacing'], params['layout'])
    bodies = []
    for point in points:
        sphere_input = spheres.createInput(point, adsk.core.ValueInput.createByReal(params['radius']))
        sphere = spheres.add(sphere_input)
        bodies.append(sphere.bodies.item(0))

    if params['union'] and len(bodies) > 1:
        combine = component.features.combineFeatures
        combine_input = combine.createInput(bodies[0], adsk.core.ObjectCollection.create())
        for body in bodies[1:]:
            combine_input.toolBodies.add(body)
        combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combine_input.isKeepToolBodies = False
        combine.add(combine_input)


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
