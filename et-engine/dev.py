from et_engine.storage import FileSystem, Dataset
from et_engine.algorithm import Algorithm 
from et_engine.compute import ComputeBackend

class VectorDataset(Dataset):
    def __init__(self, arr):
        assert(len(arr) == 3)
        self.arr = arr

    def __str__(self):
        return "[" + ", ".join([str(i) for i in self.arr]) + "]"

class TestAlgorithm(Algorithm):
    def __init__(self, **kwargs):
        super().__init__(VectorDataset, VectorDataset, **kwargs)

    def run(self, InputDataset):
        new_arr = [elem + 3 for elem in InputDataset.arr]            
        return VectorDataset(new_arr)


if __name__ == "__main__":
    import time

    # fs = FileSystem()
    compute_backend = ComputeBackend('dev-dockerfile', 'dev-helloworld.py')
    input_data = VectorDataset([0,0,0])

    
    algo = TestAlgorithm(id="cd80bc66-a489-4802-a734-389ee9ffd98f")
    # print(algo.id)

    # algo.provision()
    
    
    # output = algo.build('dev-dockerfile', 'dev-helloworld.py')
    # print(output)
    
    
    # time.sleep(200)
    # output_data = algo(input_data)


    # time.sleep(200)
    output = algo.destroy()
    print(output)

    # print(input_data)
    # print(output_data)
    



        

