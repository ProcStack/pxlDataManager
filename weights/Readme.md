Weights will automatically download upon need

Be mindful of disk space, as of February 21st, 2023 ---

All below modules rely on Torch in one way or another,
<br> The based module alone uses 3.91gb of space
<br> So if you arn't utilizing globally installed python modules,
<br> Lets say you are using a virtual environment through Anaconda/Miniconda3/etc.;
<br> Make sure to use that user, if possible, when running pxlImageLabeler


`ClipInterrogator` -
 - Only uses `BLIP` currently

`BLIP` -
 - `model_base_caption_capfilt_large.pth` - *875mb*


`FaceFinder` -
 - `detection_Resnet50_Final.pth` - *106mb*
 - `parsing_parsenet.pth` - *83mb*
