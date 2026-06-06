from django.urls import reverse
from rest_framework.test import APITestCase
from generator.models import Prototype
from metadata.models import Interface, Project, System
from django.contrib.auth.models import User
from unittest.mock import patch, mock_open
from uuid import uuid4

prototype_metadata = {
    "diagrams": [],
    "interfaces": [],
    "useAuthentication": True
}

class PrototypeAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='sequoias')

        auth_url = '/api/v1/auth/token'
        auth_response = self.client.post(auth_url, {'username': 'admin', 'password': 'sequoias'}, format='json')
        self.assertEqual(auth_response.status_code, 200)
        self.token = auth_response.json()['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

        self.project1 = Project.objects.create(name="TestProject",
                                               description="Testing description."
                                               )
        self.system1 = System.objects.create(name="TestSystem1",
                                             project=self.project1,
                                             description="Testing system 1."
                                             )
        self.system2 = System.objects.create(name="TestSystem2",
                                             project=self.project1,
                                             description="Testing system 2."
                                             )

        self.prototype1 = Prototype.objects.create(name="TestPrototype1",
                                                   system=self.system1,
                                                   description="Testing prototype 1.",
                                                   metadata=prototype_metadata,
                                                   database_hash=uuid4())
        self.prototype2 = Prototype.objects.create(name="TestPrototype2",
                                                   system=self.system1,
                                                   description="Testing prototype 2.",
                                                   metadata=prototype_metadata,
                                                   database_hash=uuid4())
        self.prototype3 = Prototype.objects.create(name="TestPrototype3",
                                                   system=self.system2,
                                                   description="Testing prototype 3.",
                                                   metadata=prototype_metadata,
                                                   database_hash=uuid4())

        self.url = reverse('api-0.0.1:list_prototypes')

    def test_list_all_prototypes(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)  # All prototypes
        
        response_data = response.json()
        prototype_names = [prototype['name'] for prototype in response_data]
        self.assertIn(self.prototype1.name, prototype_names)
        self.assertIn(self.prototype2.name, prototype_names)
        self.assertIn(self.prototype3.name, prototype_names)

    def test_list_prototypes_by_system(self):
        response = self.client.get(self.url, {'system': self.system1.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)  # Prototype 1 & Prototype 2
        
        response_data = response.json()
        prototype_names = [prototype['name'] for prototype in response_data]
        self.assertIn(self.prototype1.name, prototype_names)
        self.assertIn(self.prototype2.name, prototype_names)

    def test_list_prototypes_empty_system(self):
        response = self.client.get(self.url, {'system': uuid4()}) # Random uuid
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)  # No prototypes

    def test_hot_reload_preserves_styling(self):
        interface = Interface.objects.create(
            system=self.system1,
            name="TestInterface",
            description="Test interface",
            data={
                "sections": [{"id": "section-1", "type": "card"}],
                "pages": [{"id": "page-1", "type": "home"}],
                "styling": {
                    "accentColor": "#123456",
                    "backgroundColor": "#ffffff",
                },
            },
        )

        payload = {
            "interface_id": str(interface.id),
            "sections": [{"id": "section-2", "type": "list"}],
            "pages": [{"id": "page-1", "type": "home"}],
            "styling": {
                "accentColor": "#ff0000",
                "backgroundColor": "#111111",
            },
        }

        with patch("generator.api.views.prototypes.requests.get") as mock_get, \
             patch("generator.api.views.prototypes.render_layout") as mock_render_layout, \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open()) as mock_file:
            mock_get.return_value.json.return_value = {
                "running": True,
                "system": str(self.system1.id),
                "name": "TestPrototype1",
            }
            mock_render_layout.return_value = [
                {"path": "templates/customer_browse_products.html", "content": "<html>hot reload</html>"}
            ]

            response = self.client.post(
                "/api/v1/generator/prototypes/hot_reload/",
                payload,
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"updated": 1})
        mock_render_layout.assert_called_once()
        rendered_interface_data = mock_render_layout.call_args.args[0]
        self.assertEqual(rendered_interface_data["styling"], payload["styling"])
        self.assertEqual(rendered_interface_data["sections"][0]["id"], payload["sections"][0]["id"])
        self.assertEqual(rendered_interface_data["sections"][0]["type"], payload["sections"][0]["type"])
        mock_file.assert_called_once()
