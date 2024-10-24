import requests
import base64
from typing import List, Dict, Any

class DataForSEOTool:
    def __init__(self, api_login: str, api_password: str):
        auth = f"{api_login}:{api_password}"
        self.headers = {
            'Authorization': 'Basic ' + base64.b64encode(auth.encode()).decode(),
            'Content-Type': 'application/json'
        }

    def search_google_shopping(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        post_data = [{
            "keyword": query,
            "location_code": 2840,  # USA
            "language_code": "en",
            "depth": max_results
        }]
        response = requests.post("https://api.dataforseo.com/v3/merchant/", 
                                 headers=self.headers, 
                                 json=post_data)
        return self._parse_google_shopping_results(response.json())

    def search_amazon(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        post_data = [{
            "keyword": query,
            "location_code": 2840,  # USA
            "language_code": "en",
            "depth": max_results
        }]
        response = requests.post("https://api.dataforseo.com/v3/merchant/", 
                                 headers=self.headers, 
                                 json=post_data)
        return self._parse_amazon_results(response.json())

    def _parse_google_shopping_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        if response.get('status_code') == 20000:
            for task in response.get('tasks', []):
                for item in task.get('result', []):
                    for product in item.get('items', []):
                        results.append({
                            "name": product.get('title'),
                            "price": product.get('price'),
                            "description": product.get('description'),
                            "link": product.get('product_link'),
                            "retailer": product.get('seller_name')
                        })
        return results

    def _parse_amazon_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        if response.get('status_code') == 20000:
            for task in response.get('tasks', []):
                for item in task.get('result', []):
                    for product in item.get('items', []):
                        results.append({
                            "name": product.get('title'),
                            "price": product.get('price', {}).get('current'),
                            "description": product.get('description'),
                            "link": product.get('url'),
                            "retailer": "Amazon"
                        })
        return results






















# import dataforseo_client
# from typing import List, Dict, Any

# class DataForSEOTool:
#     def __init__(self, api_login: str, api_password: str):
#         self.client = dataforseo_client.RestClient(api_login, api_password)

#     def search_google_shopping(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
#         post_data = [{
#             "keyword": query,
#             "location_code": 2840,  # USA
#             "language_code": "en",
#             "depth": max_results
#         }]
#         response = self.client.post("/v3/shopping/google/organic/live/advanced", post_data)
#         return self._parse_google_shopping_results(response)

#     def search_amazon(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
#         post_data = [{
#             "keyword": query,
#             "location_code": 2840,  # USA
#             "language_code": "en",
#             "depth": max_results
#         }]
#         response = self.client.post("/v3/product_finder/amazon/live/advanced", post_data)
#         return self._parse_amazon_results(response)

#     def _parse_google_shopping_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
#         results = []
#         if response.get('status_code') == 20000:
#             for task in response.get('tasks', []):
#                 for item in task.get('result', []):
#                     for product in item.get('items', []):
#                         results.append({
#                             "name": product.get('title'),
#                             "price": product.get('price'),
#                             "description": product.get('description'),
#                             "link": product.get('product_link'),
#                             "retailer": product.get('seller_name')
#                         })
#         return results

#     def _parse_amazon_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
#         results = []
#         if response.get('status_code') == 20000:
#             for task in response.get('tasks', []):
#                 for item in task.get('result', []):
#                     for product in item.get('items', []):
#                         results.append({
#                             "name": product.get('title'),
#                             "price": product.get('price', {}).get('current'),
#                             "description": product.get('description'),
#                             "link": product.get('url'),
#                             "retailer": "Amazon"
#                         })
#         return results

# # Usage example:
# # dataforseo_tool = DataForSEOTool("your_api_login", "your_api_password")
# # google_results = dataforseo_tool.search_google_shopping("wireless headphones")
# # amazon_results = dataforseo_tool.search_amazon("wireless headphones")