
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- Face Isolation & Aligner Modules -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

import cv2
import os
import torch
from basicsr.utils import img2tensor, tensor2img, imwrite
from facexlib.utils.face_restoration_helper import FaceRestoreHelper








class FaceFinder():
    """
        Face Finder & Aligner Class
        
        Sourced from Tencent GFPGAN for Face Helper tooling only.
        All Python code has been heavily modified to specific Image Labeler needs.
        
    """

    def __init__(self, upscale=1, output="", device=None):
        self.upscale = upscale
        self.output = output
        
        # initialize model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if device is None else device
                
        # initialize face helper
        self.faceHelper = FaceRestoreHelper(
            upscale,
            face_size=512,
            crop_ratio=(1, 1),
            det_model='retinaface_resnet50',
            save_ext='png',
            use_parse=True,
            device=self.device,
            # TODO : Fix this nested folder thing
            model_rootpath='utils/gfpgan/weights')
        
    def input(self,imgPath):
    
        img_name = os.path.basename(imgPath)
        print(f'Processing {img_name} ...')
        basename, ext = os.path.splitext(img_name)
        inputImg = cv2.imread(imgPath, cv2.IMREAD_COLOR)
        
        saveUnalignedCropPath = os.path.join(self.output, 'cropped_faces', f'{basename}_unalign.png')
        croppedFaces, detFaces = self.find(inputImg,saveUnalignedCropPath)
        croppedFacePaths=[]
        for idx, curCroppedFace in enumerate(croppedFaces):
            save_crop_path = os.path.join(self.output, 'cropped_faces', f'{basename}_{idx:02d}.png')
            croppedFacePaths.append(save_crop_path)
            print("Outputting to - ",save_crop_path)
            imwrite(curCroppedFace, save_crop_path)
        return (detFaces,croppedFacePaths)

    @torch.no_grad()
    def find(self, img, unalignCropPath):
        self.faceHelper.clean_all()

        has_aligned = False
        paste_back = True
        if has_aligned:  # the inputs are already aligned
            img = cv2.resize(img, (512, 512))
            self.faceHelper.cropped_faces = [img]
        else:
            self.faceHelper.read_image(img)
            # get face landmarks for each face
            self.faceHelper.get_face_landmarks_5(only_center_face=False, eye_dist_threshold=5)
            # eye_dist_threshold=5: skip faces whose eye distance is smaller than 5 pixels
            # TODO: even with eye_dist_threshold, it will still introduce wrong detections and restorations.
            # align and warp each face
            self.faceHelper.align_warp_face()

        print( self.faceHelper.det_faces )
        
        """
        for idx, landmark in enumerate(self.faceHelper.all_landmarks_5):
            affine_matrix = cv2.estimateAffinePartial2D(landmark, self.faceHelper.face_template, method=cv2.LMEDS)[0]
            affine_matrix[0][0]=0
            print(affine_matrix)
            border_mode = cv2.BORDER_CONSTANT
            cropped_face = cv2.warpAffine(
                self.faceHelper.input_img, affine_matrix, self.faceHelper.face_size, borderMode=border_mode, borderValue=(135, 133, 132))  # gray
            imwrite(cropped_face, unalignCropPath)
        """
        
        return (self.faceHelper.cropped_faces,self.faceHelper.det_faces)
        """
        if not has_aligned and paste_back:
            # upsample the background
            if self.bg_upsampler is not None:
                # Now only support RealESRGAN for upsampling background
                bg_img = self.bg_upsampler.enhance(img, outscale=self.upscale)[0]
            else:
                bg_img = None

            self.faceHelper.get_inverse_affine(None)
            # paste each restored face to the input image
            restored_img = self.faceHelper.paste_faces_to_input_image(upsample_img=bg_img)
            return self.faceHelper.cropped_faces, self.faceHelper.restored_faces, restored_img
        else:
            return self.faceHelper.cropped_faces, self.faceHelper.restored_faces, None
        """
