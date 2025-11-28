import numpy as np
import re


def read_rcpsp(fname):


    ppairs = []
    durs = []
    resources = []
    cap = None
    makespan = None

    mode = None
    with open(fname, "r") as f:
        line = 1
        while line:
            line = re.sub(" +", " ", f.readline()).strip()

            if "horizon" in line:
                horizon = int(line.split(" ")[-1])
            elif line.startswith("***"):
                mode = None
            elif "PROJECT INFORMATION" in line:
                mode = "INFO"
                f.readline() # next line contains headers
            elif "PRECEDENCE RELATIONS" in line:
                mode = "PREC"
                f.readline()  # next line contains headers
            elif "REQUESTS/DURATIONS" in line:
                mode = "JOBS"
                f.readline()
                f.readline() # next line contains headers
            elif "RESOURCEAVAILABILITIES" in line:
                mode = "CAP"
                f.readline()  # next line contains headers
            elif "OPTIMAL MAKESPAN" in line:
                mode = "MAKESPAN"
            # actually parse based on mode
            elif mode == "INFO":
                pass
                # parse line based on mode
            elif mode == "PREC":
                job_idx, n_modes, n_succ, *succ = line.split(" ")
                assert int(n_modes) == 1
                ppairs += [(int(job_idx)-1, int(s)-1) for s in succ]
            elif mode == "JOBS":
                job_idx, mode_idx, dur, *rec = line.split(" ")
                durs.append(int(dur))
                irec = [int(r) for r in rec]
                # assert sum(r != 0 for r in irec) <= 1, "Each job should be assigned to exactly one machine, do not support flexible rcpsp yet"
                resources.append(irec)
            elif mode == "CAP":
                cap = [int(r) for r in line.split(" ")]
            elif mode == "MAKESPAN":
                makespan = int(line)


    return {"duration": np.array(durs),
            "precedence": np.array(ppairs),
            "resources": np.array(resources),
            "capacities": np.array(cap),
            "horizon": horizon,
            "optimal": makespan,
            "factor": 0.7}