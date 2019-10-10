import psychopy.visual
import psychopy.core
import psychopy.event


win = psychopy.visual.Window(
    size=[800, 800],
    units="pix",
    fullscr=False
)

img = psychopy.visual.ImageStim(
    win=win,
    image="stim.png",
    units="pix"
)

img.draw()

win.flip()

psychopy.event.waitKeys()

