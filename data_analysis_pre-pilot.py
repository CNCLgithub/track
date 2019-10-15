import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import pandas as pd


def frame_image(img, frame_width, frame_height):
    b = frame_width  # border width in pixel
    h = frame_height  # border height in pixel
    ny, nx = img.shape[0], img.shape[1]  # resolution / number of pixels in x and y
    if img.ndim == 3:  # rgb or rgba array
        framed_img = np.ones((h+ny+h, b+nx+b, img.shape[2]))
    elif img.ndim == 2:  # grayscale image
        framed_img = np.ones((h+ny+h, b+nx+b))
    framed_img[h:-h, b:-b] = img
    return framed_img


# Define some directories/parameters
stim_dir = 'stimuli'
data_dir = 'data'
res_dir = 'results'
scnWidth, scnHeight = (1920, 1080)

# Read all data into a pandas DataFrame
data = pd.DataFrame()
labels = []
data_list = os.listdir(data_dir)
for data_name in data_list:
    subj_data = pd.read_table(os.path.join(data_dir, data_name))
    labels.append(subj_data['RECORDING_SESSION_LABEL'].iloc[0])
    data = data.append(subj_data)

# Loop through subjects and make the summary plot
for subj_label in labels:
    subj_data = data[data['RECORDING_SESSION_LABEL'] == subj_label]
    subj_data['CURRENT_FIX_DURATION'] = subj_data['CURRENT_FIX_DURATION']
    subj_id = str.split(subj_label, '_')[1]
    stim_id = str.split(subj_label, '_')[-1]
    stim_img = mpimg.imread(os.path.join(stim_dir, 'stim_'+str(stim_id)+'.png'))
    img_with_screen = frame_image(stim_img, int((scnWidth-stim_img.shape[1])/2), int((scnHeight-stim_img.shape[0])/2))
    f, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(img_with_screen)
    # sns.scatterplot(data=subj_data, ax=ax, x='CURRENT_FIX_X', y='CURRENT_FIX_Y', size='CURRENT_FIX_DURATION',
    #                 facecolors='none', edgecolors='b')
    for fix_idx, fix in subj_data.iterrows():
        ax.plot(fix['CURRENT_FIX_X'], fix['CURRENT_FIX_Y'], 'kx', markersize=3)
        l = ax.plot(fix['CURRENT_FIX_X'], fix['CURRENT_FIX_Y'], 'o', fillstyle='none',
                markersize=fix['CURRENT_FIX_DURATION']/1000*10)
        ax.text(fix['CURRENT_FIX_X'], fix['CURRENT_FIX_Y'], str(fix_idx+1), color=l[0].get_color(), horizontalalignment='center')

    plt.savefig(os.path.join(res_dir, subj_label+'.png'))
