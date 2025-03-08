from ebaysdk.finding import Connection as Finding
from dotenv import load_dotenv
import os
load_dotenv()

app_id = ""
config = {
    'domain': 'svcs.ebay.com',  # Production endpoint
    'siteid': 'EBAY-US',
    'warnings': True
}

try:
    api = Finding(appid=app_id, config_file=None, **config)
    response = api.execute('findItemsAdvanced', {'keywords': 'laptop'})
    print(response.dict())
except Exception as e:
    print(f"Error: {str(e)}")
