Weights & Models will automatically download when needed,
<br>&nbsp;&nbsp; *Not* when initial launching pxlDataManager


&nbsp;&nbsp;*As of February 21st, 2023 ---*
<br/>The below modules rely on Torch in one way or another,
<br/>&nbsp;&nbsp; The Torch based module alone uses 3.91gb of space
<br/> So if you arn't utilizing globally installed python modules,
<br/>&nbsp;&nbsp; Lets say you are using a virtual environment through Anaconda/Miniconda3/etc.
<br/>&nbsp;&nbsp;&nbsp;&nbsp; Make sure to activate a user with Torch, *if possible,* when running pxlDataManager or it's stand-alone utility scripts

All dependencies & models below total roughly - ***6.0gb***

***Be mindful of your disk space!***

<hr/>

### `ClipInterrogator`
- Dependencies - 
  - Torch - *3.91gb*
  - Torch Vision - 13.5mb
- Models -
  - `ViT-L/14` ; *(CLIP)*
    - `./weights/ViT-L-14.pt` - *910mb*
  - `BLIP`; *(Image2Prompt)*
    - `./weights/BLIP/model_base_caption_capfilt_large.pth` - *875mb*
<br/>

### `FaceFinder` 
- Dependencies - 
  - Torch - *3.91gb*
  - Basicsr - 1.2mb
  - Facexlib - 344kb
  - CV2 - *103mb*
- Models -
  - `.weights/FaceFinder/detection_Resnet50_Final.pth` - *106mb*
  - `.weights/FaceFinder/parsing_parsenet.pth` - *83mb*
