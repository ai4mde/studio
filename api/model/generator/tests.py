from django.urls import reverse
from django.test import SimpleTestCase
from rest_framework.test import APITestCase
from generator.models import Prototype
from generator.api.views.pipeline import (
    _collect_page_ast_nodes,
    _page_preview_subtitle,
    _render_page_body,
)
from metadata.models import Project, System
from django.contrib.auth.models import User
from uuid import uuid4

prototype_metadata = {
    "diagrams": [],
    "interfaces": [],
    "useAuthentication": True
}


class PipelinePreviewRenderHelpersTests(SimpleTestCase):

    def test_collect_page_ast_nodes_from_legacy_page_ast(self):
        page = {
            "ast": [
                {"tag": "h1", "text": "Legacy"},
                {"tag": "p", "text": "Body"},
            ]
        }
        nodes = _collect_page_ast_nodes(page)
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]["text"], "Legacy")

    def test_collect_page_ast_nodes_from_regions(self):
        page = {
            "regions": [
                {"id": "r1", "ast": [{"tag": "h1", "text": "Region title"}]},
                {"id": "r2", "ast": [{"tag": "p", "text": "Region body"}]},
            ]
        }
        nodes = _collect_page_ast_nodes(page)
        self.assertEqual([n["text"] for n in nodes], ["Region title", "Region body"])

    def test_collect_page_ast_nodes_from_components(self):
        page = {
            "regions": [
                {
                    "id": "r1",
                    "components": [
                        {"id": "c1", "ast": [{"tag": "h2", "text": "One"}]},
                        {"id": "c2", "ast": [{"tag": "div", "text": "Two"}]},
                    ],
                }
            ]
        }
        nodes = _collect_page_ast_nodes(page)
        self.assertEqual([n["text"] for n in nodes], ["One", "Two"])

    def test_render_page_body_falls_back_to_under_construction(self):
        page = {"action_ids": ["act1", "act2"]}
        html = _render_page_body(page)
        self.assertIn("Page under construction", html)
        self.assertIn("act1, act2", html)

    def test_page_preview_subtitle_prefers_regions_over_actions(self):
        page = {
            "regions": [{"id": "r1"}, {"id": "r2"}],
            "action_ids": ["act1"],
        }
        self.assertEqual(_page_preview_subtitle(page), "2 region(s)")

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
