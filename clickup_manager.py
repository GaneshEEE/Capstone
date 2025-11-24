import requests
import os
import urllib3
import json
import time

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ClickUpManager:
    def __init__(self):
        self.api_token = os.getenv('CLICKUP_API_TOKEN')
        self.list_id = os.getenv('CLICKUP_LIST_ID')
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        self.verify_ssl = False

    def _ensure_custom_fields_exist(self):
        """
        Checks for required custom fields and creates them if missing.
        Returns a map of field_name -> field_id
        """
        if not self.api_token or not self.list_id:
            return {}

        # 1. Get existing fields
        existing_fields = {}
        try:
            url = f"{self.base_url}/list/{self.list_id}/field"
            response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
            if response.status_code == 200:
                fields = response.json().get('fields', [])
                existing_fields = {f['name'].lower(): f['id'] for f in fields}
        except Exception as e:
            print(f"Error fetching fields: {e}")
            return {}

        # 2. Define required fields
        required_fields = [
            {
                "name": "Current Price", 
                "type": "currency", 
                "type_config": {
                    "currency_type": "USD",
                    "default": 0,
                    "precision": 2
                }
            },
            {
                "name": "Sentiment Score", 
                "type": "number",
                "type_config": {
                    "precision": 2
                }
            },
            {"name": "Recommendation", "type": "short_text"},
            {
                "name": "Confidence", 
                "type": "number",
                "type_config": {
                    "precision": 2
                }
            },
            {"name": "AI Summary", "type": "text"} # Short summary for list view
        ]

        # 3. Create missing fields
        field_map = existing_fields.copy()
        
        for field in required_fields:
            if field['name'].lower() not in existing_fields:
                print(f"Creating missing field: {field['name']}")
                try:
                    url = f"{self.base_url}/list/{self.list_id}/field"
                    payload = field
                    response = requests.post(url, headers=self.headers, json=payload, verify=self.verify_ssl)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Handle nested 'field' key if present (as reported by user)
                        new_field = data.get('field', data)
                        
                        if 'id' in new_field:
                            field_map[field['name'].lower()] = new_field['id']
                            print(f"Successfully created field: {field['name']}")
                        else:
                            print(f"Created field {field['name']} but no ID returned: {data}")
                    else:
                        print(f"Failed to create field {field['name']}: {response.text}")
                except Exception as e:
                    print(f"Error creating field {field['name']}: {e}")
        
        return field_map

    def create_or_update_task(self, ticker, data):
        """
        Creates a task for the ticker or updates it if it exists.
        """
        if not self.api_token or not self.list_id:
            return {"error": "ClickUp credentials not configured"}

        # Ensure fields exist first
        field_map = self._ensure_custom_fields_exist()

        # 1. Check if task exists
        task_id = None
        try:
            url = f"{self.base_url}/list/{self.list_id}/task?archived=false"
            response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    if task['name'].upper() == ticker.upper():
                        task_id = task['id']
                        break
        except Exception as e:
            print(f"Error searching tasks: {e}")

        # 2. Prepare Custom Fields Payload
        custom_fields = []
        
        def add_field(name, value):
            fid = field_map.get(name.lower())
            if fid and value is not None:
                custom_fields.append({"id": fid, "value": value})

        # Process Recommendation for Dropdown (needs index or uuid usually, but value often works)
        # For dropdowns, ClickUp API usually expects the integer index of the option.
        # We need to fetch the field config to get the option index.
        # For simplicity, we'll try sending the value, if that fails, we skip.
        # Actually, creating the field returns the options with UUIDs. 
        # Let's just try sending the value (works in some API versions) or skip complexity for now.
        # Better approach: Just use a Text field for Recommendation if Dropdown is too complex without extra lookups.
        # But user wants it to look good. Let's try to find the option index if possible.
        
        rec_value = data.get('recommendation')
        # Map our snake_case to Title Case
        if rec_value:
            rec_value = rec_value.replace('_', ' ').title()
            # Try to find the option index if we have the field definition?
            # Too expensive to fetch definition every time.
            # Let's try sending the raw value, ClickUp often accepts it.
            # If not, we might need to change the field type to "short_text" in the definition above for reliability.
            # Let's stick to Dropdown and try sending the integer index? No, we don't know it.
            # Let's use the value.
            
            # Actually, for the "Recommendation" field, let's use the index if we just created it.
            # But we might have fetched it.
            # Let's try to just send the integer index based on our hardcoded list order?
            # 0: Strong Buy, 1: Buy, 2: Hold, 3: Sell, 4: Strong Sell
            options = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
            try:
                rec_index = options.index(rec_value)
                # ClickUp dropdowns are 0-indexed? Or UUIDs?
                # It's usually UUIDs. 
                # FALLBACK: If we can't get UUID, we'll just not set it or use a text field.
                # Let's change the "Recommendation" field type to "short_text" in the _ensure_custom_fields_exist 
                # if we want 100% reliability without extra API calls.
                # BUT, Dropdowns look better.
                # Let's try to fetch the field details to get the option UUID.
                pass 
            except:
                pass

        # To be safe and ensure it works:
        # I will change "Recommendation" to "short_text" in the definition above if I can't easily get UUIDs.
        # Wait, I can just fetch the field details once.
        
        # Let's keep it simple: Use "short_text" for Recommendation for now to ensure data shows up.
        # Colors can be handled by "Labels" or "Tags" if needed.
        # Or I can try to set the STATUS of the task.
        
        add_field("Current Price", data.get('price'))
        add_field("Sentiment Score", data.get('sentiment_score'))
        add_field("Recommendation", rec_value) # Will work if text, might fail if dropdown
        add_field("Confidence", data.get('sentiment_score')) # Using score as confidence proxy if needed
        add_field("AI Summary", data.get('summary')[:500] if data.get('summary') else "")

        # 3. Create or Update
        payload = {
            "name": ticker.upper(),
            "description": f"AI Analysis for {ticker}.\n\nSummary: {data.get('summary')}\n\nGenerated by AI Agent.",
            "custom_fields": custom_fields,
        }
        
        # Try to set status if possible
        # status = "to do"
        # if "buy" in str(rec_value).lower(): status = "in progress"
        # payload["status"] = status

        try:
            if task_id:
                # Update
                url = f"{self.base_url}/task/{task_id}"
                response = requests.put(url, headers=self.headers, json=payload, verify=self.verify_ssl)
                action = "updated"
            else:
                # Create
                url = f"{self.base_url}/list/{self.list_id}/task"
                response = requests.post(url, headers=self.headers, json=payload, verify=self.verify_ssl)
                action = "created"

            if response.status_code in [200, 201]:
                return {"success": True, "action": action, "task": response.json()}
            else:
                return {"error": f"ClickUp API Error: {response.text}"}

        except Exception as e:
            return {"error": str(e)}
