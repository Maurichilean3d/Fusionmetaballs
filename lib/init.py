import adsk.core, adsk.fusion, math
from .lib import fusion360utils as futil
from . import config

_handlers = []

def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmd_def = ui.commandDefinitions.itemById(config.CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(config.CMD_ID, 'Metaballs', 'Crea esferas metaball', '')

        def command_created(args):
            inputs = args.command.commandInputs
            inputs.addIntegerSpinnerCommandInput('count', 'Cantidad', 1, 50, 1, 6)
            inputs.addValueInput('radius', 'Radio', 'cm', adsk.core.ValueInput.createByReal(2.0))
            inputs.addValueInput('spacing', 'Separación', 'cm', adsk.core.ValueInput.createByReal(1.2))
            
            drop = inputs.addDropDownCommandInput('layout', 'Arreglo', 0)
            drop.listItems.add('Línea', True)
            drop.listItems.add('Círculo', False)
            
            args.command.execute.add(futil._EventHandler(command_execute))

        def command_execute(args):
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            inputs = args.command.commandInputs
            
            cnt = inputs.itemById('count').value
            rad = inputs.itemById('radius').value
            spc = inputs.itemById('spacing').value
            lay = inputs.itemById('layout').selectedItem.name

            root = design.rootComponent
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = "Metaballs Group"
            
            spheres = comp.features.sphereFeatures
            for i in range(cnt):
                if lay == 'Círculo':
                    angle = (2 * math.pi / cnt) * i
                    dist = (rad + spc) * cnt / (2 * math.pi)
                    pt = adsk.core.Point3D.create(dist * math.cos(angle), dist * math.sin(angle), 0)
                else:
                    pt = adsk.core.Point3D.create(i * (rad + spc), 0, 0)
                
                sph_inp = spheres.createInput(pt, adsk.core.ValueInput.createByReal(rad))
                spheres.add(sph_inp)

        # Registro del evento
        handler = futil._EventHandler(command_created)
        cmd_def.commandCreated.add(handler)
        _handlers.append(handler)

        # Añadir al panel
        panel = ui.workspaces.itemById(config.WORKSPACE_ID).toolbarPanels.itemById(config.PANEL_ID)
        if not panel.controls.itemById(config.CMD_ID):
            panel.controls.addCommand(cmd_def).isPromoted = True

    except:
        futil.handle_error('run')

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        panel = ui.workspaces.itemById(config.WORKSPACE_ID).toolbarPanels.itemById(config.PANEL_ID)
        ctrl = panel.controls.itemById(config.CMD_ID)
        if ctrl: ctrl.deleteMe()
        cmd_def = ui.commandDefinitions.itemById(config.CMD_ID)
        if cmd_def: cmd_def.deleteMe()
    except:
        pass