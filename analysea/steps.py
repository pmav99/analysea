from __future__ import annotations

from typing import Any
from typing import List
from typing import Tuple

import numpy as np
import numpy.typing as npt
import pandas as pd
import ruptures as rpt

from analysea.utils import detect_time_step


# ===================
# STEP FUNCTIONS
# ===================
def step_function_ruptures(
    df: pd.DataFrame, penalty: int = 10
) -> Tuple[pd.DataFrame, npt.NDArray[Any], List[int]]:
    """
    from the ruptures package
    more info here :
    https://github.com/deepcharles/ruptures
    """
    # creation of data
    time_step = detect_time_step(df).total_seconds()
    dt = int(3600 * 3 / time_step)  # one point 6 hours
    signal = np.array(df.interpolate().values[range(0, len(df), dt)])

    # Convert the signal to a 2D array as required by the ruptures library
    signal_2d = signal.reshape(-1, 1)

    c = rpt.costs.CostL1().fit(signal)
    # Perform change point detection using Potts model
    algo = rpt.Pelt(custom_cost=c).fit(signal_2d)
    stepx = algo.predict(pen=penalty)

    res = pd.DataFrame(data=np.zeros(len(df)), index=df.index)
    stepx = np.insert(stepx, 0, 0)
    steps = []
    for i, istep in enumerate(stepx[:-1]):
        step = np.nanmean(
            signal[istep : stepx[i + 1]]
        )  # mean for this part of the signal
        steps.append(step)
        stdd = np.nanstd(
            signal[istep : stepx[i + 1]]
        )  # std dev for this part of the signal
        # removing outliers for the calculation of the mean
        # because the calculation of the step is not perfect
        # this is because we downsample the signal to 3600*3 seconds ie 3 hours
        condition = np.abs(signal[istep : stepx[i + 1]] - step) < stdd
        idx = np.where(condition)
        stepp = np.nanmean(signal[istep : stepx[i + 1]][idx[0]])
        #  spikes for the calculation of the mean
        res.iloc[istep * dt : stepx[i + 1] * dt] = stepp
    return res, stepx, steps
