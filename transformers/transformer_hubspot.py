import pandas as pd

def hubspot_response_to_dataframe(board_data: dict, columns:dict) -> pd.DataFrame:
    rows = []
    # items = board_data["data"]["boards"][0]["items_page"]["items"]
    all_items = board_data

    columns = columns

    id_to_dict = {col['id']: col for col in columns}

    # print(id_to_dict)

    for item in all_items:
        base_row = {"item_id": item["id"], "item_name": item["name"]}

        # Add item-level columns
        for col in item["column_values"]:
            current_col_id = col["id"]
            current_col_title = id_to_dict.get(current_col_id)["title"]
            # print(f"col_name:{current_col_title}\n")
            if col["type"] == "subtasks":
                continue
            base_row[current_col_title] = col["text"]
            # Handle subitems (if any)
        if len(item.get("subitems", [])) > 0:
            for si in item["subitems"]:
                # Create a copy of the base row for each subitem
                row = base_row.copy()
                row["subitem_name"] = si["name"]
                for si_cv in si["column_values"]:
                    # Safer column naming
                    row[f"subitem_{si_cv['id']}"] = si_cv["text"]
                rows.append(row)
        else:
            # No subitems — just append the item-level row
            rows.append(base_row)

    
    # print(data["data"]["boards"][0]["columns"])
    # print(rows)
    return pd.DataFrame(rows)