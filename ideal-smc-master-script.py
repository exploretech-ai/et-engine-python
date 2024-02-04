import exploretech as et


class GeophysicsDataset(et.Dataset):
    def __init__(self, dockerfile = None):
        """write the initialization here"""
        pass

    def __get__(self, i):
        """write how to index the dataset here"""
        pass


class MonteCarloStep(et.MonteCarlo):
    def __init__(self, dockerfile = None):
        """configure any hyperparameters here"""
        pass

    def __call__(self, data):
        """controls the execution of one realization"""
        pass


class AggregateStep(et.Aggregate):
    def __init__(self, dockerfile = None):
        """configure any hyperparameters here"""
        pass

    def __call__(self):
        """configure what the aggregate step does here"""
        pass


class UpdateStep(et.GPU):
    def __init__(self, dockerfile = None):
        """configure hyperparameters"""
        pass

    def __call__(self):
        """what the update step does"""
        pass


class SMC(et.Algorithm):
    def __init__(self, dockerfile = None):
        """configure"""
        self.MC = MonteCarloStep
        self.Agg = AggregateStep
        self.Update = UpdateStep

    def __call__(self, dataset):
        """main algorithm here"""
        model = dataset
        for i in range(10):
            mc_results = self.MC(model)
            agg_data = self.Agg(mc_results)
            new_model = self.Update(agg_data)
            model = GeophysicsDataset(new_model)

        return model
    

if __name__ == "__main__":
    """
    Execute with: "python ideal-smc-master-script.py"
    """
    import sys

    dataset = GeophysicsDataset('/path/to/dataset')
    algo = SMC()

    try:
        algo.configure(dataset)
    except:
        print("configuration error")
        sys.exit(1)

    algo(dataset)
    """
    Internally, here's what's happening:
        1. dataset is being transferred to the cloud
        2. configurations for any ET resources are being spun up
        3. 'algo' is deployed on a monitoring node
        4. each time a resource is called, the monitoring node checks if it exists, transfers the relevant data, and then kicks off the computation
    """
    
    




        

