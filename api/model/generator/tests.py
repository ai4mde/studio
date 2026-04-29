from django.urls import reverse
from django.test import SimpleTestCase
from rest_framework.test import APITestCase
from generator.models import Prototype
from generator.api.views.pipeline import (
    _collect_page_ast_nodes,
    _page_preview_subtitle,
    _render_composition_preview,
    _render_page_body,
    _resolve_page_active_composition,
)
from generator.api.views.interface_gen import (
    _apply_structure_payload,
    _extract_variant_structure_payload,
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
        # Each region is wrapped in a div container with data-region and children
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]["tag"], "div")
        self.assertEqual(nodes[0]["attrs"]["data-region"], "r1")
        self.assertEqual(nodes[0]["children"][0]["text"], "Region title")
        self.assertEqual(nodes[1]["attrs"]["data-region"], "r2")
        self.assertEqual(nodes[1]["children"][0]["text"], "Region body")

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
        # Region is wrapped in a div container; component AST nodes are collected as children
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["tag"], "div")
        self.assertEqual(nodes[0]["attrs"]["data-region"], "r1")
        children = nodes[0]["children"]
        self.assertEqual([c["text"] for c in children], ["One", "Two"])

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

    def test_resolve_page_active_composition_prefers_explicit_composition(self):
        page = {
            "composition": {"page_archetype": "product-detail", "skeleton_id": "explicit"},
            "selectedVariantId": "variant-b",
            "candidateVariants": [
                {"id": "variant-b", "composition": {"page_archetype": "dashboard", "skeleton_id": "candidate"}},
            ],
        }

        active = _resolve_page_active_composition(page)

        self.assertEqual(active["skeleton_id"], "explicit")

    def test_render_page_body_uses_composition_preview_when_ast_missing(self):
        page = {
            "selectedVariantId": "variant-a",
            "candidateVariants": [
                {
                    "id": "variant-a",
                    "composition": {
                        "page_archetype": "product-detail",
                        "skeleton_id": "product-detail-buybox-right",
                        "region_order": ["hero_primary", "supporting"],
                        "bindings": [
                            {
                                "section_id": "section-gallery",
                                "capability": "gallery",
                                "component_variant": "carousel-gallery",
                                "region_id": "hero_primary",
                            },
                            {
                                "section_id": "section-related-products",
                                "capability": "related-items",
                                "component_variant": "product-recommendation-carousel",
                                "region_id": "supporting",
                            },
                        ],
                    },
                }
            ],
        }

        html = _render_page_body(page)

        self.assertIn("composition-preview", html)
        self.assertIn("hero primary", html)
        self.assertIn("section-gallery", html)
        self.assertIn("product-detail-buybox-right", html)


class InterfaceGenStructureHelpersTests(SimpleTestCase):

    def test_extract_variant_structure_payload_includes_candidates_and_composition(self):
        variant = {
            "id": "variant-conversion-first",
            "composition": {"pagesById": {
                "page-1": {"page_archetype": "product-detail", "skeleton_id": "product-detail-buybox-right"},
            }},
        }
        session = {
            "variants": [
                variant,
                {"id": "variant-exploration-first",
                 "composition": {"pagesById": {
                     "page-1": {"page_archetype": "product-detail", "skeleton_id": "product-detail-stack"},
                 }}},
            ]
        }

        payload = _extract_variant_structure_payload(variant, session)

        self.assertEqual(payload["selectedVariantId"], "variant-conversion-first")
        self.assertEqual(len(payload["candidateVariants"]), 2)
        # pagesById from selected variant is preserved
        self.assertEqual(
            payload["composition"]["pagesById"]["page-1"]["skeleton_id"],
            "product-detail-buybox-right",
        )
        # candidateVariantsByPageId built from all session variants
        cands = payload["composition"]["candidateVariantsByPageId"]["page-1"]
        self.assertEqual(len(cands), 2)
        ids = [c["id"] for c in cands]
        self.assertIn("variant-conversion-first", ids)
        self.assertIn("variant-exploration-first", ids)

    def test_extract_variant_structure_payload_no_candidates_by_page_when_no_pagesById(self):
        """Variants without pagesById composition should not produce candidateVariantsByPageId."""
        variant = {"id": "variant-a", "composition": {"page_archetype": "detail", "skeleton_id": "detail-card"}}
        session = {"variants": [variant]}

        payload = _extract_variant_structure_payload(variant, session)

        self.assertNotIn("candidateVariantsByPageId", payload.get("composition", {}))

    def test_apply_structure_payload_merges_selected_variant_and_composition(self):
        interface_data = {
            "pages": [{
                "id": "page-1",
                "name": "Product detail",
            }],
            "theme": {"name": "Original"},
        }
        structure_payload = {
            "selectedVariantId": "variant-conversion-first",
            "candidateVariants": [{"id": "variant-conversion-first"}, {"id": "variant-compact-detail"}],
            "composition": {
                "pagesById": {"page-1": {"page_archetype": "product-detail", "skeleton_id": "product-detail-buybox-right"}},
            },
        }

        merged = _apply_structure_payload(interface_data, structure_payload)

        self.assertEqual(merged["selectedVariantId"], "variant-conversion-first")
        self.assertEqual(len(merged["candidateVariants"]), 2)
        self.assertEqual(
            merged["composition"]["pagesById"]["page-1"]["page_archetype"],
            "product-detail",
        )
        self.assertEqual(merged["theme"]["name"], "Original")
        # selectedVariantId is also stamped on each page dict
        self.assertEqual(merged["pages"][0]["selectedVariantId"], "variant-conversion-first")

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
