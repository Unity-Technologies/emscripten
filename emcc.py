# Detect what kind of command this is:
# 1. An object file compile: "emcc -c a.c -o a.o" -> ok as is
# 2. A bad static library link: "emcc a.o b.o c.o -o b.bc" -> "emar qcL b.a a.o b.o c.o"
# 3. a final executable link: "emcc -o a.js a.bc b.bc c.bc"

import os, sys, subprocess, shutil, ntpath, tempfile, shlex

output = None

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
  env['EM_CONFIG'] = env['EM_CONFIG'] + '.2'
  proc = subprocess.run(cmd, env=env)
  return proc.returncode

for i in range(len(sys.argv)):
  if sys.argv[i] == '-o':
    output = sys.argv[i+1]
    sys.argv = sys.argv[:i] + sys.argv[i+2:]
    break

# Reroute all nonexisting .bc inputs to .a inputs if they exist:
for i in range(len(sys.argv)):
  if get_suffix(sys.argv[i]) == '.bc':
    a_file = replace_suffix(sys.argv[i], '.a')
    if not os.path.isfile(sys.argv[i]) and os.path.isfile(a_file):
      sys.argv[i] = a_file
    elif os.path.isfile(sys.argv[i]):
      tempname = tempfile.NamedTemporaryFile(suffix=get_filename_without_path(a_file)).name
      shutil.copy(sys.argv[i], tempname)
      sys.argv[i] = tempname
      tempfiles += [tempname]

if output and output.endswith('.bc'):
  a_output = output.replace('.bc', '.a')
  cmd = [sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'emar.py'), 'qcL', a_output] + sys.argv[1:]
  returncode = run(cmd)
  if returncode == 0:
    shutil.move(a_output, output)
else:
  cmd = [sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'emcc2.py')] + sys.argv[1:] + (['-o', output] if output else [])
  if output and output.endswith('.js'):
    cmd += ['-lidbfs.js']
  returncode = run(cmd)

for t in tempfiles:
  try:
    os.remove(t)
  except:
    pass

sys.exit(returncode)
