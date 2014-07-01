
"""
This is an implementation of a closure table design for representing a
hierarchical organization tree using relational database tables.

This code also demonstrates how users can be given permissions at
certain nodes in the tree, and how to retrieve that subtree of orgs,
which is a common real-world use case (ex: a regional coordinator who
has permission to administrate all orgs that fall under a
"U.S. Northeast" organization)

"""

from django.db import models
from django.contrib.auth.models import User, Group


class OrganizationManager(models.Manager):


    def get_orgs_administered_by_user(self, user, org_type=None):
        """
        Returns QuerySet of organizations that this user directly or
        indirectly has permission to administrate.
        """
        role_names = [group.name for group in user.groups.all()]

        if not "superadmin" in role_names:
            # Figure out which orgs this user has permission to
            # directly administrate
            qs = self.filter(organizationrole__user=user, organizationrole__group__in=user.groups.all())

            results = self.none()
            # create a union with orgs this user has perm to
            # indirectly administrate
            for org in qs:
                results = results | org.get_descendents(include_self=True)
        else:
            # superadmin can see everything
            results = self.all()

        results = results.filter(deleted=False, active=True)

        results = results.order_by("name")

        results = results.distinct()

        return results


class OrganizationType(models.Model):

    name = models.CharField(max_length=100)


class Organization(models.Model):
    """
    A node in the Organization tree. Many of the methods here are tree
    operations on nodes and subtress. See OrganizationManager for more
    useful, higher-level methods for querying and manipulating
    Organizations.
    """

    name = models.CharField(max_length=100)
    orgtype = models.ForeignKey(OrganizationType)
    active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    objects = OrganizationManager()


    def save(self, *args, **kwargs):
        retval = super(Organization, self).save(*args, **kwargs)

        # storing a relation of depth=0 makes it easier to return a
        # subtree that includes the root node of that subtree
        OrganizationRelation.objects.get_or_create(
            ancestor=self,
            descendent=self,
            depth=0)

        return retval


    def delete(self):
        """
        Overrides parent class's delete() method: we never really
        delete from db, we only set the deleted flag
        """
        for org in self.get_descendents():
            if not org.deleted:
                raise Exception("Cannot call delete() on org that has undeleted descendents")

        self.deleted = True
        self.save()


    def get_ancestors(self, include_self=False):
        """
        Returns a QuerySet of this node's ancestors, ordered by lowest
        depth (top of tree) first
        """
        qs = Organization.objects.filter(
            deleted=False,
            active=True)

        # we pass in kwargs dict in a single filter() call b/c doing
        # it in separate calls results in multiple INNER JOIN clauses
        # in the query, which we don't want
        kwargs = {}
        kwargs['ancestor_rel__descendent'] = self
        if include_self:
            kwargs['ancestor_rel__depth__gte'] = 0
        else:
            kwargs['ancestor_rel__depth__gt'] = 0
        qs = qs.filter(**kwargs)

        qs = qs.order_by("ancestor_rel__depth")

        return qs


    def get_descendents(self, include_self=False):
        """
        Returns a QuerySet of this node's descendents, ordered by lowest
        depth (top of tree) first.
        """
        qs = Organization.objects.filter(
            deleted=False,
            active=True)

        # we pass in kwargs dict in a single filter() call b/c doing
        # it in separate calls results in multiple INNER JOIN clauses
        # in the query, which we don't want
        kwargs = {}
        kwargs['descendent_rel__ancestor'] = self
        if include_self:
            kwargs['descendent_rel__depth__gte'] = 0
        else:
            kwargs['descendent_rel__depth__gt'] = 0
        qs = qs.filter(**kwargs)

        qs = qs.order_by("descendent_rel__depth")

        return qs


    def get_parent(self):
        """
        Returns None if no parent found; if somehow, a bug or data
        corruption caused us to find more than one parent, this raises
        an exception.
        """
        # by their nature, closure tables allow a node to have more
        # than one parent, but we enforce the restriction of exactly 1
        # parent here.
        try:
            return Organization.objects.get(ancestor_rel__descendent=self, ancestor_rel__depth=1)
        except Organization.DoesNotExist:
            return None
        except Organization.MultipleObjectsReturned, e:
            raise Exception("get_parent() found multiple parents for org id=%s, this should never happen: %s" % (self.id, str(e)))
        return None


    def get_children(self):
        """ Returns QuerySet of Organization child nodes """
        return Organization.objects.filter(descendent_rel__ancestor=self, descendent_rel__depth=1, active=True, deleted=False)


    def has_children(self):
        """ Returns True if this node has children, else False """
        return self.get_children().count() > 0


    def add_child(self, child):
        """ Adds a child org to this org, ONLY if it isn't yet a child """

        if not (child in self.get_children()):
            # make child a descendent of all self's ancestors
            for descendent in child.get_descendents(include_self=True):
                for relation in OrganizationRelation.objects.filter(descendent=self):

                    depth_from_subtree_root = \
                        OrganizationRelation.objects.get(ancestor=child, descendent=descendent).depth

                    cloned = OrganizationRelation(
                        ancestor=relation.ancestor,
                        descendent=descendent,
                        depth=relation.depth + depth_from_subtree_root + 1)
                    cloned.save()


    def orphan(self):
        """
        Orphan this node from the tree. Note that this keeps the
        relations of the orphaned subtree intact.
        """
        OrganizationRelation.objects.filter(descendent__in=self.get_descendents(), ancestor__in=self.get_ancestors()).delete()

        OrganizationRelation.objects.filter(descendent=self, depth__gt=0).delete()


    def move(self, new_parent):
        """ Move this node to a new parent in the tree """
        self.orphan()
        new_parent.add_child(self)


    def get_first_ancestor_by_orgtype(self, orgtype):
        """
        Returns the first ancestor ('first' as determined by
        traversing UP the tree) found whose orgtype is the passed-in
        arg.
        """
        qs = self.get_ancestors()
        qs = qs.filter(orgtype=orgtype)
        qs = qs.order_by("-ancestor_rel__depth")
        if qs.count() > 0:
            return qs[0]
        return None


    def get_first_descendent_by_orgtype(self, orgtype):
        """
        Returns the first descendent ('first' as determined by
        traversing DOWN the tree) found whose orgtype is the passed-in
        arg.
        """
        qs = self.get_descendents()
        qs = qs.filter(orgtype=orgtype)
        qs = qs.order_by("ancestor_rel__depth")
        if qs.count() > 0:
            return qs[0]
        return None


class OrganizationRelation(models.Model):
    """
    This is the heart of the "closure table" design: a table storing
    every possible combination of ancestor-descendent relationship.
    (See Bill Karwin's _SQL Antipatterns_ book for a good discussion.)
    Since there are 2 FKs to Organization here, Django requires us to
    use related_name, and writing queries can get a bit
    confusing. Remember, when querying Organizations, join via
    ancestor_rel when you want a final result set of ancestors; ditto
    for descendent_rel.
    """

    ancestor = models.ForeignKey('Organization', related_name='ancestor_rel')
    descendent = models.ForeignKey('Organization', related_name='descendent_rel')
    depth = models.IntegerField()


class OrganizationRole(models.Model):
    """
    Represents a role (ie. a Django auth Group) that a user has, with
    respect to a specific Organization
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    organization = models.ForeignKey(Organization)
