import os
import shutil
path_name = 'static/'
for s in next(os.walk(path_name*2))[1]:
    shutil.move(path_name*2+s, path_name+s)
shutil.rmtree(path_name*2)