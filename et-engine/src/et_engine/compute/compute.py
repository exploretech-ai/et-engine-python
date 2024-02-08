

class ComputeBackend:
    def __init__(self, dockerfile, appfile):
        self.dockerfile = dockerfile
        self.app = appfile

    def provision(self):
        with open(self.dockerfile) as f:
            dockerfile = f.read()
        with open(self.app) as f:
            app = f.read()

        return {
            'storage': 'new',
            'compute': 'SingleNode',
            'dockerfile': dockerfile,
            'app': app
        }



