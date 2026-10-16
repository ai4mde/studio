from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from model.auth import create_token


class GeneratorAuthenticationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="generator-auth-test", password="test-password"
        )
        _, self.token = create_token(user.username, "test-password")
        self.system_id = str(uuid4())
        self.candidate_id = str(uuid4())
        self.revision_id = str(uuid4())
        self.writes = [
            ("/api/v1/generate-model", {"process_text": "Review a request."}),
            ("/api/v1/refine-model", {"system_id": self.system_id, "instruction": "Review first."}),
            ("/api/v1/select-candidate", {"candidate_id": self.candidate_id}),
            ("/api/v1/restore-revision", {"system_id": self.system_id, "revision_id": self.revision_id}),
            ("/api/v1/synchronize-human-edit", {"system_id": self.system_id}),
        ]

    def test_anonymous_cannot_use_generator_or_read_revisions(self):
        with patch("model.experiment_pipeline.run_pipeline") as generate:
            for path, body in self.writes:
                with self.subTest(path=path):
                    response = self.client.post(path, body, content_type="application/json")
                    self.assertEqual(response.status_code, 401)
            response = self.client.get(f"/api/v1/system-revisions/{self.system_id}")
            self.assertEqual(response.status_code, 401)
        generate.assert_not_called()

    def test_cookie_alone_cannot_trigger_generator_writes_without_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.cookies["key"] = self.token
        with patch("model.experiment_pipeline.run_pipeline") as generate:
            for path, body in self.writes:
                with self.subTest(path=path):
                    response = client.post(path, body, content_type="application/json")
                    self.assertEqual(response.status_code, 401)
        generate.assert_not_called()

    def test_existing_bearer_token_works_for_all_generator_routes(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {self.token}"
        patches = [
            ("run_pipeline", self.writes[0]),
            ("refine_selected_model", self.writes[1]),
            ("select_provisional_candidate", self.writes[2]),
            ("restore_revision", self.writes[3]),
            ("synchronize_human_edit", self.writes[4]),
        ]
        for function, (path, body) in patches:
            with self.subTest(path=path), patch(
                f"model.experiment_pipeline.{function}", return_value={"ok": True}
            ) as operation:
                response = self.client.post(path, body, content_type="application/json")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["ok"])
                operation.assert_called_once()

        with patch("model.experiment_pipeline.get_system_revisions", return_value={"revisions": []}):
            response = self.client.get(f"/api/v1/system-revisions/{self.system_id}")
        self.assertEqual(response.status_code, 200)

    def test_revision_read_accepts_existing_cookie_authentication(self):
        self.client.cookies["key"] = self.token
        with patch("model.experiment_pipeline.get_system_revisions", return_value={"revisions": []}):
            response = self.client.get(f"/api/v1/system-revisions/{self.system_id}")
        self.assertEqual(response.status_code, 200)
