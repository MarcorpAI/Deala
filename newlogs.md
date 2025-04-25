DEBUG:httpx:load_verify_locations cafile='/home/webkaave/Dev/Deala/venv/lib/python3.12/site-packages/certifi/cacert.pem'
INFO 2025-04-22 23:25:47,507 shop_agent_factory ShopAgent instance created successfully
INFO:delapp.agent.shop_agent_factory:ShopAgent instance created successfully
INFO 2025-04-22 23:25:47,507 agent_core Processing query: 'coffee maker under 100 bucks' for conversation: 58
INFO:delapp.agent.core.agent_core:Processing query: 'coffee maker under 100 bucks' for conversation: 58
DEBUG 2025-04-22 23:25:47,523 utils (0.001) SELECT "delapp_conversation"."id", "delapp_conversation"."user_id", "delapp_conversation"."title", "delapp_conversation"."created_at", "delapp_conversation"."updated_at", "delapp_conversation"."active" FROM "delapp_conversation" WHERE "delapp_conversation"."id" = 58 LIMIT 21; args=(58,); alias=default
DEBUG:django.db.backends:(0.001) SELECT "delapp_conversation"."id", "delapp_conversation"."user_id", "delapp_conversation"."title", "delapp_conversation"."created_at", "delapp_conversation"."updated_at", "delapp_conversation"."active" FROM "delapp_conversation" WHERE "delapp_conversation"."id" = 58 LIMIT 21; args=(58,); alias=default
WARNING 2025-04-22 23:25:47,524 agent_core Failed to load conversation: Conversation not found: 58
WARNING:delapp.agent.core.agent_core:Failed to load conversation: Conversation not found: 58
INFO 2025-04-22 23:25:47,524 agent_core Classified intent as: search
INFO:delapp.agent.core.agent_core:Classified intent as: search
INFO 2025-04-22 23:25:47,524 product_search_tool Executing product search for: coffee maker under 100 bucks with price range: $0-$unlimited
INFO:delapp.agent.tools.product_search_tool:Executing product search for: coffee maker under 100 bucks with price range: $0-$unlimited
INFO 2025-04-22 23:25:47,524 product_search_tool Extracted max price from query: $100.0
INFO:delapp.agent.tools.product_search_tool:Extracted max price from query: $100.0
INFO 2025-04-22 23:25:47,524 searchapi_io Setting max_price: 100.0
INFO:delapp.searchapi_io:Setting max_price: 100.0
INFO 2025-04-22 23:25:47,524 searchapi_io SearchAPI.io async params: {'q': 'coffee maker under 100 bucks', 'engine': 'google_shopping', 'api_key': 'Y8RbP6143GLLWfVo5yX7C3V4', 'num': 10, 'max_price': 100.0}
INFO:delapp.searchapi_io:SearchAPI.io async params: {'q': 'coffee maker under 100 bucks', 'engine': 'google_shopping', 'api_key': 'Y8RbP6143GLLWfVo5yX7C3V4', 'num': 10, 'max_price': 100.0}
INFO 2025-04-22 23:25:47,525 searchapi_io Sending async request to URL: https://www.searchapi.io/api/v1/search
INFO:delapp.searchapi_io:Sending async request to URL: https://www.searchapi.io/api/v1/search
INFO 2025-04-22 23:25:47,525 searchapi_io Making API call #1 for: coffee maker under 100 bucks
INFO:delapp.searchapi_io:Making API call #1 for: coffee maker under 100 bucks
INFO 2025-04-22 23:25:51,675 searchapi_io Received async response with status: 200
INFO:delapp.searchapi_io:Received async response with status: 200
INFO 2025-04-22 23:25:51,860 searchapi_io Async SearchAPI.io shopping_results count: 40
INFO:delapp.searchapi_io:Async SearchAPI.io shopping_results count: 40
INFO 2025-04-22 23:25:51,860 searchapi_io Processing 40 items from SearchAPI.io response
INFO:delapp.searchapi_io:Processing 40 items from SearchAPI.io response
DEBUG 2025-04-22 23:25:51,860 searchapi_io Processing item 1/40
DEBUG:delapp.searchapi_io:Processing item 1/40
DEBUG 2025-04-22 23:25:51,860 searchapi_io Raw price string: '$59.00' for item Beautiful 14-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$59.00' for item Beautiful 14-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,861 searchapi_io Parsed price: 59.0 for item Beautiful 14-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 59.0 for item Beautiful 14-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,861 searchapi_io Processing item 2/40
DEBUG:delapp.searchapi_io:Processing item 2/40
DEBUG 2025-04-22 23:25:51,861 searchapi_io Raw price string: '$29.99' for item Bella Pro 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$29.99' for item Bella Pro 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,861 searchapi_io Parsed price: 29.99 for item Bella Pro 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 29.99 for item Bella Pro 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,862 searchapi_io Processing item 3/40
DEBUG:delapp.searchapi_io:Processing item 3/40
DEBUG 2025-04-22 23:25:51,862 searchapi_io Raw price string: '$79.99' for item Ninja 12-Cup Programmable Coffee Brewer
DEBUG:delapp.searchapi_io:Raw price string: '$79.99' for item Ninja 12-Cup Programmable Coffee Brewer
DEBUG 2025-04-22 23:25:51,862 searchapi_io Parsed price: 79.99 for item Ninja 12-Cup Programmable Coffee Brewer
DEBUG:delapp.searchapi_io:Parsed price: 79.99 for item Ninja 12-Cup Programmable Coffee Brewer
DEBUG 2025-04-22 23:25:51,862 searchapi_io Processing item 4/40
DEBUG:delapp.searchapi_io:Processing item 4/40
DEBUG 2025-04-22 23:25:51,862 searchapi_io Raw price string: '$59.00' for item Ninja 12-Cup Programmable Coffee Maker CE250
DEBUG:delapp.searchapi_io:Raw price string: '$59.00' for item Ninja 12-Cup Programmable Coffee Maker CE250
DEBUG 2025-04-22 23:25:51,862 searchapi_io Parsed price: 59.0 for item Ninja 12-Cup Programmable Coffee Maker CE250
DEBUG:delapp.searchapi_io:Parsed price: 59.0 for item Ninja 12-Cup Programmable Coffee Maker CE250
DEBUG 2025-04-22 23:25:51,862 searchapi_io Processing item 5/40
DEBUG:delapp.searchapi_io:Processing item 5/40
DEBUG 2025-04-22 23:25:51,863 searchapi_io Raw price string: '$68.53' for item Hamilton Beach 12-Cup BrewStation Coffee Maker 47950
DEBUG:delapp.searchapi_io:Raw price string: '$68.53' for item Hamilton Beach 12-Cup BrewStation Coffee Maker 47950
DEBUG 2025-04-22 23:25:51,863 searchapi_io Parsed price: 68.53 for item Hamilton Beach 12-Cup BrewStation Coffee Maker 47950
DEBUG:delapp.searchapi_io:Parsed price: 68.53 for item Hamilton Beach 12-Cup BrewStation Coffee Maker 47950
DEBUG 2025-04-22 23:25:51,863 searchapi_io Processing item 6/40
DEBUG:delapp.searchapi_io:Processing item 6/40
DEBUG 2025-04-22 23:25:51,863 searchapi_io Raw price string: '$78.99' for item Cuisinart 14 Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$78.99' for item Cuisinart 14 Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,863 searchapi_io Parsed price: 78.99 for item Cuisinart 14 Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 78.99 for item Cuisinart 14 Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,863 searchapi_io Processing item 7/40
DEBUG:delapp.searchapi_io:Processing item 7/40
DEBUG 2025-04-22 23:25:51,863 searchapi_io Raw price string: '$69.99' for item Amaste Coffee Maker, 5 Cup Coffee Pot with Three Brewing Modes, Retro Coffee Maker with Glass Carafe & Reusable Coffee Filter, Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$69.99' for item Amaste Coffee Maker, 5 Cup Coffee Pot with Three Brewing Modes, Retro Coffee Maker with Glass Carafe & Reusable Coffee Filter, Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,864 searchapi_io Parsed price: 69.99 for item Amaste Coffee Maker, 5 Cup Coffee Pot with Three Brewing Modes, Retro Coffee Maker with Glass Carafe & Reusable Coffee Filter, Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 69.99 for item Amaste Coffee Maker, 5 Cup Coffee Pot with Three Brewing Modes, Retro Coffee Maker with Glass Carafe & Reusable Coffee Filter, Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,864 searchapi_io Processing item 8/40
DEBUG:delapp.searchapi_io:Processing item 8/40
DEBUG 2025-04-22 23:25:51,864 searchapi_io Raw price string: '$35.00' for item Keurig K Express Essentials Single Serve K Cup Pod Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$35.00' for item Keurig K Express Essentials Single Serve K Cup Pod Coffee Maker
DEBUG 2025-04-22 23:25:51,864 searchapi_io Parsed price: 35.0 for item Keurig K Express Essentials Single Serve K Cup Pod Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 35.0 for item Keurig K Express Essentials Single Serve K Cup Pod Coffee Maker
DEBUG 2025-04-22 23:25:51,864 searchapi_io Processing item 9/40
DEBUG:delapp.searchapi_io:Processing item 9/40
DEBUG 2025-04-22 23:25:51,864 searchapi_io Raw price string: '$69.99' for item Mr. Coffee 12-Cup Programmable Coffee Maker with Rapid Brew System
DEBUG:delapp.searchapi_io:Raw price string: '$69.99' for item Mr. Coffee 12-Cup Programmable Coffee Maker with Rapid Brew System
DEBUG 2025-04-22 23:25:51,865 searchapi_io Parsed price: 69.99 for item Mr. Coffee 12-Cup Programmable Coffee Maker with Rapid Brew System
DEBUG:delapp.searchapi_io:Parsed price: 69.99 for item Mr. Coffee 12-Cup Programmable Coffee Maker with Rapid Brew System
DEBUG 2025-04-22 23:25:51,865 searchapi_io Processing item 10/40
DEBUG:delapp.searchapi_io:Processing item 10/40
DEBUG 2025-04-22 23:25:51,865 searchapi_io Raw price string: '$79.99' for item Zojirushi Zutto 5-Cup Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$79.99' for item Zojirushi Zutto 5-Cup Coffee Maker
DEBUG 2025-04-22 23:25:51,865 searchapi_io Parsed price: 79.99 for item Zojirushi Zutto 5-Cup Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 79.99 for item Zojirushi Zutto 5-Cup Coffee Maker
DEBUG 2025-04-22 23:25:51,865 searchapi_io Processing item 11/40
DEBUG:delapp.searchapi_io:Processing item 11/40
DEBUG 2025-04-22 23:25:51,866 searchapi_io Raw price string: '$69.99' for item Nostalgia 12-Cup Retro Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$69.99' for item Nostalgia 12-Cup Retro Coffee Maker
DEBUG 2025-04-22 23:25:51,866 searchapi_io Parsed price: 69.99 for item Nostalgia 12-Cup Retro Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 69.99 for item Nostalgia 12-Cup Retro Coffee Maker
DEBUG 2025-04-22 23:25:51,866 searchapi_io Processing item 12/40
DEBUG:delapp.searchapi_io:Processing item 12/40
DEBUG 2025-04-22 23:25:51,866 searchapi_io Raw price string: '$79.99' for item Haden Heritage 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$79.99' for item Haden Heritage 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,866 searchapi_io Parsed price: 79.99 for item Haden Heritage 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 79.99 for item Haden Heritage 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,866 searchapi_io Processing item 13/40
DEBUG:delapp.searchapi_io:Processing item 13/40
DEBUG 2025-04-22 23:25:51,866 searchapi_io Raw price string: '$64.10' for item Braun PureFlavor Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$64.10' for item Braun PureFlavor Coffee Maker
DEBUG 2025-04-22 23:25:51,867 searchapi_io Parsed price: 64.1 for item Braun PureFlavor Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 64.1 for item Braun PureFlavor Coffee Maker
DEBUG 2025-04-22 23:25:51,867 searchapi_io Processing item 14/40
DEBUG:delapp.searchapi_io:Processing item 14/40
DEBUG 2025-04-22 23:25:51,867 searchapi_io Raw price string: '$79.99' for item Bella VersaBrew 2-in-1 Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$79.99' for item Bella VersaBrew 2-in-1 Coffee Maker
DEBUG 2025-04-22 23:25:51,867 searchapi_io Parsed price: 79.99 for item Bella VersaBrew 2-in-1 Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 79.99 for item Bella VersaBrew 2-in-1 Coffee Maker
DEBUG 2025-04-22 23:25:51,867 searchapi_io Processing item 15/40
DEBUG:delapp.searchapi_io:Processing item 15/40
DEBUG 2025-04-22 23:25:51,867 searchapi_io Raw price string: '$78.99' for item Cuisinart Brew Central 12 Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$78.99' for item Cuisinart Brew Central 12 Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,867 searchapi_io Parsed price: 78.99 for item Cuisinart Brew Central 12 Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 78.99 for item Cuisinart Brew Central 12 Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,868 searchapi_io Processing item 16/40
DEBUG:delapp.searchapi_io:Processing item 16/40
DEBUG 2025-04-22 23:25:51,868 searchapi_io Raw price string: '$63.97' for item Cuisinart 12 Cup Classic Programmable Coffeemaker
DEBUG:delapp.searchapi_io:Raw price string: '$63.97' for item Cuisinart 12 Cup Classic Programmable Coffeemaker
DEBUG 2025-04-22 23:25:51,868 searchapi_io Parsed price: 63.97 for item Cuisinart 12 Cup Classic Programmable Coffeemaker
DEBUG:delapp.searchapi_io:Parsed price: 63.97 for item Cuisinart 12 Cup Classic Programmable Coffeemaker
DEBUG 2025-04-22 23:25:51,869 searchapi_io Processing item 17/40
DEBUG:delapp.searchapi_io:Processing item 17/40
DEBUG 2025-04-22 23:25:51,869 searchapi_io Raw price string: '$76.15' for item Hamilton Beach 2-Way Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$76.15' for item Hamilton Beach 2-Way Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,869 searchapi_io Parsed price: 76.15 for item Hamilton Beach 2-Way Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 76.15 for item Hamilton Beach 2-Way Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,869 searchapi_io Processing item 18/40
DEBUG:delapp.searchapi_io:Processing item 18/40
DEBUG 2025-04-22 23:25:51,869 searchapi_io Raw price string: '$69.00' for item GE 10 Cup Drip Coffee Maker with Single Serve
DEBUG:delapp.searchapi_io:Raw price string: '$69.00' for item GE 10 Cup Drip Coffee Maker with Single Serve
DEBUG 2025-04-22 23:25:51,870 searchapi_io Parsed price: 69.0 for item GE 10 Cup Drip Coffee Maker with Single Serve
DEBUG:delapp.searchapi_io:Parsed price: 69.0 for item GE 10 Cup Drip Coffee Maker with Single Serve
DEBUG 2025-04-22 23:25:51,870 searchapi_io Processing item 19/40
DEBUG:delapp.searchapi_io:Processing item 19/40
DEBUG 2025-04-22 23:25:51,870 searchapi_io Raw price string: '$52.46' for item Krups Simply Brew 10-Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$52.46' for item Krups Simply Brew 10-Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,870 searchapi_io Parsed price: 52.46 for item Krups Simply Brew 10-Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 52.46 for item Krups Simply Brew 10-Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,870 searchapi_io Processing item 20/40
DEBUG:delapp.searchapi_io:Processing item 20/40
DEBUG 2025-04-22 23:25:51,870 searchapi_io Raw price string: '$34.99' for item BLACK+DECKER 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$34.99' for item BLACK+DECKER 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,871 searchapi_io Parsed price: 34.99 for item BLACK+DECKER 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 34.99 for item BLACK+DECKER 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,871 searchapi_io Processing item 21/40
DEBUG:delapp.searchapi_io:Processing item 21/40
DEBUG 2025-04-22 23:25:51,871 searchapi_io Raw price string: '$119.99' for item Hamilton Beach FlexBrew 2-in-1 Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$119.99' for item Hamilton Beach FlexBrew 2-in-1 Coffee Maker
DEBUG 2025-04-22 23:25:51,871 searchapi_io Parsed price: 119.99 for item Hamilton Beach FlexBrew 2-in-1 Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 119.99 for item Hamilton Beach FlexBrew 2-in-1 Coffee Maker
DEBUG 2025-04-22 23:25:51,872 searchapi_io Processing item 22/40
DEBUG:delapp.searchapi_io:Processing item 22/40
DEBUG 2025-04-22 23:25:51,872 searchapi_io Raw price string: '$29.95' for item MUeller HOME Mueller 12-Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$29.95' for item MUeller HOME Mueller 12-Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,872 searchapi_io Parsed price: 29.95 for item MUeller HOME Mueller 12-Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 29.95 for item MUeller HOME Mueller 12-Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,872 searchapi_io Processing item 23/40
DEBUG:delapp.searchapi_io:Processing item 23/40
DEBUG 2025-04-22 23:25:51,872 searchapi_io Raw price string: '$70.00' for item PowerXL Grind and Go Plus Automatic Single-Serve Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$70.00' for item PowerXL Grind and Go Plus Automatic Single-Serve Coffee Maker
DEBUG 2025-04-22 23:25:51,872 searchapi_io Parsed price: 70.0 for item PowerXL Grind and Go Plus Automatic Single-Serve Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 70.0 for item PowerXL Grind and Go Plus Automatic Single-Serve Coffee Maker
DEBUG 2025-04-22 23:25:51,873 searchapi_io Processing item 24/40
DEBUG:delapp.searchapi_io:Processing item 24/40
DEBUG 2025-04-22 23:25:51,873 searchapi_io Raw price string: '$99.99' for item Ninja Pods & Grounds Specialty Single-Serve Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$99.99' for item Ninja Pods & Grounds Specialty Single-Serve Coffee Maker
DEBUG 2025-04-22 23:25:51,873 searchapi_io Parsed price: 99.99 for item Ninja Pods & Grounds Specialty Single-Serve Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 99.99 for item Ninja Pods & Grounds Specialty Single-Serve Coffee Maker
DEBUG 2025-04-22 23:25:51,873 searchapi_io Processing item 25/40
DEBUG:delapp.searchapi_io:Processing item 25/40
DEBUG 2025-04-22 23:25:51,873 searchapi_io Raw price string: '$99.95' for item Cuisinart PerfecTemp 14-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$99.95' for item Cuisinart PerfecTemp 14-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,873 searchapi_io Parsed price: 99.95 for item Cuisinart PerfecTemp 14-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 99.95 for item Cuisinart PerfecTemp 14-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,873 searchapi_io Processing item 26/40
DEBUG:delapp.searchapi_io:Processing item 26/40
DEBUG 2025-04-22 23:25:51,873 searchapi_io Raw price string: '$99.99' for item Ninja 14 Cup Programmable Coffee Maker XL PRO
DEBUG:delapp.searchapi_io:Raw price string: '$99.99' for item Ninja 14 Cup Programmable Coffee Maker XL PRO
DEBUG 2025-04-22 23:25:51,874 searchapi_io Parsed price: 99.99 for item Ninja 14 Cup Programmable Coffee Maker XL PRO
DEBUG:delapp.searchapi_io:Parsed price: 99.99 for item Ninja 14 Cup Programmable Coffee Maker XL PRO
DEBUG 2025-04-22 23:25:51,874 searchapi_io Processing item 27/40
DEBUG:delapp.searchapi_io:Processing item 27/40
DEBUG 2025-04-22 23:25:51,874 searchapi_io Raw price string: '$19.99' for item Mr. Coffee 5-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$19.99' for item Mr. Coffee 5-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,874 searchapi_io Parsed price: 19.99 for item Mr. Coffee 5-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 19.99 for item Mr. Coffee 5-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,874 searchapi_io Processing item 28/40
DEBUG:delapp.searchapi_io:Processing item 28/40
DEBUG 2025-04-22 23:25:51,874 searchapi_io Raw price string: '$65.99' for item Kenmore Aroma Control 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$65.99' for item Kenmore Aroma Control 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,874 searchapi_io Parsed price: 65.99 for item Kenmore Aroma Control 12-Cup Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 65.99 for item Kenmore Aroma Control 12-Cup Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,875 searchapi_io Processing item 29/40
DEBUG:delapp.searchapi_io:Processing item 29/40
DEBUG 2025-04-22 23:25:51,875 searchapi_io Raw price string: '$79.99' for item Gevi 12 Cup Programmable Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$79.99' for item Gevi 12 Cup Programmable Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,875 searchapi_io Parsed price: 79.99 for item Gevi 12 Cup Programmable Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 79.99 for item Gevi 12 Cup Programmable Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,875 searchapi_io Processing item 30/40
DEBUG:delapp.searchapi_io:Processing item 30/40
DEBUG 2025-04-22 23:25:51,875 searchapi_io Raw price string: '$99.95' for item Braun BrewSense 12-Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$99.95' for item Braun BrewSense 12-Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,875 searchapi_io Parsed price: 99.95 for item Braun BrewSense 12-Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 99.95 for item Braun BrewSense 12-Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,875 searchapi_io Processing item 31/40
DEBUG:delapp.searchapi_io:Processing item 31/40
DEBUG 2025-04-22 23:25:51,875 searchapi_io Raw price string: '$69.99' for item Better Chef Coffeemaker
DEBUG:delapp.searchapi_io:Raw price string: '$69.99' for item Better Chef Coffeemaker
DEBUG 2025-04-22 23:25:51,876 searchapi_io Parsed price: 69.99 for item Better Chef Coffeemaker
DEBUG:delapp.searchapi_io:Parsed price: 69.99 for item Better Chef Coffeemaker
DEBUG 2025-04-22 23:25:51,876 searchapi_io Processing item 32/40
DEBUG:delapp.searchapi_io:Processing item 32/40
DEBUG 2025-04-22 23:25:51,876 searchapi_io Raw price string: '$69.99' for item Keurig K-Express Single Serve K-Cup Pod Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$69.99' for item Keurig K-Express Single Serve K-Cup Pod Coffee Maker
DEBUG 2025-04-22 23:25:51,876 searchapi_io Parsed price: 69.99 for item Keurig K-Express Single Serve K-Cup Pod Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 69.99 for item Keurig K-Express Single Serve K-Cup Pod Coffee Maker
DEBUG 2025-04-22 23:25:51,876 searchapi_io Processing item 33/40
DEBUG:delapp.searchapi_io:Processing item 33/40
DEBUG 2025-04-22 23:25:51,876 searchapi_io Raw price string: '$69.99' for item 12-Cup Programmable Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$69.99' for item 12-Cup Programmable Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,876 searchapi_io Parsed price: 69.99 for item 12-Cup Programmable Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 69.99 for item 12-Cup Programmable Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,876 searchapi_io Processing item 34/40
DEBUG:delapp.searchapi_io:Processing item 34/40
DEBUG 2025-04-22 23:25:51,876 searchapi_io Raw price string: '$56.99' for item 2-Way Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$56.99' for item 2-Way Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,877 searchapi_io Parsed price: 56.99 for item 2-Way Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 56.99 for item 2-Way Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,877 searchapi_io Processing item 35/40
DEBUG:delapp.searchapi_io:Processing item 35/40
DEBUG 2025-04-22 23:25:51,877 searchapi_io Raw price string: '$37.43' for item Mr. Coffee Programmable 3-Way Brewing System 12-Cup Drip Coffee Makers
DEBUG:delapp.searchapi_io:Raw price string: '$37.43' for item Mr. Coffee Programmable 3-Way Brewing System 12-Cup Drip Coffee Makers
DEBUG 2025-04-22 23:25:51,877 searchapi_io Parsed price: 37.43 for item Mr. Coffee Programmable 3-Way Brewing System 12-Cup Drip Coffee Makers
DEBUG:delapp.searchapi_io:Parsed price: 37.43 for item Mr. Coffee Programmable 3-Way Brewing System 12-Cup Drip Coffee Makers
DEBUG 2025-04-22 23:25:51,877 searchapi_io Processing item 36/40
DEBUG:delapp.searchapi_io:Processing item 36/40
DEBUG 2025-04-22 23:25:51,877 searchapi_io Raw price string: '$89.99' for item Calphalon Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$89.99' for item Calphalon Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,877 searchapi_io Parsed price: 89.99 for item Calphalon Programmable Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 89.99 for item Calphalon Programmable Coffee Maker
DEBUG 2025-04-22 23:25:51,877 searchapi_io Processing item 37/40
DEBUG:delapp.searchapi_io:Processing item 37/40
DEBUG 2025-04-22 23:25:51,877 searchapi_io Raw price string: '$99.99' for item Instant Solo Single Serve Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$99.99' for item Instant Solo Single Serve Coffee Maker
DEBUG 2025-04-22 23:25:51,877 searchapi_io Parsed price: 99.99 for item Instant Solo Single Serve Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 99.99 for item Instant Solo Single Serve Coffee Maker
DEBUG 2025-04-22 23:25:51,877 searchapi_io Processing item 38/40
DEBUG:delapp.searchapi_io:Processing item 38/40
DEBUG 2025-04-22 23:25:51,877 searchapi_io Raw price string: '$79.99' for item World Market Haden Heritage 12 Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$79.99' for item World Market Haden Heritage 12 Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,878 searchapi_io Parsed price: 79.99 for item World Market Haden Heritage 12 Cup Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 79.99 for item World Market Haden Heritage 12 Cup Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,878 searchapi_io Processing item 39/40
DEBUG:delapp.searchapi_io:Processing item 39/40
DEBUG 2025-04-22 23:25:51,878 searchapi_io Raw price string: '$59.24' for item Krups Simply Brew Digital Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$59.24' for item Krups Simply Brew Digital Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,878 searchapi_io Parsed price: 59.24 for item Krups Simply Brew Digital Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 59.24 for item Krups Simply Brew Digital Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,878 searchapi_io Processing item 40/40
DEBUG:delapp.searchapi_io:Processing item 40/40
DEBUG 2025-04-22 23:25:51,878 searchapi_io Raw price string: '$35.00' for item Farberware 9 Cup High Temperature Drip Coffee Maker
DEBUG:delapp.searchapi_io:Raw price string: '$35.00' for item Farberware 9 Cup High Temperature Drip Coffee Maker
DEBUG 2025-04-22 23:25:51,878 searchapi_io Parsed price: 35.0 for item Farberware 9 Cup High Temperature Drip Coffee Maker
DEBUG:delapp.searchapi_io:Parsed price: 35.0 for item Farberware 9 Cup High Temperature Drip Coffee Maker
INFO 2025-04-22 23:25:51,878 searchapi_io Successfully processed 40 items out of 40 total results
INFO:delapp.searchapi_io:Successfully processed 40 items out of 40 total results
DEBUG:django.db.backends:(0.001) UPDATE "delapp_conversationstate" SET "conversation_id" = 58, "current_products" = '[]'::jsonb, "last_query" = 'coffee maker under 100 bucks', "last_category" = '', "applied_filters" = '{}'::jsonb, "last_intent" = NULL, "conversation_turn" = 1, "product_references" = '{}'::jsonb, "user_preferences" = '{}'::jsonb, "keywords" = '[]'::jsonb, "last_action" = NULL, "updated_at" = '2025-04-22T23:25:51.920607+00:00'::timestamptz WHERE "delapp_conversationstate"."id" = 14; args=(58, <django.db.backends.postgresql.psycopg_any.Jsonb object at 0x7e3b5ce62d50>, 'coffee maker under 100 bucks', '', <django.db.backends.postgresql.psycopg_any.Jsonb object at 0x7e3b5ce62720>, 1, <django.db.backends.postgresql.psycopg_any.Jsonb object at 0x7e3b5ce630b0>, <django.db.backends.postgresql.psycopg_any.Jsonb object at 0x7e3b5ce63260>, <django.db.backends.postgresql.psycopg_any.Jsonb object at 0x7e3b5ce605c0>, datetime.datetime(2025, 4, 22, 23, 25, 51, 920607, tzinfo=datetime.timezone.utc), 14); alias=default
WARNING 2025-04-22 23:25:51,922 views No products returned from agent for query: coffee maker under 100 bucks
WARNING:delapp.views:No products returned from agent for query: coffee maker under 100 bucks
