"""toplevel setup/teardown for parallel tests."""

#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import tempfile
import time
from subprocess import Popen, PIPE, STDOUT

from IPython.utils.path import get_ipython_dir
from IPython.parallel import Client

processes = []
blackhole = tempfile.TemporaryFile()

# nose setup/teardown

def setup():
    cp = Popen('ipcontroller --profile iptest -r --log-level 10 --log-to-file --usethreads'.split(), stdout=blackhole, stderr=STDOUT)
    processes.append(cp)
    engine_json = os.path.join(get_ipython_dir(), 'cluster_iptest', 'security', 'ipcontroller-engine.json')
    client_json = os.path.join(get_ipython_dir(), 'cluster_iptest', 'security', 'ipcontroller-client.json')
    tic = time.time()
    while not os.path.exists(engine_json) or not os.path.exists(client_json):
        if cp.poll() is not None:
            print cp.poll()
            raise RuntimeError("The test controller failed to start.")
        elif time.time()-tic > 10:
            raise RuntimeError("Timeout waiting for the test controller to start.")
        time.sleep(0.1)
    add_engines(1)

def add_engines(n=1, profile='iptest'):
    rc = Client(profile=profile)
    base = len(rc)
    eps = []
    for i in range(n):
        ep = Popen(['ipengine']+ ['--profile', profile, '--log-level', '10', '--log-to-file'], stdout=blackhole, stderr=STDOUT)
        # ep.start()
        processes.append(ep)
        eps.append(ep)
    tic = time.time()
    while len(rc) < base+n:
        if any([ ep.poll() is not None for ep in eps ]):
            raise RuntimeError("A test engine failed to start.")
        elif time.time()-tic > 10:
            raise RuntimeError("Timeout waiting for engines to connect.")
        time.sleep(.1)
        rc.spin()
    rc.close()
    return eps

def teardown():
    time.sleep(1)
    while processes:
        p = processes.pop()
        if p.poll() is None:
            try:
                p.terminate()
            except Exception, e:
                print e
                pass
        if p.poll() is None:
            time.sleep(.25)
        if p.poll() is None:
            try:
                print 'killing'
                p.kill()
            except:
                print "couldn't shutdown process: ", p
    
