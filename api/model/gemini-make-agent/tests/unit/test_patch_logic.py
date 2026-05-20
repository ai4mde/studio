import json
from unittest.mock import patch, MagicMock
import pytest
from app.tools import apply_interface_patch

def test_apply_interface_patch_with_attributes_and_query():
    interface_id = "test-uuid"
    
    # Mock current interface data
    current_data = {
        "id": interface_id,
        "name": "Test Interface",
        "description": "Desc",
        "system": "sys-uuid",
        "actor": "actor-uuid",
        "data": {
            "sections": [
                {
                    "id": "sec-1",
                    "layout": "card",
                    "attributes": ["name"],
                    "query": {"limit": 10},
                    "style": {"color": "rose"}
                }
            ],
            "pages": [],
            "styling": {},
            "tokens": {}
        }
    }
    
    patch_dict = {
        "sections": [
            {
                "id": "sec-1",
                "attributes": ["name", "seller.name"],
                "query": {"limit": 5, "order_by": ["-price"]},
                "style": {"color": "blue"}
            }
        ]
    }
    
    with patch("requests.get") as mock_get, patch("requests.put") as mock_put:
        mock_get.return_value.json.return_value = current_data
        mock_get.return_value.raise_for_status = MagicMock()
        mock_put.return_value.raise_for_status = MagicMock()
        
        result = apply_interface_patch(interface_id, patch_dict)
        
        assert "successfully" in result
        
        # Verify the payload sent to PUT
        args, kwargs = mock_put.call_args
        sent_data = kwargs["json"]["data"]
        
        section = sent_data["sections"][0]
        assert section["attributes"] == ["name", "seller.name"]
        assert section["query"] == {"limit": 5, "order_by": ["-price"]}
        assert section["style"]["color"] == "blue"
        # Ensure other fields are preserved
        assert section["layout"] == "card"
