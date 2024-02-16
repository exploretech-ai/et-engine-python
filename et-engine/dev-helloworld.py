# app.py
import os

name = os.getenv('NAME', 'Underworld')
print(f"Hello, {name}!")
print("Hello, Underworld - without environment variable")


# This app mimics a Monte Carlo simulation
#     - Draw a random 3-digit number
#     - Write the 3-digit number to a text file in a separate directory called <bucket>/realizations/i.txt

# import numpy as np

# random_number = np.random.random(1)


# from et_engine.storage import FileSystem

# filesystem = FileSystem('68cdad4af35945329ed719b19072b71a')


# filesystem.write(str(random_number))
# print(random_number)