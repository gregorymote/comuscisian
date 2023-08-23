import argparse
from src.stream_analyzer import Stream_Analyzer
import time
from  pulsectl import pulsectl, PulseVolumeInfo
import numpy as np
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=None, dest='device',
                        help='pyaudio (portaudio) device index')
    parser.add_argument('--height', type=int, default=450, dest='height',
                        help='height, in pixels, of the visualizer window')
    parser.add_argument('--n_frequency_bins', type=int, default=400, dest='frequency_bins',
                        help='The FFT features are grouped in bins')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--window_ratio', default='24/9', dest='window_ratio',
                        help='float ratio of the visualizer window. e.g. 24/9')
    parser.add_argument('--sleep_between_frames', dest='sleep_between_frames', action='store_true',
                        help='when true process sleeps between frames to reduce CPU usage (recommended for low update rates)')
    return parser.parse_args()

def convert_window_ratio(window_ratio):
    if '/' in window_ratio:
        dividend, divisor = window_ratio.split('/')
        try:
            float_ratio = float(dividend) / float(divisor)
        except:
            raise ValueError('window_ratio should be in the format: float/float')
        return float_ratio
    raise ValueError('window_ratio should be in the format: float/float')

def run_co():
    state = 'SPDIF'
    pulse = pulsectl.Pulse('my-client')
    sinks = set_sink_volume(state=state, pulse=pulse)

    args = parse_args()
    window_ratio = convert_window_ratio(args.window_ratio)

    ear = Stream_Analyzer(
                    device = args.device,        # Pyaudio (portaudio) device index, defaults to first mic input
                    rate   = None,               # Audio samplerate, None uses the default source settings
                    FFT_window_size_ms  = 256,    # Window size used for the FFT transform
                    updates_per_second  = 1000,  # How often to read the audio stream for new data
                    smoothing_length_ms = 50,    # Apply some temporal smoothing to reduce noisy features
                    n_frequency_bins = args.frequency_bins, # The FFT features are grouped in bins
                    visualize = 0,               # Visualize the FFT features with PyGame
                    verbose   = args.verbose,    # Print running statistics (latency, fps, ...)
                    height    = args.height,     # Height, in pixels, of the visualizer window,
                    window_ratio = window_ratio  # Float ratio of the visualizer window. e.g. 24/9
                    )

    fps = 60  #How often to update the FFT features + display
    last_update = time.time()
    size = fps * 6 
    i = 0
    average = 0
    avg = np.zeros(size) #have a numpy array with averages from the last size seconds to calculate a running average
    while True:
        if (time.time() - last_update) > (1./fps):
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
            avg[i % size] = get_avg(raw_fftx, raw_fft, 18750, 19250) #This range is arbirtrary
            i+=1
            if (i > size):
                average = np.mean(avg)
                print(f'\r{average}', end='')
            current = get_state(average)
            if(current != state):
                state = current
                sinks = set_sink_volume(state=state, pulse=pulse, sinks=sinks)
            
        elif args.sleep_between_frames:
            time.sleep(((1./fps)-(time.time()-last_update)) * 0.99)


def get_sinks(pulse):
    sinks = {}
    for sink in pulse.sink_input_list():
        if('SPDIF' in sink.name):
            sinks['spdif'] = sink
        elif('Playback' in sink.name):
            sinks['playback'] = sink
    if not sinks['spdif']:
        raise KeyError('spdif')   
    if not sinks['playback']:
        raise KeyError('playback')
    return sinks


def set_sink_volume(state, pulse, sinks=None,):
    if not sinks:
        sinks = get_sinks(pulse)
        print(sinks)
    mute = PulseVolumeInfo([0])
    unmute = PulseVolumeInfo([1])
    update = False

    if state == 'SPDIF':
        if sinks['spdif'].volume.value_flat != 1.0:
            pulse.sink_input_volume_set(sinks['spdif'].index, unmute)
            update = True
        if sinks['playback'].volume.value_flat != 0.0:
            pulse.sink_input_volume_set(sinks['playback'].index, mute)
            update = True
    else:
        if sinks['playback'].volume.value_flat != 1.0:
            pulse.sink_input_volume_set(sinks['playback'].index, unmute)
            update = True
        if sinks['spdif'].volume.value_flat != 0.0:
            pulse.sink_input_volume_set(sinks['spdif'].index, mute)
            update = True
    if update:
        sinks = get_sinks(pulse)
    return sinks


def get_state(average):

    if average > 17500 or average < 1000: #These thresholds are arbirtrary
        return 'PLAYBACK'
    else:
        return 'SPDIF'
    

def get_avg(raw_fftx, raw_fft, low, high):
    ind = np.where(np.logical_and(raw_fftx >= low, raw_fftx < high))
    x = ind[0]
    return np.mean(raw_fft[x[0] : x[len(x) - 1]])
    

if __name__ == '__main__':
    run_co()
