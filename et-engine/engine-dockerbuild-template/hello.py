# app.py
import os

name = os.getenv('NAME', 'World')
print(f"Hello, {name}!")
