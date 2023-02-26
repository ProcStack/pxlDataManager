# pxlDataManager v0.0.2
## PyQt5 Image Organization, GL Effects, & AI Prep Toolkit

This repo contains a set of different integrated *(with stand-alone support)* tools to organize, label, and apply image tweeks/filters.
<br>&nbsp;&nbsp;In attempt to aid handling training material, preperation, and the training process for AI Models, Textural Inversion, and Hyper Networks.

Along with general image viewing, modification, & other file tools I've needed in my day to day in computer graphics texturing pipelines.
<br/>
<br/>
<hr/>

## Index --
&nbsp;&nbsp;&nbsp;&nbsp; **¤** &nbsp;&nbsp;[What AIs can be ran in pxlDataManager?](#what-ais-can-be-ran-in-pxldatamanager)
<br/>&nbsp;&nbsp;&nbsp;&nbsp; **¤** &nbsp;&nbsp;[What's in pxlDataManager?](#whats-in-pxldatamanager)
<br/>&nbsp;&nbsp;&nbsp;&nbsp; **¤** &nbsp;&nbsp;[Future ControlNet Features](#future-controlnet-features)
<br/>&nbsp;&nbsp;&nbsp;&nbsp; **¤** &nbsp;&nbsp;[Notes from the Developer](#notes-from-the-developer)
<br/>&nbsp;&nbsp;&nbsp;&nbsp; **¤** &nbsp;&nbsp;[Notes of Warning ](#notes-of-warning)
<br/>
<hr/>
<br/>

## What AIs Can Be Ran In pxlDataManager?
Once setting a source folder and regressively sourcing all folders & images within the source folder,
<br>You'll have all found images accessible within the `Project` window

The available AI's you may run on any & all found images -
 - `Facexlib` & `Resnet-50` for face finding in provided image paths, adapted from `GFPGAN`
   - Found faces are both aligned & left unaligned then saved to disk
   - With found face's bounding boxes in the image provided back
 - `Clip Interrogator` for `BLIP`'s Image2Prompt
   - Provide an image path & return the image's 'prompt'
   - For easy editing and saving of image & prompt `.jpg`/`.png` + `.txt` pairs.
   - *( For `AUTOMATIC1111`'s Textural Inversion and/or HyperNet training )*
 - `ControlNet`'s `Depth`, `Normal`, and `OpenPose` generation;
   - The `canny`, `mlsd`, & `hed` AI outputs fail to meet my level of acceptable edge finding.
   - ***Do note***, all `ControlNet` generations are sourced into `pxlDataManager` allowing for interactive adjustment and correction for `ControlNet` usage in existing AI pipelines.  As it's outputs are limited in accuracy, `pxlDataManager` will inject your alterations when needed.
   - *(With plans for further training of `ControlNet`'s existing models based on your alterations)*

Final implementation, *currently not added*, is to add ProcStack's altered StableDiffusion directly into `pxlDataManager` itself.
<br>&nbsp;&nbsp;Randomized prompts per image per iteration,
<br>&nbsp;&nbsp;Better organization of outputs,
<br>&nbsp;&nbsp;Clean output names,
<br>&nbsp;&nbsp;And optional ranking of a personal "expected output" AI for future input prompts.

For now, custom implementations are not being added to `pxlDataManager` as its out-of-date by a few months.
<br>&nbsp;&nbsp;I'll be modularizing my alterations for an agnostic approach to AI generations.
<br>&nbsp;&nbsp;*(Any on-the-fly repository pulls will be added soon, most likely from a ProcStack branch of the core StableDiffusion repo)*
<br/>
<br/>

## What's In pxlDataManager?
*(All scripts have stand-alone PyQt5 versions, works-in-progress though.)*

 - `pxlDataManager.py` <br> **MAIN**; Primary Image Organization Manager; Import folder hierarchies of images for easy viewing, including all below image and file tools. While also organizing the outputs from all the scripts below in `./Projects/PROJECT_NAME`

 - `utils/ControlNetGenerator.py` <br> **WIP** ControlNet Preprocessors; Generate and alter ControlNet data prior to AI usage.

 - `utils/ViewportGL.py` <br> **WIP** PyOpenGL scripts for easy image cropping, interaction, and visual effects.  

 - `utils/FaceFinder.py` <br> Find, Isolate, and Align faces in provided images. Based on `GFPGAN`

 - `utils/FileIngester.py` <br> Load all found files within directories for adding arbitrary data.  This creates JSON dictionary files with any custom user data saved.  This extends the limitations of image META data, but only within the `FileIngester.py` / `pxlDataManager.py` pipelines.

 - `utils/ImageToPrompt.py` <br> Generate a Prompt from a provided Image. Currently only using BLIP.  Based on `clip-interrogator`

 - `utils/TrainingLabelGenerator.py` <br> Easy file organizations and text editor for Prompt'ed images for AI training.  <br> Will export Image + Text file pairs for easy injestion for Textural Inversion and HyperNet training.
<br/>
<br/>

## Future ControlNet Features
I have plans for `Frame-to-Frame Pixel Velocity` & `Pixel Rest Position` to be added into `ControlNet` injection locations.
<br>&nbsp;&nbsp;Being that, Gif & Video will have accurate frame-to-frame tweening within AI generation.
<br>&nbsp;&nbsp;Smooth & accurate AI generation, regardless of input prompt.

This will require Gif & Video ingestion in `pxlDataManager`
<br>&nbsp;&nbsp;As with everything else in `pxlDataManager`, will live in a pre-process environment.


There is also plans for continued training of `ControlNet` models from your custom alterations.
<br>&nbsp;&nbsp;Rectifying outputted `Depth`, `Normal`, and `OpenPose` generations.
<br>&nbsp;&nbsp;This will likely come sooner than the other above listed Future Features
<br>&nbsp;&nbsp;*(Futher `ControlNet` model training will be an optional use of resources, hit a button to train)*

Outside of direct influence, I'll be adding a 3d `OpenPose` posing interface.
<br>&nbsp;&nbsp;Being a 3d representation of `Depth` + `Normal` + `OpenPose` + `pxlDataManager` Segmentation
<br>&nbsp;&nbsp;To easily alter poses in real-time prior to Prompt2Image AI generation.
<br>&nbsp;&nbsp;Inverse Kinematics (grab a wrist & move an arm), `Depth` rectrification, and `Normal` clean up from user adjustments.
<br>&nbsp;&nbsp;*(Normal fixes sourced from pxlDataManager Segmentation and 3d OpenPose adjustments)*

*Do realize*, this will take quite a bit of time to implement. 
<br/>
<br/>

## Notes from the developer
*(Nod to the current landscape)*
<br>This repo was created with the intention to help train personal AI models in low vram environments; with the use of Microsoft's `DeepSpeed`
<br>&nbsp;&nbsp;All this outside the reliance of internet scrapped images currently used in AI models.

I have no ill will toward AI researcher's scraping the internet for training material.
<br>&nbsp;&nbsp;But, as a former feature film technical director & *still* digital creator,
<br>&nbsp;&nbsp;&nbsp;&nbsp;I fully understand the distain from those of whom which don't want their hard work sourced for AI training material.
<br>Since I'm an open-source friendly bugger,
<br>&nbsp;&nbsp;I don't care as much for my 20+ years of creations...

**However**,
<br>&nbsp;&nbsp;That means I'm taking the side of my friends & co-workers before my own selfish desires.
<br>*<span style="font-size:120%;">&nbsp;&nbsp;&nbsp;&nbsp;Live and let Live</span>*
<p>I'd like to imagine, while you have access to the `pxlDataManager` toolkit,
<br>&nbsp;&nbsp;You'll make forthright judgement calls for the betterment of AI as a whole.</p>
<br/>

File organization & managment for training purposes may get into the 10's-100's of thousands.  Yeilding the need for this toolkit.
<br>&nbsp;&nbsp;Easy indexing, `Project`-ifying of source material, and quick image alterations in lieu of running AI generations.

Since there are many popular AI systems currently in existance, my aim is to cater to their pipelines.
<br>&nbsp;&nbsp;Thus Textural Inversion and HyperNet training tool outputs organized for AUTOMATIC1111 WebUI.
<br>&nbsp;&nbsp;Pre-processed ControlNet outputs with direct injections into existing neural networks.
<br>&nbsp;&nbsp;&nbsp;&nbsp;Being, you can adjust your ControlNet input images before running any model generations.

All ControlNet scripts being added currently are designed to be a pre-process system, prior to using any AI toolkit which utilizes ControlNet in their pipeline.
<br>&nbsp;&nbsp;*Such as `sd-webui-controlnet` for `AUTOMATIC1111`'s webui project*
<br>&nbsp;&nbsp;I'll add any branches or requirements for any A1111 webui extension to this repo itself.
<br>&nbsp;&nbsp;Mostly for retaining the breadcrumb trail of required repos for functionality of those extention scripts.
<br>&nbsp;&nbsp;&nbsp;&nbsp;*(To be added soon)*


## Notes of Warning
***As of Feb. 26th, 2023 -***
<br>These tools were built on Python 3.10.6, PyQt5 5.15.9, Torch 1.13.1+cu117
<br>&nbsp;&nbsp;**Do NOT `pip install XX_requirements.txt`** as I'm still figuring out the workflow for required repositories and python modules.
<br>&nbsp;&nbsp;&nbsp;&nbsp;In the mean time, only install packages under `// Found needed --` in `XX_requirements.txt`

Required AI Models should automatically download into `./models/AI_NAME` & `./weights/AI_NAME`
<br>&nbsp;&nbsp;Please see [./weights/Readme.md](weights/Readme.md) for required harddrive space of AI Model `.pth` files.

These python scripts were written on Windows, with SOME potential OS issues mitigated, some...
<br>&nbsp;&nbsp;Which may be better for cross platform usage anyway, as there is no `glutInit()` on Windows PyOpenGL
<br>&nbsp;&nbsp;&nbsp;&nbsp;*Testing will be needed on Linux / MacOS.  But I don't have a Linux machine strong enough to test these tools.*
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*Pull Requests are welcomed!*
<br/>
<br/>

