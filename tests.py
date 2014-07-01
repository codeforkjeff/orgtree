
from django.test import TestCase

from orgtree.models import Organization, OrganizationRelation, OrganizationRole, OrganizationType
from django.contrib.auth.models import User, Group


class OrgTreeTest(TestCase):

    def setUp(self):
        self.orgtype_umbrella = OrganizationType.objects.create(name="Umbrella Organization")
        self.orgtype_regional = OrganizationType.objects.create(name="Regional Network")
        self.orgtype_site = OrganizationType.objects.create(name="Service Site")

        self.group_superadmin = Group.objects.create(name="superadmin")
        self.group_regional_coordinator = Group.objects.create(name="regional coordinator")
        self.group_site_coordinator = Group.objects.create(name="site coordinator")


    def create_user(self, username, group):
        user = User.objects.create(username=username)
        user.groups.add(group)
        return user


    def create_org_role(self, user, group, org):
        return OrganizationRole.objects.create(user=user, group=group, organization=org)


    def create_org(self, name, orgtype):
        return Organization.objects.create(name=name, orgtype=orgtype)


    def create_umbrella_org(self, name):
        return self.create_org(name, self.orgtype_umbrella)


    def create_regional_org(self, name):
        return self.create_org(name, self.orgtype_regional)


    def create_site_org(self, name):
        return self.create_org(name, self.orgtype_site)


    def test_parent(self):
        org = self.create_umbrella_org("test 1")

        self.assertEqual(None, org.get_parent(), "expected no parent")

        child = self.create_regional_org("test regional org")
        org.add_child(child)

        self.assertEqual(org, child.get_parent(), "expected parent")


    def test_children(self):
        org = self.create_umbrella_org("test umbrella org")

        self.assertFalse(org.has_children(), "expected no children")

        child = self.create_regional_org("test regional org")
        org.add_child(child)

        self.assertTrue(org.has_children(), "expected children")


    def dump(self):
        """ dump data from database, for debugging tests """
        for org in Organization.objects.all().order_by("id"):
            print org.id, org.name

        for rel in OrganizationRelation.objects.all().order_by("ancestor", "descendent", "depth"):
            print rel.ancestor.id, rel.descendent.id, rel.depth


    def test_ancestors_descendents(self):

        org = self.create_umbrella_org("test umbrella org")

        self.assertEqual(0, org.get_ancestors().count())
        self.assertEqual(1, org.get_ancestors(include_self=True).count())
        self.assertTrue(org in org.get_ancestors(include_self=True))
        self.assertEqual(0, org.get_descendents().count())
        self.assertEqual(1, org.get_descendents(include_self=True).count())
        self.assertTrue(org in org.get_descendents(include_self=True))

        regional1 = self.create_regional_org("test regional org 1")
        org.add_child(regional1)

        regional2 = self.create_regional_org("test regional org 2")
        org.add_child(regional2)

        self.assertEqual(0, org.get_ancestors().count())
        self.assertEqual(1, regional1.get_ancestors().count())
        self.assertTrue(org in regional1.get_ancestors())
        self.assertEqual(2, regional1.get_ancestors(include_self=True).count())
        self.assertTrue(org in regional1.get_ancestors(include_self=True))
        self.assertTrue(regional1 in regional1.get_ancestors(include_self=True))

        self.assertEqual(2, org.get_descendents().count())
        self.assertTrue(regional1 in org.get_descendents())
        self.assertTrue(regional2 in org.get_descendents())
        self.assertEqual(3, org.get_descendents(include_self=True).count())
        self.assertTrue(org in org.get_descendents(include_self=True))
        self.assertTrue(regional1 in org.get_descendents(include_self=True))
        self.assertTrue(regional2 in org.get_descendents(include_self=True))

        site1 = self.create_site_org("test site org 1")
        regional1.add_child(site1)

        site2 = self.create_site_org("test site org 2")
        regional1.add_child(site2)

        self.assertEqual(2, site1.get_ancestors().count())
        self.assertTrue(org in site1.get_ancestors())
        self.assertTrue(regional1 in site1.get_ancestors())
        self.assertEqual(2, site2.get_ancestors().count())
        self.assertTrue(org in site2.get_ancestors())
        self.assertTrue(regional1 in site2.get_ancestors())

        self.assertEqual(None, org.get_first_ancestor_by_orgtype(self.orgtype_umbrella))
        self.assertEqual(org, regional1.get_first_ancestor_by_orgtype(self.orgtype_umbrella))
        self.assertEqual(regional1, site1.get_first_ancestor_by_orgtype(self.orgtype_regional))

        self.assertEqual(None, org.get_first_descendent_by_orgtype(self.orgtype_umbrella))
        self.assertEqual(regional1, org.get_first_descendent_by_orgtype(self.orgtype_regional))
        self.assertEqual(site1, org.get_first_descendent_by_orgtype(self.orgtype_site))


    def test_delete(self):

        # it's hard to test delete() b/c the flag needs to be
        # accounted for in queries across all methods, so this is
        # pretty incomplete

        org = self.create_umbrella_org("test 1")

        self.assertEqual(None, org.get_parent(), "expected no parent")

        regional1 = self.create_regional_org("test regional org 1")
        org.add_child(regional1)

        regional2 = self.create_regional_org("test regional org 2")
        org.add_child(regional2)

        self.assertEqual(2, org.get_children().count())
        self.assertEqual(2, org.get_descendents().count())

        regional1.delete()

        self.assertEqual(1, org.get_children().count())
        self.assertEqual(1, org.get_descendents().count())

        self.assertRaisesRegexp(Exception, "undeleted descendents", org.delete)


    def test_move(self):
        org = self.create_umbrella_org("test umbrella org")

        regional1 = self.create_regional_org("test regional org 1")
        org.add_child(regional1)

        regional2 = self.create_regional_org("test regional org 2")
        org.add_child(regional2)

        site1 = self.create_site_org("test site org 1")
        regional1.add_child(site1)

        site2 = self.create_site_org("test site org 2")
        regional1.add_child(site2)

        # move site2 from regional1 to regional2
        site2.move(regional2)

        self.assertEquals(2, org.get_children().count())
        self.assertTrue(regional1 in org.get_children())
        self.assertTrue(regional2 in org.get_children())

        self.assertEquals(1, regional1.get_children().count())
        self.assertTrue(site1 in regional1.get_children())

        self.assertEqual(1, regional2.get_children().count())
        self.assertTrue(site2 in regional2.get_children())

        # move regional1 to regional2, which is kinda weird but should work
        regional1.move(regional2)

        self.assertEquals(4, org.get_descendents().count())
        self.assertTrue(regional1 in org.get_descendents())
        self.assertTrue(regional2 in org.get_descendents())
        self.assertTrue(site1 in org.get_descendents())
        self.assertTrue(site2 in org.get_descendents())

        self.assertEquals(1, regional1.get_children().count())
        self.assertTrue(site1 in regional1.get_children())

        self.assertEquals(2, regional2.get_children().count())
        self.assertTrue(regional1 in regional2.get_children())
        self.assertTrue(site2 in regional2.get_children())


    def test_orphan(self):
        org = self.create_umbrella_org("test umbrella org")

        regional1 = self.create_regional_org("test regional org 1")
        org.add_child(regional1)

        regional2 = self.create_regional_org("test regional org 2")
        org.add_child(regional2)

        site1 = self.create_site_org("test site org 1")
        regional1.add_child(site1)

        site2 = self.create_site_org("test site org 2")
        regional2.add_child(site2)

        regional1.orphan()

        self.assertEquals(2, org.get_descendents().count())
        self.assertTrue(regional2 in org.get_descendents())
        self.assertTrue(site2 in org.get_descendents())

        self.assertEquals(1, regional1.get_children().count())
        self.assertTrue(site1 in regional1.get_children())


    def test_permissions(self):

        superadmin = self.create_user("admin1", self.group_superadmin)

        org = self.create_umbrella_org("test 1")

        regional1 = self.create_regional_org("test regional org 1")
        org.add_child(regional1)
        regional_coordinator = self.create_user("admin2", self.group_regional_coordinator)
        self.create_org_role(regional_coordinator, self.group_regional_coordinator, regional1)

        regional2 = self.create_regional_org("test regional org 2")
        org.add_child(regional2)

        self.assertEqual(3, Organization.objects.get_orgs_administered_by_user(superadmin).count())

        self.assertEqual(1, Organization.objects.get_orgs_administered_by_user(regional_coordinator).count())
        self.assertTrue(regional1 in Organization.objects.get_orgs_administered_by_user(regional_coordinator))

