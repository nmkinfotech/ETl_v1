import requests
from config import MONDAY_API_URL

def get_board_items(api_key: str, board_id: int):
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    # print(f"API Key:{api_key}\n")
    # print(f"Board ID:{board_id}")

    query = """
    query ($board_id: [ID!], $limit: Int, $cursor: String) {
        boards(ids: $board_id) {
            columns {
                  id
                  title
                  type
                }
            items_page(limit: $limit, cursor: $cursor) {
                cursor
                items {
                    id
                    name
                    column_values {
                        id
                        type
                        text
                        value
                    }
                    subitems {
                        id
                        name
                        column_values {
                            id
                            type
                            text
                            value
                        }
                    }
                }
            }
        }
    }
    """

    all_items = []
    cursor = None  # start with first page
    api_call_number = 1

    while True:
        variables = {
            "board_id": [board_id],
            "limit": 200,
            "cursor": cursor
        }
        # print(f"Making API call {api_call_number}")
        response = requests.post(
            MONDAY_API_URL,
            json={"query": query, "variables": variables},
            headers=headers
        )
        # print(f"Made API call {api_call_number}")
        api_call_number+=1
        # response.raise_for_status()
        data = response.json()
        # print(data)
        board_data = data["data"]["boards"][0]
        items_page = board_data["items_page"]
        items = items_page["items"]
        columns = board_data["columns"]
        all_items.extend(items)
        print(f"Fetched {len(all_items)} items so far...")

        cursor = items_page.get("cursor")

        if not cursor:
            break  # stop when no more pages

    print(f"✅ Total items fetched: {len(all_items)}")
    return all_items,columns
