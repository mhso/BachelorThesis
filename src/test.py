class NetworkThing:
    networks = {}
    curr_step = 0

    def save_stuff(self, step, network):
        self.networks[step] = network
        if len(self.networks) > 5:
            # Don't remove latest macro network.
            macro = round(self.curr_step, -1)
            macro = macro if macro < self.curr_step else macro - 10
            if macro == 0:
                macro = -1
            # Find step of oldest nework, apart from the macro network.
            lowest_step = self.curr_step
            for s in self.networks:
                if s < lowest_step and s != macro:
                    lowest_step = s
            # Copy all networks, but the oldest.
            new_dict = dict()
            for s, n in self.networks.items():
                if s != lowest_step:
                    new_dict[s] = n
            self.networks = new_dict
        self.curr_step = step

ns = NetworkThing()
for i in range(28):
    ns.save_stuff(i, "wow"+str(i))

print(ns.networks)
