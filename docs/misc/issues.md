# Known issues

- The Ardennes department does not provide any information on the housing units per building in BD-TOPO. As a fix, keep all buildings by assigning them exactly one housing unit. This is the best we can do for now. (See `data/bdtopo/raw.py`)

- The 2024 edition of IRIS contains the municipality 14581 (Aurseulles). The data is a bit ahead of time since all other data sets that refer to 2024 still contain the this municipality with the code 14011. Therefore, we replace the identifier here. This fix can be removed for future versions of the data. (See `data/spatial/iris.py`)