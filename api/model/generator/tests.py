from django.urls import reverse
from rest_framework.test import APITestCase
from generator.models import Prototype
from metadata.models import Project, System
from django.contrib.auth.models import User
from uuid import uuid4

prototype_metadata = {
    "diagrams": [],
    "interfaces": [],
    "useAuthentication": True
}

class PrototypeAPITests(APITestCase):

    def setUp(self):
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
        response = self.client.get(self.url, {'system': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)  # No prototypes
