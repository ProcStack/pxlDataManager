import os, sys
import traceback
#from collections import namedtuple
from PIL import Image
from repositories.clip_interrogator.clip_interrogator import Config, Interrogator



import torch
import torch.hub
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode



#scriptAbsPath = os.path.abspath(__file__)
#scriptDir = os.path.dirname(scriptAbsPath)

#Category = namedtuple("Category", ["name", "topn", "items"])

class ImageToPrompt():
    def __init__(self, modelRootPath=None, device=None):
        self.runningCuda = torch.cuda.is_available()
        self.runningHalf = not self.runningCuda
        #self.runningHalf = True
        self.deviceType = "cuda" if self.runningCuda else "cpu"
        self.device = torch.device( self.deviceType ) if device is None else device
        self.dtype = None #torch.float16
        #self.dtype = torch.float16
        
        self.clipModel = "ViT-L-14.pt"
        self.imageEvalSize = 384
        self.clip_num_beams = 3
        self.clip_min_length = 10
        self.clip_max_length = 30
        
        self.modelRootPath = modelRootPath
        self.categoryPath = os.path.join(self.modelRootPath, "ClipInterrogator")
        self.loadedCategories = None
        
        self.clip_model = None
        self.blip_model = None
        self.models={}
        
        self.models['CLIP']={}
        self.models['CLIP']['name']='ViT-L/14'
        self.models['CLIP']['path']=os.path.join(self.modelRootPath, self.clipModel)
        self.models['CLIP']['keepInMemory']=True
        
        self.models['BLIP']={}
        self.models['BLIP']['path']=os.path.join(self.modelRootPath, "BLIP", "model_base_caption_capfilt_large.pth")
        self.models['BLIP']['config']=os.path.join(self.modelRootPath, "BLIP", "med_config.json")
        self.models['BLIP']['keepInMemory']=True
        
        self.promptOutputs={}
        self.boot()
    """
    def categories(self):
        #if not os.path.exists(self.categoryPath):
        #    download_default_clip_interrogate_categories(self.categoryPath)

        if self.loadedCategories is not None:
           return self.loadedCategories

        self.loadedCategories = []

        if os.path.exists(self.categoryPath):
            #self.skip_categories = shared.opts.interrogate_clip_skip_categories
            category_types = []
            #for filename in Path(self.content_dir).glob('*.txt'):
            #    category_types.append(filename.stem)
            #    #if filename.stem in self.skip_categories:
            #    #    continue
            #    m = re_topn.search(filename.stem)
            #    topn = 1 if m is None else int(m.group(1))
            topn = 1
            categoryList=os.listdir(self.categoryPath)
            for curList in categoryList:
                filename = os.path.join(self.categoryPath,curList)
                with open(filename, "r", encoding="utf8") as file:
                    lines = [x.strip() for x in file.readlines()]
            
                self.loadedCategories.append(Category(name=curList, topn=topn, items=lines))

        return self.loadedCategories
    """
    def boot(self):
        if self.blip_model is None:
            self.blip_model = self.load_blip_model()
            if False and not self.runningHalf and not self.device:
                self.blip_model = self.blip_model.half()

        self.blip_model = self.blip_model.to( self.device )

        """
        if self.clip_model is None:
            self.clip_model, self.clip_preprocess = self.loadClipModel()
            if False and not self.runningHalf and self.runningCuda:
                self.clip_model = self.clip_model.half()

        self.clip_model = self.clip_model.to( self.device )
        self.dtype = next(self.clip_model.parameters()).dtype
        """
    def shutdown(self):
        self.send_clip_to_ram()
        self.send_blip_to_ram()

        self.dumpTorchCache()
    def dumpTorchCache(self):
        #print( self.device )
        if torch.cuda.is_available():
            with torch.cuda.device( self.device ):
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
    def loadClipModel(self):
        import clip

        if self.runningCuda:
            model, preprocess = clip.load(self.models['CLIP']['name'], download_root=self.modelRootPath)
        else:
            model, preprocess = clip.load(self.models['CLIP']['name'], device="cpu", download_root=self.modelRootPath)

        model.eval()
        model = model.to( self.device )

        return model, preprocess
        
    def create_fake_fairscale(self):
        class FakeFairscale:
            def checkpoint_wrapper(self):
                pass;
        sys.modules["fairscale.nn.checkpoint.checkpoint_activations"] = FakeFairscale
    
    def load_blip_model(self):
        self.create_fake_fairscale()
        import repositories.BLIP.models.blip as BLIP

        """
        files = modelloader.load_models(
            model_path=self.models['BLIP'],
            model_url='https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_base_caption_capfilt_large.pth',
            ext_filter=[".pth"],
            download_name='model_base_caption_capfilt_large.pth',
        )
        """
        blipPath = self.models['BLIP']['path']
        blipModel = BLIP.blip_decoder(
            pretrained=self.models['BLIP']['path'],
            image_size=self.imageEvalSize,
            vit='base',
            med_config=self.models['BLIP']['config']
        )
        blipModel.eval()

        return blipModel
        
    def send_clip_to_ram(self):
        if not self.models['CLIP']['keepInMemory'] :
            if self.clip_model is not None:
                self.clip_model = self.clip_model.to( torch.device("cpu") )

    def send_blip_to_ram(self):
        if not self.models['BLIP']['keepInMemory'] :
            if self.blip_model is not None:
                self.blip_model = self.blip_model.to( torch.device("cpu") )

    def generate_caption(self, pilImage):
        gpu_image = transforms.Compose([
            transforms.Resize((self.imageEvalSize, self.imageEvalSize), interpolation=InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        ])(pilImage).unsqueeze(0).to(self.device)
        #.type(self.dtype)
        with torch.no_grad():
            caption = self.blip_model.generate(gpu_image, sample=False, num_beams=self.clip_num_beams, min_length=self.clip_min_length, max_length=self.clip_max_length)
        #print( caption )
        return caption[0]

    def interrogate(self, curImage):
        if type(curImage) == str:
            curImage = Image.open( curImage ).convert('RGB')
        res = ""
        try:
            #if shared.cmd_opts.lowvram or shared.cmd_opts.medvram:
            #    lowvram.send_everything_to_cpu()
            #    self.dumpTorchCache()

            self.boot()

            caption = self.generate_caption(curImage)
            self.send_blip_to_ram()
            self.dumpTorchCache()

            res = caption
        except Exception:
            print("Error interrogating", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            res += "<error>"

        self.shutdown()
        return res


#modelsDir = os.path.join( scriptDir, "weights" )
#imgPath = os.path.join( scriptDir, "Aria-Amor_twistys_2534_08.jpg" )


#ITP = ImageToPrompt( modelsDir )
#foundPrompt = ITP.interrogate( imgPath )
#print( foundPrompt )