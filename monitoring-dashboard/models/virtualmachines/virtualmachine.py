vmSnapshots = {}

class VirtualMachine(object):
    name = None
    hardware = None
    meta = None
    network = None
    storage = None

    def __init__(self, name):
        self.name = name
        self.hardware = {}
        self.meta = {}
        self.network = {}
        self.storage = {}
        self.app = {}
        vmSnapshots[name] = self

    def __repr__(self):
        return self.name

    def update_vm_hardware(self, params):
        self.hardware = params

    def update_vm_meta(self, params):
        self.meta = params

    def update_vm_network(self, params):
        self.network = params

    def update_vm_storage(self, params):
        self.storage = params

    def update_vm_app(self, params):
        self.app = params
    
    def display_vm_data(self):
        print "vm meta: ", + self.meta
