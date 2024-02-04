from et_engine.storage import FileSystem

# class GeophysicsDataset(et.Dataset):
#     def __init__(self, dockerfile = None):
#         """write the initialization here"""
#         pass

#     def __get__(self, i):
#         """write how to index the dataset here"""
#         pass


# class GeologyModel(et.Distribution):
#     def __init__(self, dockerfile = None):
#         """blah"""
#         pass


# class MonteCarloStep(et.MonteCarlo):
#     def __init__(self, dockerfile = None):
#         """configure any hyperparameters here"""
#         pass

#     def __call__(self, data, model):
#         """controls the execution of one realization"""
#         pass


# class MonteCarloTest(et.Algorithm):
#     def __init__(self, dataset, dockerfile = None):
#         """configure"""
#         self.MC = MonteCarloStep(dataset)

#     def __call__(self, geology):
#         """main algorithm here"""
#         model = geology
        

#         return model


if __name__ == "__main__":
    fs = FileSystem()
    fs.configure()
    # import sys

    # dataset = GeophysicsDataset('/path/to/dataset')
    # init_model = GeologyModel('/path/to/model')
    # algo = MonteCarloTest(dataset)

    # try:
    #     algo.configure()
    # except:
    #     print("configuration error")
    #     sys.exit(1)

    
    """
    Internally, here's what's happening:
        1. dataset is being transferred to the cloud
        2. configurations for any ET resources are being spun up
        3. 'algo' is deployed on a monitoring node
        4. each time a resource is called, the monitoring node checks if it exists, transfers the relevant data, and then kicks off the computation
    """
    # algo(init_model)
    
    




        

