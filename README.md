# pxlDataManager v0.0.2
## PyQt5 Image Organization, GL Effects, & AI Prep Toolkit

This repo contains a set of different stand-alone tools to organize, label, and apply image effects in aid of training material preperation and the training process for AI Models, Textural Inversion, and Hyper Networks.

Along with general aid for image viewing, modifications, and other tools I've needed in my day to day in texturing pipelines.

### What AI access is there within pxlDataManager?
Once setting a source folder and regressively sourcing all folders & images within the source folder,
<br>You'll have all found images accessible within the `Project` window

The available AI's you may run on any & all found images -
<br>`Resnet` & `Torch` face finding, with face alignment, from `GFPGAN`
<br>`Clip Interrogator` for `BLIP`'s Image2Prompt, with easy editing and saving of image & prompt `.jpg`/`.png` + `.txt` pairs.
<br>*( For `AUTOMATIC1111`'s Textural Inversion and/or HyperNet training )*
<br>`ControlNet`'s `Depth`, `Normal`, and `OpenPose` generation; as `canny`, `mlsd`, & `hed` AI outputs fail to meet my level of acceptable edge finding.
<br>  Do note, all `ControlNet` generations are sourced into `pxlDataManager` allowing for interactive adjustment and correction for `ControlNet` usage in existing AI pipelines.  As its outputs are quite limited in accuracy, `pxlDataManager` will inject your alterations where needed, when needed.
<br>*(With plans for further training of `ControlNet`'s existing models based on your custom alterations)*

Final implementation, *currently not added*, is to add ProcStack's altered StableDiffusion directly into `pxlDataManager` itself.
<br>Randomized prompts per image per iteration, more organized outputs, better output names, and optional ranking for a personal "expected output" AI for future input prompts.
<br>For now, custom implementations are not being added to `pxlDataManager` as its out-of-date by a few months. I'll be modularizing my alterations for an agnostic approach to AI generations.
<br>*(Any on-the-fly repository pulls will be added soon, most likely from a ProcStack branch of the core StableDiffusion repo)*

### What's In pxlDataManager?
*(All scripts have stand-alone PyQt5 versions, works-in-progress though.)*

`pxlDataManager.py` - **MAIN**; Primary Image Organization Manager; Import folder hierarchies of images for easy viewing, including all below image and file tools. While also organizing the outputs from all the scripts below in `./Projects/PROJECT_NAME`

`ControlNetGenerator.py` - **WIP** ControlNet Preprocessors; Generate and alter ControlNet data prior to AI usage.

`ViewportGL.py` - **WIP** PyOpenGL scripts for easy image cropping, interaction, and visual effects.  

`FaceFinder.py` - Find, Isolate, and Align faces in provided images. Based on `GFPGAN`

`FileIngester.py` - Load all found files within directories for adding arbitrary data.  This creates JSON dictionary files with any custom user data saved.  This extends the limitations of image META data, but only within the `FileIngester.py` / `pxlDataManager.py` pipelines.

`ImageToPrompt.py` - Generate a Prompt from a provided Image. Currently only using BLIP.  Based on `clip-interrogator`

`TrainingLabelGenerator.py` - Easy file organizations and text editor for Prompt'ed images for AI training.  Will export Image + Text file pairs for easy injestion for Textural Inversion and HyperNet training.


#### Future ControlNet Altered Features
I have plans for `Frame-to-Frame Pixel Velocity` & `Pixel Rest Position` to be added into `ControlNet` injection locations.
<br>Being that, Gif & Video will have accurate frame-to-frame tweening within AI generation. Smooth & accurate AI generation, regardless of input prompt.

This will require Gif & Video ingestion in `pxlDataManager`
<br>As with everything else in `pxlDataManager`, will live in a pre-process environment.


There is also plans for continued training of `ControlNet` models from your custom alterations of outputted `Depth`, `Normal`, and `OpenPose` generations.
<br>This will likely come sooner than the other above listed Future Features
<br>*(Futher `ControlNet` model training will be an optional use of resources, hit a button to train)*

Outside of direct influence, I'll be adding a 3d `OpenPose` posing interface.
<br>Being a 3d representation of `Depth` + `Normal` + `OpenPose` + `pxlDataManager` Segmentation to easily alter poses in real-time prior to Prompt2Image AI generation.
<br>Inverse Kinematics (grab a wrist & move an arm), `Depth` rectrification, and `Normal` clean up from user adjustments.
<br>*(Normal fixes sourced from pxlDataManager Segmentation and 3d OpenPose adjustments)*

*Do realize*, this will take quite a bit of time to implement. 


### Note from the developer
*(Nod to the current landscape)*
<br>This repo was created with the intention to help train personal AI models in low vram environments; with the use of Microsoft's `DeepSpeed`
<br>All this outside the reliance of internet scrapped images currently used in AI models.

I have no ill will toward AI researcher's scraping the internet for training material. However, as a former feature film technical director & *still* digital creator, I fully understand the distain from those of whom don't want their hard work sourced as AI training material.
<br>While I'm an open-source friendly bugger, I don't care as much for the 20+ years worth of my own work...
<br>**BUT**, that means I'm taking the side of my friends & co-workers before my own selfish desires.
<br>*Live and let Live*

I'd like to imagine, while you have access to the `pxlDataManager` toolkit, you'll make forthright judgement calls for the betterment of AI as a whole.

<hr>

File organization & managment for training purposes may get into the 10's-100's of thousands.  Yeilding the need for this toolkit.
<br> Easy indexing, `Project`-ifying of source material, and quick image alterations in lieu of running AI generations.

Since there are many popular AI systems currently in existance, my aim is to cater to their pipelines.  Thus Textural Inversion and HyperNet training tool outputs organized for AUTOMATIC1111 WebUI.
<br>Pre-processed ControlNet outputs with direct injections into existing neural networks.  Being, you can adjust your ControlNet input images before running any model generations.

All ControlNet scripts being added currently are designed to be a pre-process system, prior to using any AI toolkit which utilizes ControlNet in their pipeline.  Such as `sd-webui-controlnet` for `AUTOMATIC1111`'s webui project.
<br>I'll add any branches or requirements for any A1111 webui extension to this repo itself.
<br>Mostly for retaining the breadcrumb trail of required repos for functionality of those extention scripts.
<br>*(To be added soon)*

#### Notes of Warning
#### As of Feb. 21st, 2023 -
**These tools were built on Python 3.10.6, PyQt5 5.15.9, Torch 1.13.1+cu117**
<br>**Do NOT pip install `XX_requirements.txt` as I'm still figuring out the workflow for required repositories and python modules.**

**These scripts were written on Windows, with SOME potential OS issues mitigated, some...**
<br>**Testing will be needed on Linux / MacOS.  But I don't have a Linux machine strong enough to test these tools.**
