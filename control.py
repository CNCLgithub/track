from __future__ import division

import psychopy

from psychopy import visual, core, event, data, monitors
import random, time, math, datetime
import numpy  # can't be imported as np bc of pylink compatibility
import os
import copy
import pylink
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
from PIL import Image
import json

tk = pylink.EyeLink('100.1.1.1')  # ip address for the eyetracker
stim_id = 4

# get the current working directory
curr_dir = os.getcwd()
output_dir = os.path.join(curr_dir, 'output-v2')


# a function for presenting text
def textScreen(text, keyList, timeOut):
    textStim.setText(text)
    textStim.draw()
    win.flip()
    if timeOut == 0:
        event.waitKeys(maxWait=float('inf'), keyList=keyList)
    else:
        timer.reset()
        while timer.getTime() < timeOut:
            pass


# open the edf data file
# Note that the file name cannot exceeds 8 characters
# please open eyelink data files early to record as much info as possible
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

try:
    subj_id = numpy.load(os.path.join(output_dir, 'subjectcounter.npy'))[0]
    numpy.save(os.path.join(output_dir, 'subjectcounter.npy'), numpy.array([subj_id + 1]))
except:
    subj_id = 0
    numpy.save(os.path.join(output_dir, 'subjectcounter.npy'), numpy.array([subj_id + 1]))

dataFileName = 'subj_' + str(subj_id) + '_' + str(stim_id) + '.EDF'
tk.openDataFile(dataFileName)

# Initialize custom graphics for camera setup & drift correction
scnWidth, scnHeight = (1920, 1080)

# you MUST specify the physical properties of your monitor first, otherwise you won't be able to properly use
# different screen "units" in psychopy. One may define his/her monitor object within the GUI, but
# I find it is a better practice to put things all under control in the experimental script instead.
mon = monitors.Monitor('dell27', width=60.0, distance=60.0)
mon.setSizePix((scnWidth, scnHeight))
win = visual.Window((scnWidth, scnHeight), fullscr=True,
                    monitor=mon, color=[0, 0, 0], units='pix',
                    allowStencil=True, autoLog=False)

# call the custom calibration routine "EyeLinkCoreGraphicsPsychopy.py", instead of the default
# routines that were implemented in SDL
genv = EyeLinkCoreGraphicsPsychoPy(tk, win)
pylink.openGraphicsEx(genv)

# STEP V: Set up the tracker
# we need to put the tracker in offline mode before we change its configurations
tk.setOfflineMode()

# sampling rate, 250, 500, 1000, or 2000; this command won't work for EyeLInk II/I
tk.sendCommand('sample_rate 500')

# inform the tracker the resolution of the subject display
# [see Eyelink Installation Guide, Section 8.4: Customizing Your PHYSICAL.INI Settings ]
tk.sendCommand("screen_pixel_coords = 0 0 %d %d" % (scnWidth - 1, scnHeight - 1))

# save display resolution in EDF data file for Data Viewer integration purposes
# [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
tk.sendMessage("DISPLAY_COORDS = 0 0 %d %d" % (scnWidth - 1, scnHeight - 1))

# specify the calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
tk.sendCommand("calibration_type = HV9")  # tk.setCalibrationType('HV9') also works, see the Pylink manual

# specify the proportion of subject display to calibrate/validate (OPTIONAL, useful for wide screen monitors)
# tk.sendCommand("calibration_area_proportion 0.85 0.83")
# tk.sendCommand("validation_area_proportion  0.85 0.83")

# Using a button from the EyeLink Host PC gamepad to accept calibration/drift check target (optional)
# tk.sendCommand("button_function 5 'accept_target_fixation'")

# the model of the tracker, 1-EyeLink I, 2-EyeLink II, 3-Newer models (100/1000Plus/DUO)
eyelinkVer = tk.getTrackerVersion()

# turn off scenelink camera stuff (EyeLink II/I only)
if eyelinkVer == 2: tk.sendCommand("scene_camera_gazemap = NO")

# Set the tracker to parse Events using "GAZE" (or "HREF") data
tk.sendCommand("recording_parse_type = GAZE")

# Online parser configuration: 0-> standard/cognitive, 1-> sensitive/psychophysiological
# the Parser for EyeLink I is more conservative, see below
# [see Eyelink User Manual, Section 4.3: EyeLink Parser Configuration]
if eyelinkVer >= 2: tk.sendCommand('select_parser_configuration 0')

# get Host tracking software version
hostVer = 0
if eyelinkVer == 3:
    tvstr = tk.getTrackerVersionString()
    vindex = tvstr.find("EYELINK CL")
    hostVer = int(float(tvstr[(vindex + len("EYELINK CL")):].strip()))

# set link and EDF file contents (see section 4.6 of the EyeLink user manual)
# for sample data, version 4 (EyeLink 100 and newer trackers) added remote tracking,
# and thus the 'HTARGET' data; for link data, the 'FIXUPDATE' event can be useful for HCI applications
tk.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
tk.sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,BUTTON,INPUT")
if hostVer >= 4:
    tk.sendCommand("file_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,HTARGET,INPUT")
    tk.sendCommand("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,HTARGET,INPUT")
else:
    tk.sendCommand("file_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,INPUT")
    tk.sendCommand("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,INPUT")

# show some instructions here.
msg = visual.TextStim(win, text='Press ENTER twice (or sometimes three times) to calibrate the tracker')
msg.draw()
win.flip()
event.waitKeys()

# set up the camera and calibrate the tracker
tk.doTrackerSetup()

win = visual.Window(fullscr=True, allowGUI=False,
                    units='pix', winType='pyglet',
                    colorSpace='rgb255', color=[255, 255, 255])

msg = visual.TextStim(win, color='black',
                      text='You will be presented with an image of a scene consisting of multiple objects.\n'
                           'If the perceived shape of the objects in the scene changes, please press space bar.\n'
                           'Afterwards, you will be asked whether the objects were right side up or upside down.\n\n'
                           'Press space bar to see the image.')
msg.draw()
win.flip()
event.waitKeys()

# textStim = visual.TextStim(win, color='black', pos=(0, 0), height=32, wrapWidth=800, font = 'Helvetica')
stim_image = 'stimuli/stim_' + str(stim_id) + '.png'

img = psychopy.visual.ImageStim(
    win=win,
    image=stim_image,
    units="pix"
)
# img.pos += (0, 150)

# ------- INSTRUCTIONS & PRACTICE ------ #
# textScreen("Enter text here.",'space',0)

# close the EDF data file
tk.setOfflineMode()
# send message to eyetracker
tk.sendMessage('TRIALID_1')

# start recording, parameters specify whether events and samples are
# stored in file, and available over the link
error = tk.startRecording(1, 1, 1, 1)
pylink.pumpDelay(100)  # wait for 100 ms to make sure data of interest is recorded

# determine which eye(s) are available
eyeTracked = tk.eyeAvailable()
if eyeTracked == 2:
    eyeTracked = 1

img.draw()

win.flip()

"""
dt = tk.getNewestSample()
if (dt != None):
        if eyeTracked == 1 and dt.isRightSample():
                gazePos = dt.getRightEye().getGaze()
"""

tk.sendMessage('image_onset')

# check if the subject pressed space bar (= perception flipped) or waited until timeout (perception did not flip)
key = event.waitKeys(maxWait=20)
if key is None:  # time-out
    flipped_info = 'not flipped'
else:
    flipped_info = 'flipped'

# send a message to mark the end of trial
# [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
tk.sendMessage('TRIAL_RESULT')
pylink.pumpDelay(100)
tk.stopRecording()  # stop recording

# close the EDF data file
tk.setOfflineMode()
tk.closeDataFile()
pylink.pumpDelay(100)

# ask how the objects in the image were perceived
if flipped_info == 'flipped':
    msg = visual.TextStim(win, color='black',
                          text='What did you perceive at FIRST SIGHT before the image flipped?\n'
                               'Were the objects right side up (press r) or upside down (press u)?')
else:
    msg = visual.TextStim(win, color='black',
                          text='Did you perceive the objects to be right side up (press r) or upside down (press u)?')
msg.draw()
win.flip()
key = event.waitKeys()
if key == 'r' or key == 'u':
    perceived_orientation = key
else:
    perceived_orientation = 'invalid'

# store custom data as JSON. Let's try to integrate that into the EDF later on.
with open(os.path.join(output_dir, 'subj_' + str(subj_id) + '.json'), 'w') as fp:
    json.dump({'flipped': flipped_info, 'perceived_orientation': perceived_orientation}, fp, sort_keys=True, indent=4)


# Get the EDF data and say goodbye
msg.text = 'Data transferring.....'
msg.draw()
win.flip()
tk.receiveDataFile(dataFileName, os.path.join(output_dir, dataFileName))
pylink.pumpDelay(100)

# close the link to the tracker
tk.close()

# close the graphics
pylink.closeGraphics()
win.close()
core.quit()
