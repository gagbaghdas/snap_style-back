import torch
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipelineLegacy, DDIMScheduler, AutoencoderKL
from PIL import Image
from ip_adapter import IPAdapter
import os

base_model_path = "runwayml/stable-diffusion-v1-5"
vae_model_path = "stabilityai/sd-vae-ft-mse"
image_encoder_path = "IP-Adapter/models/image_encoder/"
ip_ckpt = "IP-Adapter/models/ip-adapter_sd15.bin"
device = "cpu"

def image_grid(imgs, rows, cols):
    assert len(imgs) == rows*cols

    w, h = imgs[0].size
    grid = Image.new('RGB', size=(cols*w, rows*h))
    grid_w, grid_h = grid.size
    
    for i, img in enumerate(imgs):
        grid.paste(img, box=(i%cols*w, i//cols*h))
    return grid

noise_scheduler = DDIMScheduler(
    num_train_timesteps=1000,
    beta_start=0.00085,
    beta_end=0.012,
    beta_schedule="scaled_linear",
    clip_sample=False,
    set_alpha_to_one=False,
    steps_offset=1,
)
vae = AutoencoderKL.from_pretrained(vae_model_path).to(dtype=torch.float32)

### Image Variations ###
pipe = StableDiffusionPipeline.from_pretrained(
    base_model_path,
    torch_dtype=torch.float32,
    scheduler=noise_scheduler,
    vae=vae,
    feature_extractor=None,
    safety_checker=None
)

# image = Image.open("IP-Adapter/assets/images/woman.png")
# image.resize((256, 256))
# image.show()

ip_model = IPAdapter(pipe, image_encoder_path, ip_ckpt, device)
# images = ip_model.generate(pil_image=image, num_samples=4, num_inference_steps=50, seed=42)
# grid = image_grid(images, 1, 4)
# grid.show()
### Image Variations ###

### Image to Image ###
# del pipe, ip_model
# torch.cuda.empty_cache()
# pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
#     base_model_path,
#     torch_dtype=torch.float32,
#     scheduler=noise_scheduler,
#     vae=vae,
#     feature_extractor=None,
#     safety_checker=None
# )

# image = Image.open("IP-Adapter/assets/images/river.png")
# image.show()
# g_image = Image.open("IP-Adapter/assets/images/vermeer.jpg")
# g_image.show()
# image_grid([image.resize((256, 256)), g_image.resize((256, 256))], 1, 2)

# ip_model = IPAdapter(pipe, image_encoder_path, ip_ckpt, device)

# images = ip_model.generate(pil_image=image, num_samples=4, num_inference_steps=50, seed=42, image=g_image, strength=0.6)
# grid = image_grid(images, 1, 4)
# grid.show()
### Image to Image ###

### Inpainting ###
del pipe, ip_model
torch.cuda.empty_cache()
pipe = StableDiffusionInpaintPipelineLegacy.from_pretrained(
    base_model_path,
    torch_dtype=torch.float32,
    scheduler=noise_scheduler,
    vae=vae,
    feature_extractor=None,
    safety_checker=None
)

image = Image.open("IP-Adapter/assets/images/my_images/pants.png")
# image.resize((256, 256))
if image.mode != 'RGB':
    image = image.convert('RGB')
image.show()

masked_image = Image.open("IP-Adapter/assets/images/my_images/initial_image.png").resize((512, 768))
masked_image.show()

mask = Image.open("IP-Adapter/assets/images/my_images/pants_mask.png").resize((512, 768))
mask.show()

image_grid([masked_image.resize((256, 384)), mask.resize((256, 384))], 1, 2)

ip_model = IPAdapter(pipe, image_encoder_path, ip_ckpt, device)

images = ip_model.generate(pil_image=image, num_samples=1, num_inference_steps=30,
                           seed=-1, image=masked_image, mask_image=mask, strength=0.7, )
grid = image_grid(images, 1, 4)
grid.show()
### Inpainting ###
