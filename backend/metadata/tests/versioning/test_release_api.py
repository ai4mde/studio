import json
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from config.auth import create_token
from diagram.models import Diagram
from metadata.models import Project, Release, System
from metadata.services.versioning import create_release, snapshot_project


BASE_URL = "/api/v1/metadata/releases/"


class ReleaseAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(name="Main project", description="Original")
        cls.system = System.objects.create(project=cls.project, name="Main system")
        cls.diagram = Diagram.objects.create(
            system=cls.system, name="Overview", type="class"
        )
        cls.other_project = Project.objects.create(name="Other project")
        cls.other_system = System.objects.create(
            project=cls.other_project, name="Other system"
        )

        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="release-api-tester", password="test-password"
        )

    def setUp(self):
        user, token = create_token("release-api-tester", "test-password")
        self.assertIsNotNone(user)
        self.assertIsNotNone(token)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def _json_post(self, url, data):
        return self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

    def _upload(self, snapshot, *, name="Imported", description="Imported snapshot"):
        file = SimpleUploadedFile(
            "release.json",
            json.dumps(snapshot).encode("utf-8"),
            content_type="application/json",
        )
        return self.client.post(
            f"{BASE_URL}import/{self.project.pk}/",
            data={"file": file, "name": name, "description": description},
        )

    def _release(self, name="Version 1", *, project=None):
        return create_release((project or self.project).pk, name)

    def test_list_only_returns_releases_for_requested_project(self):
        a = self._release("First")
        b = self._release("Second")
        other = self._release("Other release", project=self.other_project)

        response = self.client.get(BASE_URL, {"project_id": str(self.project.pk)})

        self.assertEqual(response.status_code, 200, response.content)
        records = response.json()
        self.assertEqual({row["id"] for row in records}, {str(a.pk), str(b.pk)})
        self.assertNotIn(str(other.pk), {row["id"] for row in records})
        self.assertEqual(records[0]["id"], str(b.pk))
        self.assertTrue(all("project_data" not in row for row in records))

    def test_list_empty_project(self):
        response = self.client.get(
            BASE_URL, {"project_id": str(self.other_project.pk)}
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), [])

    def test_create_release_saves_snapshot_and_sets_current_release(self):
        response = self._json_post(BASE_URL, {
            "project_id": str(self.project.pk),
            "name": "Milestone",
            "description": "First milestone",
            "release_notes": ["Added overview"],
        })

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        release = Release.objects.get(pk=payload["id"])
        self.assertEqual(release.name, "Milestone")
        self.assertEqual(release.description, "First milestone")
        self.assertEqual(release.release_notes, ["Added overview"])
        self.assertEqual(release.project_data, snapshot_project(self.project.pk))
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, release.pk)
        self.assertNotIn("project_data", payload)

    def test_create_release_requires_name(self):
        before = Release.objects.count()
        response = self._json_post(BASE_URL, {
            "project": str(self.project.pk),
            "description": "No name",
        })
        self.assertEqual(response.status_code, 422, response.content)
        self.assertEqual(Release.objects.count(), before)

    def test_export_is_a_downloadable_json_file(self):
        release = self._release()
        response = self.client.get(f"{BASE_URL}{release.pk}/export/")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response["Content-Type"].startswith("application/json"))
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(f"release-{release.pk}.json", response["Content-Disposition"])
        self.assertEqual(json.loads(response.content), release.project_data)

    def test_export_does_not_change_when_live_project_changes(self):
        release = self._release()
        original = deepcopy(release.project_data)
        Project.objects.filter(pk=self.project.pk).update(name="Changed live project")

        response = self.client.get(f"{BASE_URL}{release.pk}/export/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(json.loads(response.content), original)

    def test_import_upload_creates_release_without_activating_it(self):
        current = self._release("Current")
        original_state = snapshot_project(self.project.pk)

        response = self._upload(original_state)

        self.assertEqual(response.status_code, 200, response.content)
        imported = Release.objects.get(pk=response.json()["id"])
        self.assertEqual(imported.name, "Imported")
        self.assertEqual(imported.description, "Imported snapshot")
        self.assertEqual(imported.project_data, original_state)
        self.assertEqual(snapshot_project(self.project.pk), original_state)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, current.pk)

    def test_import_rejects_invalid_json_file_with_client_error(self):
        """Contract: invalid uploads should not become HTTP 500 responses."""
        file = SimpleUploadedFile(
            "invalid.json", b"{not-json", content_type="application/json"
        )
        before = Release.objects.count()
        response = self.client.post(
            f"{BASE_URL}import/{self.project.pk}/",
            data={"file": file, "name": "Invalid"},
        )
        self.assertIn(response.status_code, (400, 422), response.content)
        self.assertEqual(Release.objects.count(), before)

    def test_import_rejects_snapshot_from_another_project(self):
        snapshot = snapshot_project(self.other_project.pk)
        before = Release.objects.count()

        response = self._upload(snapshot)

        self.assertIn(response.status_code, (400, 422), response.content)
        self.assertEqual(Release.objects.count(), before)

    def test_restore_release_restores_project(self):
        release = self._release("Saved")
        expected = deepcopy(release.project_data)
        Project.objects.filter(pk=self.project.pk).update(name="Unsaved")

        response = self.client.post(f"{BASE_URL}{release.pk}/restore/?force=true")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(snapshot_project(self.project.pk), expected)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, release.pk)

    def test_restore_rejects_unsaved_changes_without_force(self):
        release = self._release()
        Project.objects.filter(pk=self.project.pk).update(name="Unsaved")
        response = self.client.post(f"{BASE_URL}{release.pk}/restore/")

        self.assertEqual(response.status_code, 409, response.content)
        self.assertIn("message", response.json())
        self.assertIn("changed", response.json()["message"].lower())
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Unsaved")
        self.assertEqual(self.project.current_release_id, release.pk)

    def test_restore_without_changes_does_not_require_force(self):
        initial = self._release("Original")
        Project.objects.filter(pk=self.project.pk).update(name="Next")
        self._release("Current")

        response = self.client.post(f"{BASE_URL}{initial.pk}/restore/")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(snapshot_project(self.project.pk), initial.project_data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, initial.pk)


    def test_merge_creates_release_but_does_not_modify_live_project(self):
        ground_truth = self._release("A")
        snapshot_a = deepcopy(ground_truth.project_data)

        added = Diagram.objects.create(
            system=self.system, name="Added by B", type="class"
        )

        incoming = self._release("B")
        snapshot_b = deepcopy(incoming.project_data)

        live_before = snapshot_project(self.project.pk)

        self.project.refresh_from_db()
        current_before = self.project.current_release_id

        response = self._json_post(f"{BASE_URL}merge/", {
            "ground_truth_id": str(ground_truth.pk),
            "incoming_id": str(incoming.pk),
            "name": "Combined",
            "description": "Merged branches",
            "release_notes": ["Merge A + B"],
        })

        self.assertEqual(response.status_code, 200, response.content)

        merged = Release.objects.get(pk=response.json()["id"])
        self.assertEqual(merged.name, "Combined")
        self.assertEqual(merged.description, "Merged branches")
        self.assertEqual(merged.release_notes, ["Merge A + B"])

        self.assertTrue(any(
            item["model"] == Diagram._meta.label_lower
            and item["pk"] == str(added.pk)
            for item in merged.project_data["objects"]
        ))

        self.assertEqual(snapshot_project(self.project.pk), live_before)

        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, current_before)

        ground_truth.refresh_from_db()
        incoming.refresh_from_db()

        self.assertEqual(ground_truth.project_data, snapshot_a)
        self.assertEqual(incoming.project_data, snapshot_b)


    def test_merge_rejects_different_projects_with_readable_conflict(self):
        a = self._release("A")
        b = self._release("B", project=self.other_project)
        before = Release.objects.count()

        response = self._json_post(f"{BASE_URL}merge/", {
            "ground_truth_id": str(a.pk),
            "incoming_id": str(b.pk),
            "name": "Impossible merge",
        })

        self.assertEqual(response.status_code, 409, response.content)
        payload = response.json()
        self.assertEqual(payload["code"], "DIFFERENT_PROJECTS")
        self.assertTrue(payload["message"])
        self.assertTrue(payload["resolution"])
        self.assertEqual(Release.objects.count(), before)

    def test_merge_ground_truth_wins_in_api(self):
        a = self._release("Ground truth")
        Project.objects.filter(pk=self.project.pk).update(name="Incoming project")
        b = self._release("Incoming")

        response = self._json_post(f"{BASE_URL}merge/", {
            "ground_truth_id": str(a.pk),
            "incoming_id": str(b.pk),
            "name": "Merged",
        })

        self.assertEqual(response.status_code, 200, response.content)
        merged = Release.objects.get(pk=response.json()["id"])
        project_record = next(
            item for item in merged.project_data["objects"]
            if item["model"] == Project._meta.label_lower
        )
        self.assertEqual(project_record["fields"]["name"], "Main project")

    def test_merge_result_can_be_restored_through_api(self):
        a = self._release("A")
        Diagram.objects.create(system=self.system, name="B diagram", type="class")
        b = self._release("B")
        response = self._json_post(f"{BASE_URL}merge/", {
            "ground_truth_id": str(a.pk),
            "incoming_id": str(b.pk),
            "name": "Merged",
        })
        self.assertEqual(response.status_code, 200, response.content)
        merged = Release.objects.get(pk=response.json()["id"])

        restore = self.client.post(f"{BASE_URL}{merged.pk}/restore/?force=true")
        self.assertEqual(restore.status_code, 200, restore.content)
        self.assertEqual(snapshot_project(self.project.pk), merged.project_data)


    def _project_import_upload(self, content, *, name="Imported baseline"):
        file = SimpleUploadedFile(
            "project.json", content, content_type="application/json"
        )
        return self.client.post(
            "/api/v1/metadata/projects/import/",
            data={"file": file, "name": name},
        )

    def _new_project_snapshot(self):
        """Create a project snapshot, then delete the original project."""
        source = Project.objects.create(
            name="From JSON", description="Transferred"
        )
        system = System.objects.create(
            project=source, name="Imported system"
        )
        diagram = Diagram.objects.create(
            system=system, name="Imported diagram", type="class"
        )

        snapshot = snapshot_project(source.pk)
        ids = (source.pk, system.pk, diagram.pk)
        source.delete()

        return snapshot, ids

    def test_project_import_upload_creates_project_and_initial_release(self):
        snapshot, (project_id, system_id, diagram_id) = self._new_project_snapshot()
        before = Release.objects.count()

        response = self._project_import_upload(
            json.dumps(snapshot).encode("utf-8"),
            name="Imported baseline",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["id"], str(project_id))

        project = Project.objects.get(pk=project_id)
        self.assertEqual(project.name, "From JSON")
        self.assertEqual(System.objects.get(pk=system_id).project_id, project_id)
        self.assertEqual(Diagram.objects.get(pk=diagram_id).system_id, system_id)
        self.assertEqual(snapshot_project(project_id), snapshot)

        self.assertEqual(Release.objects.count(), before + 1)
        self.assertIsNotNone(project.current_release)
        self.assertEqual(project.current_release.name, "Imported baseline")
        self.assertEqual(project.current_release.project_data, snapshot)

    def test_project_import_rejects_existing_project_without_changes(self):
        snapshot = snapshot_project(self.project.pk)
        before = Release.objects.count()

        response = self._project_import_upload(
            json.dumps(snapshot).encode("utf-8")
        )

        self.assertEqual(response.status_code, 409, response.content)
        self.assertIn("message", response.json())
        self.assertIn("version", response.json()["message"].lower())
        self.assertEqual(Release.objects.count(), before)
        self.assertEqual(snapshot_project(self.project.pk), snapshot)

    def test_project_import_rejects_invalid_json(self):
        before_projects = Project.objects.count()
        before_releases = Release.objects.count()

        response = self._project_import_upload(b"{not-json")

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("message", response.json())
        self.assertEqual(Project.objects.count(), before_projects)
        self.assertEqual(Release.objects.count(), before_releases)

    def test_project_import_rejects_invalid_snapshot_without_writes(self):
        snapshot, (project_id, _, _) = self._new_project_snapshot()
        snapshot["objects"].append(deepcopy(snapshot["objects"][0]))

        before_projects = Project.objects.count()
        before_releases = Release.objects.count()

        response = self._project_import_upload(
            json.dumps(snapshot).encode("utf-8")
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("message", response.json())
        self.assertFalse(Project.objects.filter(pk=project_id).exists())
        self.assertEqual(Project.objects.count(), before_projects)
        self.assertEqual(Release.objects.count(), before_releases)

    def test_project_import_rejects_object_uuid_collision(self):
        snapshot, (project_id, system_id, _) = self._new_project_snapshot()

        existing_system = System.objects.create(
            pk=system_id,
            project=self.other_project,
            name="Existing system",
        )
        before_releases = Release.objects.count()

        response = self._project_import_upload(
            json.dumps(snapshot).encode("utf-8")
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("message", response.json())
        self.assertFalse(Project.objects.filter(pk=project_id).exists())
        self.assertEqual(Release.objects.count(), before_releases)

        existing_system.refresh_from_db()
        self.assertEqual(existing_system.project_id, self.other_project.pk)
        self.assertEqual(existing_system.name, "Existing system")
