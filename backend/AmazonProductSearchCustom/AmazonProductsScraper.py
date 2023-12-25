# -*- coding: utf-8 -*-
"""
Module to get and parse the product info on Amazon Search
"""

import re
import time
import uuid
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import json
from .product import Product
import urllib.parse

base_url = "https://www.amazon.com"


class AmazonProductsScraper():
    """Does the requests with the Amazon servers
    """

    def __init__(self):
        """ Init of the scraper
        """
        self.headers = {
            'authority': 'www.amazon.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cookie':'session-id=138-8865251-6049918; i18n-prefs=USD; ubid-main=135-8571418-1315300; aws-ubid-main=826-1122125-1700776; aws-session-id=910-6840076-6823111; aws-analysis-id=910-6840076-6823111; aws-target-data=%7B%22support%22%3A%221%22%7D; AMCVS_7742037254C95E840A4C98A6%40AdobeOrg=1; s_cc=true; aws_lang=en; aws-target-visitor-id=1697522641177-389875.47_0; regStatus=registered; skin=noskin; lwa-context=3e3f363b5de444867ebe7f24935a4ada; x-main="HT3bOXn6AOUsSU1CgNExsc12vWUTJl5XqPM2ZpTOu0q8modKXRrYRp0weK2I?CYX"; at-main=Atza|IwEBIGhdbTK-WpRbKK8zNHR6446q-8DawC-yzyZit3IT4hur2uGxHSh8CvaGMHkPlwLdRm4WAJ1E-pMeRrpmcxsEYegAZJg6eg9qF21MAmPmSAcenxxz6wPjrgqOLw534T7NJ8SbqhcD7d4LSFnRpMpaXquf2FQP0kxgucrwb-Jx0akrBhItiHe1GVVqB86FM1a_3oQRrv053nVE_lkoz1DyfEgSzyd4CoIU2XFQBRGYU70aLA; sess-at-main="uV8B3LW6cPQh+K0TD4QRZAGxlgS8G2kPrWpbbKv0Z/0="; lc-main=en_US; s_vnum=2133417020924%26vn%3D1; s_ppv=33; s_nr=1701417023071-New; s_dslv=1701417023072; aws-mkto-trk=id%3A112-TZM-766%26token%3A_mch-aws.amazon.com-1701693326512-48258; aws-session-id-time=1701859050l; _mkto_trk=id:112-TZM-766&token:_mch-aws.amazon.com-1701693326512-48258; AMCV_7742037254C95E840A4C98A6%40AdobeOrg=1585540135%7CMCIDTS%7C19700%7CMCMID%7C17878210457559841702126440308182032000%7CMCAAMLH-1702625447%7C6%7CMCAAMB-1702625447%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1702027847s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.0; awsc-color-theme=light; awsc-uh-opt-in=; noflush_awsccs_sid=ee580ac52f462883546410d6adcf3c5e58966a3cc6382ebf51254377aeaf260b; aws-userInfo=%7B%22arn%22%3A%22arn%3Aaws%3Aiam%3A%3A722919505331%3Aroot%22%2C%22alias%22%3A%22%22%2C%22username%22%3A%22snapstyle%22%2C%22keybase%22%3A%22%22%2C%22issuer%22%3A%22http%3A%2F%2Fsignin.aws.amazon.com%2Fsignin%22%2C%22signinType%22%3A%22PUBLIC%22%7D; _rails-root_session=RUphMjVOUERDcVJtcnRwZEswWjkyNXkrV2NiQ0h6eVFoVWsyYVFrUUlFandzYUtXZVlIRUhHbE1YUnB0N0FlZkE5V01QN0xLR09xdndQWmk0VE1IUTJxanIrTU9IWEdYS2RiWW5tbTBLUnlMZ01ORU40NXd0WHhnZjdYdDVXSmt3ODIvczFvYnJOV24yaFV1cDJOeFNKTnJ0OEZ0anpUc05meWwwSFdNSHRCUUVjaGpWWitxT0c3ZXh5U2Z3eGNaLS1hSWs5RmtpTlhWekNqSUlrSXd2cVpRPT0%3D--8d03ee1d659c3fa21294e0613fc3a4cb8af7a8ce; s_fid=56ABA38D7D86E8DC-26C6F88B06C05F06; s_sq=amazdiusprod%3D%2526pid%253Dhttps%25253A%25252F%25252Faffiliate-program.amazon.com%25252F%2526oid%253Dhttps%25253A%25252F%25252Faffiliate-program.amazon.com%25252Fsignup%2526ot%253DA%26amazditemplate%3D%2526pid%253Dhttps%25253A%25252F%25252Faffiliate-program.amazon.com%25252F%2526oid%253Dhttps%25253A%25252F%25252Faffiliate-program.amazon.com%25252Fsignup%2526ot%253DA; session-id-time=2082787201l; session-token=zRGErDWqJ0rzc/Z9EsF7e51ddYl53mIColK9HNCTHNKEH/TK3ofdWaLNn1YICiYH6Iz+LPYQcLhkC0Kefk4lOFAZud5yXOZJltqS+Fi37Utf0abc+7FYpsBeMrPFh9WjOyTACB/5ta1PhF//TskJ9fhA2LfUnIE735SOa46pw682ZbledoVFNvCkM71NKU1ZZIqqlFPuFCOuANo5cKZxhbbHDko7CCimnavgvfD3M7DliURgx4qw0PcU43AXW1bYQ9LwWoqarKIusR5LVJNfg5wu5BdCdf+5RHU+HgpyDFc5HiPBGOhbuYNGw6aE7FdTEzikT8xykl+iOrugZ4ZKj70te4DydUpzcW05kIuUCnW+2fqY6YLAwtvO43u2ccTy; csm-hit=tb:s-6VEYJ9PD5QF0FY28CXV3|1703006564994&t:1703006565867&adb:adblk_no; JSESSIONID=A4D6453E0B9BD0FEA32C4AA2413AA147'
        }
        self.proxies = {
            'http': 'http://91.244.66.174:80'
                            }

    def prepare_url(self, search_word):
        """Get the Amazon search URL, based on the keywords passed

        Args:
            search_word (str): word passed by the user to search amazon.com for (eg. smart phones)

        Returns:
            search url: Url where the get request will be passed (it will look something like https://www.amazon.com/s?k=smart+phones)
        """
        search_word = search_word.replace("'", '%27s')
        params = ("/s?k=%s" % (search_word.replace(' ', '+')))

        return urljoin(base_url, params)

    def get_request(self, url):
        """ Places GET request with the proper headers

        Args:
            url (str): Url where the get request will be placed

        Raises:
            requests.exceptions.ConnectionError: Raised when there is no internet connection while placing GET request

            requests.HTTPError: Raised when response stattus code is not 200

        Returns:
            response or None: returns whatever response was sent back by the server or returns None if requests.exceptions.ConnectionError occurs
        """
        try:
            print("GET request placed at: " + url)
            print("proxies: ",self.proxies)
            response = requests.get(url, headers=self.headers,proxies=self.proxies)
            if response.status_code != 200:
                raise requests.HTTPError(
                    f"Error occured, status code:{response.status_code}")
        #  returns None if requests.exceptions.ConnectionError or requests.HTTPError occurs
        except (requests.exceptions.ConnectionError, requests.HTTPError) as e:
            print(f"{e} while connecting to{url}")
            return None

        return response

    def check_page_validity(self, page_content):
        """Check if the page is a valid result page

        Returns:
            valid_page: returns true for valid page and false for invalid page(in accordance with conditions)
        """

        if "We're sorry. The Web address you entered is not a functioning page on our site." in page_content:
            valid_page = False
        elif "Try checking your spelling or use more general terms" in page_content:
            valid_page = False
        elif "Sorry, we just need to make sure you're not a robot." in page_content:
            valid_page = False
        elif "The request could not be satisfied" in page_content:
            valid_page = False
        else:
            valid_page = True
        return valid_page

    def get_page_content(self, search_url):
        """Retrieve the html content at search_url

        Args:
            search_url (str): Url where the get request will be placed

        Raises:
            ValueError: raised if no valid page is found

        Returns:
            response.text or None: returns html response encoded in unicode or returns None if get_requests function or if the page is not valid even after retries
        """

        valid_page = True
        trial = 0
        # if a page does not get a valid response it retries(5 times)
        max_retries = 5
        while (trial < max_retries):

            response = self.get_request(search_url)

            if (not response):
                return None

            valid_page = self.check_page_validity(response.text)

            if valid_page:
                break

            print("No valid page was found, retrying in 3 seconds...")
            time.sleep(3)
            trial += 1

        if not valid_page:
            print(
                "Even after retrying, no valid page was found on this thread, terminating thread...")
            return None

        return response.text

    def get_product_url(self, product):
        """Retrieves and returns product url

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            url: returns full url of product
        """
        regexp = "a-link-normal s-no-outline".replace(' ', '\s+')
        classes = re.compile(regexp)
        product_url = product.find('a', attrs={'class': classes}).get('href')
        return base_url + product_url

    def get_product_asin(self, product):
        """ Retrieves and returns Amazon Standard Identification Number (asin) of a product

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            asin: returns Amazon Standard Identification Number (asin) of a product
        """

        return product.get('data-asin')

    def get_product_title(self, product):
        """Retrieves and returns product title
        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            title: returns product title or empty string if no title is found
        """

        regexp = "a-color-base a-text-normal".replace(' ', '\s+')
        classes = re.compile(regexp)
        try:
            title = product.find('span', attrs={'class': classes})
            return title.text.strip()

        except AttributeError:
            """AttributeError occurs when no title is found and we get back None
            in that case when we try to do title.text it raises AttributeError
            because Nonetype object does not have text attribute"""
            return ''

    def get_product_price(self, product):
        """Retrieves and returns product price
        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            price: returns product price or None if no price is found
        """

        try:
            price = product.find('span', attrs={'class': 'a-offscreen'})
            return float(price.text.strip('$').replace(',', ''))

        except (AttributeError, ValueError):
            """AttributeError occurs when no price is found and we get back None
            in that case when we try to do price.text it raises AttributeError
            because Nonetype object does not have text attribute"""

            """ValueError is raised while converting price.text.strip() into float
            of that value and that value for some reason is not convertible to
            float"""

            return None

    def get_product_image_url(self, product):
        """Retrieves and returns product image url

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            image_url: returns product image url
        """

        image_tag = product.find('img')
        return image_tag.get('src')

    def get_product_rating(self, product):
        """Retrieves and returns product rating

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            rating : returns product rating or returns None if no rating is found
        """

        try:
            rating = re.search(r'(\d.\d) out of 5', str(product))
            return float(rating.group(1))

        except (AttributeError, ValueError):
            """AttributeError occurs when no rating is found and we get back None
            in that case when we try to do rating.text it raises AttributeError
            because Nonetype object does not have text attribute"""

            """ValueError is raised while converting rating.group(1) into float
            of that value and that value for some reason is not convertible to
            float"""

            return None

    def get_product_review_count(self, product):
        """Retrieves and returns number of reviews a product has

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            review count: returns number of reviews a product has or returns None if no reviews are available
        """

        try:
            review_count = product.find(
                'span', attrs={'class': 'a-size-base', 'dir': 'auto'})
            return int(review_count.text.strip().replace(',', ''))

        except (AttributeError, ValueError):
            """AttributeError occurs when no review_count is found and we get back None
            in that case when we try to do review_count.text it raises AttributeError
            because Nonetype object does not have text attribute"""

            """ValueError is raised while converting review_count.text.strip() into
            int of that value and that value for some reason is not convertible to
            int"""

            return None

    def get_product_bestseller_status(self, product):
        """Retrieves and returns if product is best-seller or not

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            bestseller_status: returns if product is best-seller or not
        """

        try:
            bestseller_status = product.find(
                'span', attrs={'class': 'a-badge-text'})
            return bestseller_status.text.strip() == 'Best Seller'

        except AttributeError:
            """AttributeError occurs when no bestseller_status is found and we get back None
            in that case when we try to do bestseller_status.text it raises AttributeError
            because Nonetype object does not have text attribute
            """
            return False

    def get_product_prime_status(self, product):
        """Retrieves and returns if product is supported by Amazon prime

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            prime_status: eturns if product is supported by Amazon prime
        """

        regexp = "a-icon a-icon-prime a-icon-medium".replace(' ', '\s+')
        classes = re.compile(regexp)
        prime_status = product.find('i', attrs={'class': classes})
        return bool(prime_status)

    def get_product_info(self, product):
        """Gathers all the information about a product and 
        packs it all into an object of class Product
        and appends it to list of Product objects

        Args:
            product (str): higher level html tags of a product containing all the information about a product
        """

        product_obj = Product()
        product_obj.url = self.get_product_url(product)
        product_obj.asin = self.get_product_asin(product)
        product_obj.title = self.get_product_title(product)
        product_obj.price = self.get_product_price(product)
        product_obj.img_url = self.get_product_image_url(product)
        product_obj.rating_stars = self.get_product_rating(product)
        product_obj.review_count = self.get_product_review_count(product)
        product_obj.bestseller = self.get_product_bestseller_status(product)
        product_obj.prime = self.get_product_prime_status(product)

        return product_obj

    # def get_page_count(self, page_content):
    #     """Extracts number of pages present while searching for user-specified word

    #     Args:
    #         page_content (str): unicode encoded response

    #     Returns:
    #         page count: returns number of search pages for user-specified word if IndexError is raised then function returns 1
    #     """

    #     soup = BeautifulSoup(page_content, 'html5lib')
    #     try:
    #         pagination = soup.find_all(
    #             'li', attrs={'class': ['a-normal', 'a-disabled', 'a-last']})
    #         return int(pagination[-2].text)
    #     except IndexError:
    #         return 1

    # def prepare_page_list(self, search_url):
    #     """prepares a url for every page and appends it to page_list in accordance with the page count

    #     Args:
    #         search_url (str): url generated by prepare_url function
    #     """

    #     for i in range(1, self.page_count + 1):
    #         self.page_list.append(search_url + '&page=' + str(i))

    def get_products(self, page_content):
        """extracts higher level html tags for each product present while scraping all the pages in page_list

        Args:
            page_content (str): unicode encoded response

        """

        soup = BeautifulSoup(page_content, "html5lib")
        product_list = soup.find_all(
            'div', attrs={'data-component-type': 's-search-result'})
      
        product_obj_list = []
        for product in product_list:
            productIfo = self.get_product_info(product)
            product_obj_list.append(productIfo)
        return product_obj_list

    def get_products_wrapper(self, page_url):
        """wrapper function that gets contents of a given url and gets products from that url

        Args:
            page_url (str): url of one of search pages
        """

        page_content = self.get_page_content(page_url)
        if (not page_content):
            return

        return self.get_products(page_content)

    def generate_output_file(self, product_obj_list):
        """generates json file from list of products found in the whole search
        """

        products_json_list = []
        # generate random file name
        filename = str(uuid.uuid4()) + '.json'
        # every object gets converted into json format
        for obj in product_obj_list:
            products_json_list.append(obj.to_json())

        products_json_list = ','.join(products_json_list)
        json_data = '[' + products_json_list + ']'
        return json.loads(json_data)
        # with open('./' + filename, mode='w') as f:
        #     f.write(json_data)

    def search(self, search_word):
        """Initializies that search and puts together the whole class

        Args:
            search_word (str): user given word to be searched
        """

        search_url = self.prepare_url(search_word)
        page_content = self.get_page_content(search_url)
        if (not page_content):
            return

        # self.page_count = self.get_page_count(page_content)

        product_obj_list = self.get_products(page_content)
        return self.generate_output_file(product_obj_list)
         
        # else:
        #     # if page count is more than 1, then we prepare a page list and start a thread at each page url
        #     self.prepare_page_list(search_url)
        #     # creating threads at each page in page_list
        #     with ThreadPoolExecutor() as executor:
        #         for page in self.page_list:
        #             executor.submit(self.get_products_wrapper, page)

        # generate a json output file
        #return self.generate_output_file()
