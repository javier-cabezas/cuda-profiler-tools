#!/usr/bin/env python

from distutils.core import setup

setup(name='cudaprof',
      version='0.1.1',
      description='CUDA Profiler Tools',
      author='Javier Cabezas',
      author_email='javier.cabezas@gmail.com',
      url='https://code.google.com/p/cuda-profiler-tools/',
      packages=[ 'cudaprof', 'cudaprof.gui' ],
      package_dir={'cudaprof': 'tools/cudaprof'},
      scripts=['tools/cuda-profiler']
)

# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
