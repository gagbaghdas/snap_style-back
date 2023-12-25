from backend.AmazonProductSearchCustom.AmazonProductsScraper import AmazonProductsScraper
from IPAdapter.IPAdapterProcessor import IPAdapterProcessor
import uuid
import os

class OutfitGenerator:
    def __init__(self):
        self.ipAdapterProcessor = IPAdapterProcessor()
        self.amazon_scrapper = AmazonProductsScraper()


    def generateOutfit(self, user_id, keywords, main_image_url, upper_mask_image_url, lower_mask_image_url):
        upper_keywords = keywords[0]
        upper_result = self.generateOutfitPart(upper_keywords, main_image_url, upper_mask_image_url)
        upper_image = upper_result[0]
        upper_product= upper_result[1]

        image_name = uuid.uuid4().hex[:8]
        upper_file_path = f'images/{user_id}_{image_name}.png'
        upper_image.save(upper_file_path)

        lower_keywords = keywords[1]
        outfit_result = self.generateOutfitPart(lower_keywords, upper_file_path, lower_mask_image_url)
        outfit_image = outfit_result[0]
        lower_product = outfit_result[1]

        image_name = uuid.uuid4().hex[:8]
        final_file_path = f'images/{user_id}_{image_name}.png'
        outfit_image.save(final_file_path)

        try:
            os.remove(upper_file_path)
            print(f"File '{upper_file_path}' has been deleted.")
        except OSError as e:
            print(f"Error: {e.strerror}")

        return image_name, final_file_path, [upper_product, lower_product]
    
    def generateOutfitPart(self, keywords, main_image_url, mask_image_url):
        results = self.amazon_scrapper.search(keywords)
        product = results[0]# random.choice(results)
        control_image_url = product["img_url"]

        result_images = self.ipAdapterProcessor.inPaintingUsingIPAdapter(main_image_url, control_image_url, mask_image_url)
        result_image = result_images[0]
        return result_image, product