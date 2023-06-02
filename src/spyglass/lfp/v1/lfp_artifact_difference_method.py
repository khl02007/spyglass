import warnings
from functools import reduce
from typing import Union

import numpy as np

from spyglass.common.common_interval import (
    _union_concat,
    interval_from_inds,
    interval_list_intersect,
)
from spyglass.utils.nwb_helper_fn import get_valid_intervals


def difference_artifact_detector(
    recording: None,
    amplitude_thresh_1st: Union[float, None] = None,
    amplitude_thresh_2nd: Union[float, None] = None,
    proportion_above_thresh_1st: float = 1.0,
    proportion_above_thresh_2nd: float = 1.0,
    removal_window_ms: float = 1.0,
    local_window_ms: float = 1.0,
    sampling_frequency: float = 1000.0,
):
    """Detects times during which artifacts do and do not occur.

    Artifacts are defined as periods where the absolute value of the change in LFP exceeds
    amplitude change thresholds on the proportion of channels specified,
    with the period extended by the removal_window_ms/2 on each side. amplitude change
    threshold values of None are ignored.

    Parameters
    ----------
    recording : lfp eseries
    zscore_thresh : float, optional
        Stdev threshold for exclusion, should be >=0, defaults to None
    amplitude_thresh : float, optional
        Amplitude (ad units) threshold for exclusion, should be >=0, defaults to None
    proportion_above_thresh : float, optional, should be>0 and <=1
        Proportion of electrodes that need to have threshold crossings, defaults to 1
    removal_window_ms : float, optional
        Width of the window in milliseconds to mask out per artifact
        (window/2 removed on each side of threshold crossing), defaults to 1 ms

    Returns
    -------
    artifact_removed_valid_times : np.ndarray
        Intervals of valid times where artifacts were not detected, unit: seconds
    artifact_intervals : np.ndarray
        Intervals in which artifacts are detected (including removal windows), unit: seconds
    """

    valid_timestamps = recording.timestamps

    local_window = np.int(local_window_ms / 2)

    # if both thresholds are None, we skip artifact detection
    if amplitude_thresh_1st is None:
        recording_interval = np.asarray(
            [valid_timestamps[0], valid_timestamps[-1]]
        )
        artifact_times_empty = np.asarray([])
        print("Amplitude threshold is None, skipping artifact detection")
        return recording_interval, artifact_times_empty

    # verify threshold parameters
    (
        amplitude_thresh_1st,
        amplitude_thresh_2nd,
        proportion_above_thresh_1st,
        proportion_above_thresh_2nd,
    ) = _check_artifact_thresholds(
        amplitude_thresh_1st,
        amplitude_thresh_2nd,
        proportion_above_thresh_1st,
        proportion_above_thresh_2nd,
    )

    # want to detect frames without parallel processing
    # compute the number of electrodes that have to be above threshold
    nelect_above_1st = np.ceil(
        proportion_above_thresh_1st * recording.data.shape[1]
    )
    nelect_above_2nd = np.ceil(
        proportion_above_thresh_2nd * recording.data.shape[1]
    )

    # find the artifact occurrences using one or both thresholds, across channels
    # replace with LFP artifact code
    # is this supposed to be indices??
    if amplitude_thresh_1st is not None:
        # first find times with large amp change
        artifact_boolean = np.sum(
            (np.abs(np.diff(recording.data, axis=0)) > amplitude_thresh_1st),
            axis=1,
        )
        above_thresh_1st = np.where(artifact_boolean >= nelect_above_1st)[0]

        # second, find artifacts with large baseline change
        big_artifacts = np.zeros(
            (recording.data.shape[1], above_thresh_1st.shape[0])
        )
        for art_count in np.arange(above_thresh_1st.shape[0]):
            if above_thresh_1st[art_count] <= local_window:
                local_min = local_max = above_thresh_1st[art_count]
            else:
                local_max = np.max(
                    recording.data[
                        above_thresh_1st[art_count]
                        - local_window : above_thresh_1st[art_count]
                        + local_window,
                        :,
                    ],
                    axis=0,
                )
                local_min = np.min(
                    recording.data[
                        above_thresh_1st[art_count]
                        - local_window : above_thresh_1st[art_count]
                        + local_window,
                        :,
                    ],
                    axis=0,
                )
            big_artifacts[:, art_count] = (
                np.abs(local_max - local_min) > amplitude_thresh_2nd
            )

        # sum columns in big artficat, then compare to nelect_above_2nd
        above_thresh = above_thresh_1st[
            np.sum(big_artifacts, axis=0) >= nelect_above_2nd
        ]

    artifact_frames = above_thresh.copy()
    print("detected ", artifact_frames.shape[0], " artifacts")

    # turn ms to remove total into s to remove from either side of each detected artifact
    half_removal_window_s = removal_window_ms / 1000 * 0.5

    if len(artifact_frames) == 0:
        recording_interval = np.asarray(
            [[valid_timestamps[0], valid_timestamps[-1]]]
        )
        artifact_times_empty = np.asarray([])
        print("No artifacts detected.")
        return recording_interval, artifact_times_empty

    artifact_intervals = interval_from_inds(artifact_frames)

    artifact_intervals_s = np.zeros(
        (len(artifact_intervals), 2), dtype=np.float64
    )
    for interval_idx, interval in enumerate(artifact_intervals):
        artifact_intervals_s[interval_idx] = [
            valid_timestamps[interval[0]] - half_removal_window_s,
            valid_timestamps[interval[1]] + half_removal_window_s,
        ]
    artifact_intervals_s = reduce(_union_concat, artifact_intervals_s)

    valid_intervals = get_valid_intervals(
        valid_timestamps, sampling_frequency, 1.5, 0.000001
    )

    # these are artifact times - need to subtract these from valid timestamps
    artifact_valid_times = interval_list_intersect(
        valid_intervals, artifact_intervals_s
    )

    # note: this is a slow step
    list_triggers = []
    for interval in artifact_valid_times:
        list_triggers.append(
            np.arange(
                np.searchsorted(valid_timestamps, interval[0]),
                np.searchsorted(valid_timestamps, interval[1]),
            )
        )

    new_array = np.array(np.concatenate(list_triggers))

    new_timestamps = np.delete(valid_timestamps, new_array)

    artifact_removed_valid_times = get_valid_intervals(
        new_timestamps, sampling_frequency, 1.5, 0.000001
    )

    return artifact_removed_valid_times, artifact_intervals_s


def _check_artifact_thresholds(
    amplitude_thresh_1st,
    amplitude_thresh_2nd,
    proportion_above_thresh_1st,
    proportion_above_thresh_2nd,
):
    """Alerts user to likely unintended parameters. Not an exhaustive verification.

    Parameters
    ----------
        amplitude_thresh_1st: float
        amplitude_thresh_2nd: float
        proportion_above_thresh_1st: float
        proportion_above_thresh_2nd: float

    Return
    ------
        amplitude_thresh_1st: float
        amplitude_thresh_2nd: float
        proportion_above_thresh_1st: float
        proportion_above_thresh_2nd: float

    Raise
    ------
    ValueError: if signal thresholds are negative
    """
    # amplitude or zscore thresholds should be not negative, as they are applied to an absolute signal
    signal_thresholds = [
        t for t in [amplitude_thresh_1st, amplitude_thresh_1st] if t is not None
    ]
    for t in signal_thresholds:
        if t < 0:
            raise ValueError("Amplitude  thresholds must be >= 0, or None")

    # proportion_above_threshold should be in [0:1] inclusive
    if proportion_above_thresh_1st < 0:
        warnings.warn(
            "Warning: proportion_above_thresh must be a proportion >0 and <=1."
            f" Using proportion_above_thresh = 0.01 instead of {str(proportion_above_thresh_1st)}"
        )
        proportion_above_thresh_1st = 0.01
    elif proportion_above_thresh_1st > 1:
        warnings.warn(
            "Warning: proportion_above_thresh must be a proportion >0 and <=1. "
            f"Using proportion_above_thresh = 1 instead of {str(proportion_above_thresh_1st)}"
        )
        proportion_above_thresh_1st = 1
    # proportion_above_threshold should be in [0:1] inclusive
    if proportion_above_thresh_2nd < 0:
        warnings.warn(
            "Warning: proportion_above_thresh must be a proportion >0 and <=1."
            f" Using proportion_above_thresh = 0.01 instead of {str(proportion_above_thresh_2nd)}"
        )
        proportion_above_thresh_2nd = 0.01
    elif proportion_above_thresh_2nd > 1:
        warnings.warn(
            "Warning: proportion_above_thresh must be a proportion >0 and <=1. "
            f"Using proportion_above_thresh = 1 instead of {str(proportion_above_thresh_2nd)}"
        )
        proportion_above_thresh_2nd = 1

    return (
        amplitude_thresh_1st,
        amplitude_thresh_2nd,
        proportion_above_thresh_1st,
        proportion_above_thresh_2nd,
    )
