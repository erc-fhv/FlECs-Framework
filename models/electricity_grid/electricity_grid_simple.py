class Grid():
    def __init__(self, name):
        self.name = name
        self.delta_t = 60  # s

        self.inputs = [f'P_node_*'] 
        self.outputs = ['P_substation']

    def step(self, time, **P_node):
        P_substation = sum(P_node.values())

        return {'P_substation': P_substation}
    