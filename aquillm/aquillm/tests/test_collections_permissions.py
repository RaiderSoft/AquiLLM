from django.test import TestCase
from django.contrib.auth.models import User
from aquillm.models import Collection, CollectionPermission

class CollectionPermissionPropagationTest(TestCase):
    def setUp(self):
        # Create a user.
        self.user = User.objects.create(username="testuser")
        # Create a parent collection.
        self.parent_collection = Collection.objects.create(name="Parent Collection")
        # Create a child collection nested within the parent.
        self.child_collection = Collection.objects.create(name="Child Collection", parent=self.parent_collection)

    def test_permission_creation_propagates(self):
        # Create a permission on the parent collection.
        parent_perm = CollectionPermission.objects.create(
            user=self.user, 
            collection=self.parent_collection, 
            permission="VIEW"
        )
        # Check that a corresponding permission is automatically created for the child.
        child_perm = CollectionPermission.objects.filter(
            user=self.user, 
            collection=self.child_collection
        ).first()
        self.assertIsNotNone(child_perm, "Child collection permission should be created.")
        self.assertEqual(child_perm.permission, "VIEW", "Child collection permission should match the parent's.")

    def test_permission_update_propagates(self):
        # Create a permission on the parent collection and propagate it.
        parent_perm = CollectionPermission.objects.create(
            user=self.user, 
            collection=self.parent_collection, 
            permission="VIEW"
        )
        # Update the parent's permission.
        parent_perm.permission = "EDIT"
        parent_perm.save()
        # Fetch the child's permission and ensure it's updated.
        child_perm = CollectionPermission.objects.get(
            user=self.user, 
            collection=self.child_collection
        )
        self.assertEqual(child_perm.permission, "EDIT", "Child collection permission should update on parent's change.")