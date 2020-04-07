"""
Installer for PyTimber for the SWAN environment.

Installs PyTimber into a special directory and then sets the sys.path
to point to it.

"""
# Note: This script must be run inside Python so that it can control
#       things like the sys.path

_locals_before = set(locals())

import os
import site
import subprocess
import sys


def run_w_stream(cmd, env=None):
    full_env = os.environ.copy()
    full_env.update(env or {})
    print('Running: ', ' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, env=full_env)
    while not proc.poll():
       line = proc.stdout.readline()
       if line:
           sys.stdout.write(line)
       else:
          break
    # Capture any remaining stdout.
    for line in proc.stdout.readlines():
        sys.stdout.write(line)

install_loc=os.path.join(os.environ['HOME'], 'python', 'environments', 'pytimber3')


# Disable site.getusersitepackages so that we have non .local JARs (bad practice).
# This doesn't prevent .local/lib from working (it would still be on the sys.path) but does
# influence how cmmnbuild-dep-manager searches for its JARs.
# https://gitlab.cern.ch/scripting-tools/cmmnbuild-dep-manager/-/blob/v2.4.0/cmmnbuild_dep_manager/cmmnbuild_dep_manager.py#L217
if hasattr(site, 'getusersitepackages'):
    site.__dict__.pop('getusersitepackages')


# Put the environment on the path:
env_pkgs = os.path.join(install_loc, 'lib', 'python3.6', 'site-packages')
if sys.path[2] != env_pkgs:
    sys.path.insert(2,  env_pkgs)    
    

if not os.path.exists(install_loc):
    print('Creating an environment in {}. This can take a while.'.format(install_loc))
    # This is quite slow on EOS, so try to not call it if we can avoid.
    cmd = [sys.executable, '-m', 'venv', install_loc, '--system-site-packages']
    run_w_stream(cmd)

    env_py = os.path.join(install_loc, 'bin', 'python')
    cmd = [env_py, '-m', 'pip', 'install', '--upgrade', 'pip', '--prefix={}'.format(install_loc)]
    run_w_stream(cmd)

    env = {'PIP_INDEX_URL': 'http://acc-py-repo.cern.ch:8081/repository/vr-py-releases/simple',
           'PIP_TRUSTED_HOST': 'acc-py-repo.cern.ch'}
    cmd = [env_py, '-m', 'pip', 'install', 'pytimber==3.*']
    run_w_stream(cmd, env)
    
    print('Resolving JARs for PyTimber')
    import cmmnbuild_dep_manager
    cmmnbuild_dep_manager.Manager().resolve()
    print('All done!')
else:
    print('Using existing environment in {}'.format(install_loc))


import pytimber
if not pytimber.__version__.startswith('3.'):
    print("Error installing newer version of PyTimber. " +
          "You have version {}. ".format(pytimber.__version__) +
          "Please try restarting the kernel and re-running.")

# Tidy up since this is being run in the active kernel environment
for local_before in set(locals()) - _locals_before:
    locals().pop(local_before)
locals().pop('_local_before', None)