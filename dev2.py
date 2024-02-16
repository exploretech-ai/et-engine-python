from et_engine.storage import FileSystem, Dataset
from et_engine.workflows import Workflow, Module
from et_engine.compute import ComputeBackend
import et_engine as et


if __name__ == "__main__":
    

    algo = Workflow(id="4827cb7f-a68c-4782-a7f4-2872ee8007c2")
    test_module = Module("module1")

    algo.add_module(test_module, connection = et.workflows.END())
    print(algo.graph)
    # response = algo.submit()
    
    
    output = algo.build('dev-dockerfile', 'dev-helloworld.py')
    # print(output)


        

