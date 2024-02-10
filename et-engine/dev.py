from et_engine.storage import FileSystem, Dataset
from et_engine.algorithm import BaseAlgorithm 
from et_engine.compute import ComputeBackend

class VectorDataset(Dataset):
    def __init__(self, arr):
        assert(len(arr) == 3)
        self.arr = arr

    def __str__(self):
        return "[" + ", ".join([str(i) for i in self.arr]) + "]"

class TestAlgorithm(BaseAlgorithm):
    def __init__(self):
        super().__init__(fs, VectorDataset, VectorDataset)

    def run(self, InputDataset):
        new_arr = [elem + 3 for elem in InputDataset.arr]            
        return VectorDataset(new_arr)


if __name__ == "__main__":
    import time

    fs = FileSystem()
    compute_backend = ComputeBackend('dev-dockerfile', 'dev-helloworld.py')
    input_data = VectorDataset([0,0,0])

    
    algo = TestAlgorithm()
    # id = algo.provision(fs, compute_backend)
    # print(id)
    algo.id = "e4b378b9118e495496c1a1d8234af117"
    
    
    # output = algo.configure(fs, compute_backend)
    # print(output)
    
    
    # time.sleep(300)
    # output_data = algo(input_data)


    # time.sleep(300)
    output = algo.destroy()
    print(output)

    # print(input_data)
    # print(output_data)
    



        

