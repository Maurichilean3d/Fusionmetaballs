import adsk.core, traceback

handlers = []

def handle_error(name):
    app = adsk.core.Application.get()
    app.userInterface.messageBox(f'Error en {name}:\n{traceback.format_exc()}')

class _EventHandler(adsk.core.CommandEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    def notify(self, args):
        try: self.callback(args)
        except: handle_error('EventHandler')