#!/usr/bin/env python3
import sys
import numpy as np
import sounddevice as sd
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import platform

FS = 48000
CHANNELS = 6
BUFFER_DURATION = 2.0   # seconds visible on screen
BLOCK_SIZE = 1024       # audio callback block size

BUFFER_SIZE = int(FS * BUFFER_DURATION)

if platform.system() == 'Windows':
    DEVICE = 'Microphone (MicNode_6_Ch), Windows WASAPI'
elif platform.system() == 'Darwin':
    DEVICE = 'MicNode_6_Ch'
else:
    DEVICE = 'default'

buffer = np.zeros((BUFFER_SIZE, CHANNELS), dtype=np.float32)
write_idx = 0

def audio_callback(indata, frames, time, status):
    global buffer, write_idx

    if status:
        print(status)

    # normalize int16 -> float
    data = indata.astype(np.float32) / 32768.0

    end_idx = write_idx + frames

    if end_idx < BUFFER_SIZE:
        buffer[write_idx:end_idx] = data
    else:
        split = BUFFER_SIZE - write_idx
        buffer[write_idx:] = data[:split]
        buffer[:frames - split] = data[split:]

    write_idx = (write_idx + frames) % BUFFER_SIZE


app = QtWidgets.QApplication(sys.argv)

win = pg.GraphicsLayoutWidget(title="MicNode 6ch Real-Time Viewer")
win.resize(1000, 800)

plots = []
curves = []

for ch in range(CHANNELS):
    p = win.addPlot(row=ch, col=0)
    p.setLabel('left', f'CH-{ch+1}')
    p.showGrid(x=True, y=True)

    if ch > 0:
        p.setXLink(plots[0])  # sync zoom/pan

    curve = p.plot(pen=pg.mkPen(width=1))

    plots.append(p)
    curves.append(curve)

# time axis
time_axis = np.linspace(-BUFFER_DURATION, 0, BUFFER_SIZE)


def update():
    global buffer, write_idx

    # get ordered buffer (circular unwrap)
    if write_idx == 0:
        data = buffer
    else:
        data = np.vstack((buffer[write_idx:], buffer[:write_idx]))

    for ch in range(CHANNELS):
        curves[ch].setData(time_axis, data[:, ch])


# timer for UI refresh
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(30)  # ~30 FPS

stream = sd.InputStream(
    samplerate=FS,
    channels=CHANNELS,
    dtype='int16',
    blocksize=BLOCK_SIZE,
    device=DEVICE,
    callback=audio_callback
)

with stream:
    win.show()
    sys.exit(app.exec())