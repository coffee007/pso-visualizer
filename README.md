## If you want to just run the Pygame visualization

Install the following: 
```
pip install pygame
```
Then run vis_new.py

## If you want to build the pso_core engine locally

Install:
```
pip install pygame
pip install pybind11
```

Build the pso_core dll using 
```
python setup.py build_ext --inplace
```
Do not rename the file. Then run vis_new.py.
