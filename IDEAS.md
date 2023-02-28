# pxlDataManager Ideas & Research


These are more of rambling; mental vomit. They may be incorrect, but ask pre-schooler to explain Algebra, you'll get some interesting unbiased ideas.  While most likely wrong, thought provoking never-the-less.


To note, the ideas in `Future ControlNet Altered Features` in README.md has spawned from step-by-step feedback, swapping data back & forth, then continuing the generations.  Definitely doable, but the brute force *(and slow)* method.  `Extending ControlNet` below is exploration into shifting the GPU-CPU-GPU swapping onto GPU alone.


### Extending ControlNet
I still need to explore more of the exact injection location and method of injection for ControlNet.  But if I to implement something like ControlNet on my own, it would be at the "input noise" generation prior to sending off to the GPU.  Along with corrective steps to retain the source input to guide the AI's generation.
<br>
<br>
ControlNets ussually inject in the mid of the network, bypassing initial steps of the AI itself.  Sourcing from its own model as the initial source.

Should set aspects of a source image be adjusted; Edge Detection, Depth, Skeletal Poses.  The initial environment for the AI could already be defined, acting as a guide instead of noise.

With this, Frame-to-Frame tracking of pixel data, A-B Deltas, could be blended into the AI's source material to guide the "noise" filtering into the given prompt.
<br>This would lead to overly sharp details, but makes me wonder how interactive step-by-step of generations can be tweaked.  Like blending in the "control" from a 3d noise [x,y] noise with [z] being a multiplier of how much the "control" is blended into the current AI's step.
<br>That the blending noise randomizes per generation step, to not hold the AI strictly to the "control", allowing for less sharp outputs with guided generation.
<br>
<br>
Should this be doable, pixel "rest positions" could allow for smearing or dynamic shifting of the denoising generation per step.  Like with the Frame-to-Frame position deltas, Rest Positions could use the "control" to shift back to the original positions along the duration of steps in the generation.

<br>
<br>

The forseeable issues with the above idea is the latency of swapping GPU data/renders back to CPU for processing.
<br>Thinking, maybe there could be a use of pre-compiled shaders swapping buffers and FBO render between AI steps mid-generation.  Then blitting the shaders output's fbo texture back into the AI's network to continue it's 'control', guiding the AI's generation.
<br>&nbsp;&nbsp;Perhaps how LoRA adds its layers into the Stable Diffusion training process
<br>&nbsp;&nbsp;&nbsp;&nbsp;Guess I'll need to look into how LoRA works/injects at a network level

<br>
<br>

But hey, per step, animated ControlNet influences.


### Prompt Generator
I've been working on a prompt ranking & input prompt analyzer for my custom Stable Diffusion script.
<br>&nbsp;&nbsp;Storing the randomly generated prompt per generation per iteration in a JSON file
<br>&nbsp;&nbsp;&nbsp;&nbsp;Each prompt entry also stores user ranking in a number of catagories
<br>&nbsp;&nbsp;This data is fed into a PyTorch network for training a custom 'Personal Preference' ai model to help guide your future prompt creations
<br>&nbsp;&nbsp;&nbsp;&nbsp;BUT I had no interface for interactive updates of ranking catagories or running the 'Personal Preference' training itself.
<br>
<br>Now with pxlDataManager, BLIP outputs and SD generation opinions can easily be trained on and used
<br>
<br>Would be cool to set up a S3 & Lambda AWS system for people to upload their prompt opinions to help gather more 'Prompt Opinions' data and allow for a 'Prompt Opinion' extension for A1111 WebUI
<br>&nbsp;&nbsp;*( Opt-in only, certainly )*
