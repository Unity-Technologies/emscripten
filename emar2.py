#!/usr/bin/env python3
# Copyright 2016 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

"""Archive helper script

This script acts as a frontend replacement for `llvm-ar`.
"""

import sys

from tools import shared


### XXX Unity local workaround to make llvm-ar "rcL" behave like a "qcL" option (https://bugs.llvm.org/show_bug.cgi?id=52197)
# (we never need a qcL option)
# Possibly helps with https://fogbugz.unity3d.com/f/cases/1371445/
import shlex, os
def read_response_file(response_filename):
  with open(response_filename) as f:
    args = f.read()
  return shlex.split(args)

def substitute_response_files(args):
  new_args = []
  for arg in args:
    if arg.startswith('@'):
      new_args += read_response_file(arg[1:])
    else:
      new_args.append(arg)
  return new_args

if sys.argv[1] == 'qcL':
  argv = substitute_response_files(sys.argv)
  if os.path.isfile(argv[2]):
    try:
      os.remove(argv[2])
    except:
      pass
### XXX End Unity local workaround







#
# Main run() function
#
def run():
  cmd = [shared.LLVM_AR] + sys.argv[1:]
  return shared.run_process(cmd, stdin=sys.stdin, check=False).returncode


if __name__ == '__main__':
  sys.exit(run())
