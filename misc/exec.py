
class PipeReader(threading.Thread):
    """Read and write pipes using threads.
    """ 
    def __init__(self, result, pipe):
        threading.Thread.__init__(self)
        self.result = result
        self.pipe = pipe

    def run(self):
        try:
            while True:
                chunk = self.pipe.read()
                if not chunk:
                    break
                self.result.append( chunk )
        finally:
            self.pipe.close()

def _run_prog(self,prog='nop',args=''):
    runprog=self._get_prog(prog)
    cmd=' '.join([runprog,args])
    p = subprocess.Popen(cmd, 
                         shell=True,
                         stdin=subprocess.PIPE, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         close_fds=False)
    (child_stdin,
     child_stdout,
     child_stderr) = (p.stdin, p.stdout, p.stderr)
    # Use threading to avoid blocking
    data = []
    errors = []
    threads = [PipeReader(data, child_stdout),
               PipeReader(errors, child_stderr)]
    for t in threads:
        t.start()

    self.write(child_stdin)
    child_stdin.close()

    for t in threads:
        t.join()

    if data==[]:
        raise IOError("".join(errors))

    if len(errors)>0:
        warnings.warn("".join(errors),RuntimeWarning)

    return "".join(data)
