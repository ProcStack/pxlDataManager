# pxlImageManager v0.0.2
### PyQt5 Image Organization, Effects, & AI Prep Toolkit

This repo contains a set of different stand-alone tools to organize, label, and apply image effects to aid in the preperation and training process of AI Models, Textural Inversion, and Hyper Networks.  Along with general aid for image viewing, modifications, and other tools I've needed from day to day in texturing pipelines.

This was created for the intention to help train personal AI models, outside of the internet scrapped images currently used in AI models.

Organizing and managing images for training purposes gets into the 10's-100's of thousands of training material.  So this set of tools came into existence.

But since there are many popular AI systems that currently exist, my aim is to cater to their pipelines.  Thus Textural Inversion and HyperNet training tool outputs organized for AUTOMATIC1111 WebUI.

All ControlNet scripts being added currently are designed to be a pre-process system, prior to using any AI toolkit which utilizes ControlNet in their pipeline.  Such as `sd-webui-controlnet` for `AUTOMATIC1111`'s webui project.
<br>I'll add any branches or requirements for any A1111 webui extension to this repo itself.
<br>Mostly for retaining the breadcrumb trail of required repos for functionality of those extention scripts.
<br>(To be added soon)

## What's In pxlImageManager?
*(All scripts have stand-alone PyQt5 versions, works-in-progress though.)*

`pxlImageManager.py` - **MAIN**; Primary Image Organization Manager; Import folder hierarchies of images for easy viewing, including all below image and file tools. While also organizing the outputs from all the scripts below in `./Projects/PROJECT_NAME`

`ControlNetGenerator.py` - **WIP** ControlNet Preprocessors; Generate and alter ControlNet data prior to AI usage.

`EffectorGL.py` - **WIP** PyOpenGL scripts for easy image cropping, interaction, and visual effects.  

`FaceFinder.py` - Find, Isolate, and Align faces in provided images. Based on `GFPGAN`

`FileIngester.py` - Load all found files within directories for adding arbitrary data.  This creates JSON dictionary files with any custom user data saved.  This extends the limitations of image META data, but only within the `FileIngester.py` / `pxlImageManager.py` pipelines.

`ImageToPrompt.py` - Generate a Prompt from a provided Image. Currently only using BLIP.  Based on `clip-interrogator`

`TrainingLabelGenerator.py` - Easy file organizations and text editor for Prompt'ed images for AI training.  Will export Image + Text file pairs for easy injestion for Textural Inversion and HyperNet training.



### Note of Warning
#### As of Feb. 21st, 2023 -
**These tools were built on Python 3.10.6, PyQt5 5.15.9, Torch 1.13.1+cu117**
<br>**Do NOT pip install `XX_requirements.txt` as I'm still figuring out the workflow for required repositories and python modules.**

**These scripts were written on Windows, with SOME potential OS issues mitigated, some...**
<br>**Testing will be needed on Linux / MacOS.  But I don't have a Linux machine strong enough to test these tools.**
