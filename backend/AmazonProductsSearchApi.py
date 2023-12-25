from amazon.paapi import AmazonAPI
import os
load_dotenv()

class AmazonProductsSearchApi:
    def __init__(self, region):
        self.amazon = AmazonAPI(os.getenv('AMAZON_PRODUCTS_ACCESS_KEY'), os.getenv('AMAZON_PRODUCTS_SECRET_KEY'), os.getenv('AMAZON_PRODUCTS_ASSOC_TAG'), region)

    def search(self, keywords):
        products = self.amazon.search_products(keywords=keywords)
        results = []
        for product in products:
            item = {
                'title': product.title,
                'url': product.url,
                'image': product.images.large if product.images.large else None,
                'price': product.prices.price.value if product.prices.price else None,
                'currency': product.prices.price.currency if product.prices.price else None
            }
            results.append(item)
        return results
