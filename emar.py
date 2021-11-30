# This wrapper script fixes .a and .bc inconsistencies in the build process.

import os, sys, subprocess, shutil, ntpath, tempfile, shlex

def read_response_file(response_filename):
  with open(response_filename) as f:
    args = f.read()
  return shlex.split(args)

def substitute_response_files(args):
  new_args = []
  for arg in args:
    if arg.startswith('@'):
      new_args += read_response_file(arg[1:])
    elif arg.startswith('-Wl,@'):
      for a in read_response_file(arg[5:]):
        if a.startswith('-'):
          a = '-Wl,' + a
        new_args.append(a)
    else:
      new_args.append(arg)
  return new_args

sys.argv = substitute_response_files(sys.argv)

def get_filename_without_path(path):
  head, tail = ntpath.split(path)
  return tail or ntpath.basename(head)

def get_suffix(f):
  return os.path.splitext(f)[1]

def replace_suffix(f, new_suffix):
  return os.path.splitext(f)[0] + new_suffix

tempfiles = []

def create_response_file(args):
  response_fd, response_filename = tempfile.mkstemp(suffix='.rsp', text=True)

  WINDOWS = (os.name == 'nt')

  def escape(arg):
    for char in ['\\', '\"'] + (['\''] if not WINDOWS else []):
      arg = arg.replace(char, '\\' + char)
    return arg

  args = [escape(a) for a in args]
  contents = ""

  # Arguments containing spaces need to be quoted.
  for arg in args:
    if ' ' in arg:
      arg = '"%s"' % arg
    contents += arg + '\n'
  with os.fdopen(response_fd, 'w', encoding='utf-8' if WINDOWS else None) as f:
    f.write(contents)

  global tempfiles
  tempfiles += [response_filename]
  return response_filename

def run(cmd):
  if len(cmd) > 10:
    cmd = cmd[:2] + ['@' + create_response_file(cmd[2:])]
  env = os.environ.copy()

  if not os.environ.get('_UNITY_SKIP_REDIRECT_EMCONFIG'):
    redirected_emconfig = env['EM_CONFIG'] + '.2'
    if os.path.isfile(redirected_emconfig):
      env['EM_CONFIG'] = redirected_emconfig

  proc = subprocess.run(cmd, env=env)
  return proc.returncode

# Reroute all nonexisting .bc inputs to .a inputs (and vice versa) if they exist:
if not os.environ.get('_UNITY_SKIP_RENAME_A_BC'):
  for i in range(len(sys.argv)):
    if get_suffix(sys.argv[i]) == '.bc':
      a_file = replace_suffix(sys.argv[i], '.a')
      if not os.path.isfile(sys.argv[i]) and os.path.isfile(a_file):
        sys.argv[i] = a_file
      elif os.path.isfile(sys.argv[i]):
        # Only rename .bc input to .a if not actually a BC file
        with open(sys.argv[i], "rb") as f:
          is_bc_file = f.read(2) == b"BC"
        if not is_bc_file:
          tempname = tempfile.NamedTemporaryFile(suffix=get_filename_without_path(a_file)).name
          shutil.copy(sys.argv[i], tempname)
          sys.argv[i] = tempname
          tempfiles += [tempname]
    elif get_suffix(sys.argv[i]) == '.a': # Reroute all .a inputs to .bc inputs if they exist.
      a_file = sys.argv[i]
      bc_file = replace_suffix(sys.argv[i], '.bc')
      if not os.path.isfile(sys.argv[i]) and os.path.isfile(bc_file):
        sys.argv[i] = bc_file

      if os.path.isfile(sys.argv[i]):
        # Copy the input file with .bc suffix to an input with suffix .a to not confuse emcc.
        with open(sys.argv[i], "rb") as f:
          is_bc_file = f.read(2) == b"BC"
        if get_suffix(sys.argv[i]) == '.bc' and not is_bc_file:
          tempname = tempfile.NamedTemporaryFile(suffix=get_filename_without_path(a_file)).name
          shutil.copy(sys.argv[i], tempname)
          sys.argv[i] = tempname
          tempfiles += [tempname]

cmd = [sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'emar2.py')] + sys.argv[1:]
returncode = run(cmd)

for t in tempfiles:
  try:
    os.remove(t)
  except:
    pass

sys.exit(returncode)
