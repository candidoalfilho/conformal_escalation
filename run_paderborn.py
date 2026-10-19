#!/usr/bin/env python3
"""Compatibility wrapper: equivalent to  python run_experiments.py --dataset paderborn [e1 ... e6]"""
import sys, runpy
sys.argv = ["run_experiments.py", "--dataset", "paderborn", *sys.argv[1:]]
runpy.run_path("run_experiments.py", run_name="__main__")
