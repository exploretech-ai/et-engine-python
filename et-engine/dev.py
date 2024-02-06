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
    fs = FileSystem()
    compute_backend = ComputeBackend()

    algo = TestAlgorithm()
    # algo.provision(fs, compute_backend)
    
    input_data = VectorDataset([0,0,0])
    output_data = algo(input_data)

    # print(input_data)
    # print(output_data)
    



        

