import numpy as np
from moviepy.editor import VideoFileClip, concatenate


def read_video(path):
    clip = VideoFileClip(path)
    return clip


def get_averaged_volumes(clip):
    cut = lambda i: clip.audio.subclip(i, i + 1).to_soundarray(fps=22000)
    volume = lambda array: np.sqrt(((1.0 * array) ** 2).mean())
    volumes = [volume(cut(i)) for i in range(0, int(clip.duration - 1))]
    averaged_volumes = np.array([sum(volumes[i:i + 10]) / 10 for i in range(len(volumes) - 10)])
    return averaged_volumes


def choose_times(averaged_volumes):
    increases = np.diff(averaged_volumes)[:-1] >= 0
    decreases = np.diff(averaged_volumes)[1:] <= 0
    peaks_times = (increases * decreases).nonzero()[0]
    peaks_vols = averaged_volumes[peaks_times]
    peaks_times = peaks_times[peaks_vols > np.percentile(peaks_vols, 60)]

    final_times = [peaks_times[0]]
    for t in peaks_times:
        if (t - final_times[-1]) < 60:
            if averaged_volumes[t] > averaged_volumes[final_times[-1]]:
                final_times[-1] = t
        else:
            final_times.append(t)
    return final_times


def extract_summary(final_times, clip):
    final = concatenate([clip.subclip(max(t - 5, 0), min(t + 5, clip.duration)) for t in final_times])
    # final.to_videofile("temp_fast_summary\\Summary of " + fileName + '.mp4')
    return final


def quick_summary(read_path):
    clip = read_video(read_path)
    averaged_volumes = get_averaged_volumes(clip)
    final_times = choose_times(averaged_volumes)
    return final_times, clip

