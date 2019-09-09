from cx_Freeze import setup, Executable

build_options = {"packages":["numpy"]}

setup(name='game',
      version='0.1',
      description='the game',
      options = {"build_exe": build_options},
      executables = [Executable("main.py")])
