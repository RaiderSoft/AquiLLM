from . import models
import functools


# returns a list of objects, not a queryset!
def get_user_accessible_documents(user, collections=None, perm='VIEW'):

    if collections is None:
        collections = models.Collection.objects.all()

    collections = collections.filter_by_user_perm(user, perm)
    documents = functools.reduce(lambda l, r: l + r, [list(x.objects.filter(collection__in=collections)) for x in models.DESCENDED_FROM_DOCUMENT])
    return documents
