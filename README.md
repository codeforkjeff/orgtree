orgtree
=======

Django app demonstrating an organization tree implemented using a closure table design

Background
----------

A good discussion of closure tables can be found in Bill Karwin's book, [SQL Antipatterns](http://pragprog.com/book/bksqla/sql-antipatterns). An article by Vipin Raj on this design can also be found [here](http://http://technobytz.com/closure_table_store_hierarchical_data.html).

In a nutshell, this design makes it particularly easy to fetch a subtree in a single query. In contrast, the more typical "naive" approach of storing a foreign key to the node's parent in each record requires recursion and a query per node traversal. Closure tables are much more performant for deep trees, the main drawback being the large table containing all ancestor-descendent relationships.

The code in this repository is a simplified, more generic version of code I wrote for a work project. It doesn't contain any views or user interfaces, only a models.py file and tests.py to demonstrate usage.


Installation
------------

It's easy and quick to install this code as a Django app and use it or experiment with it, but this repository is intended primarily to be an illustration of how an unusual database design can be implemented within the Django framework. It's not meant to be a full-featured app, so if you use it for any serious projects, you should expect to have to adapt it to your own purposes.

If you don't already have a Django project in which to stick this app, make one:

    django-admin.py startproject orgtreeproj

Change your working directory to the project:

    cd orgtreeproj

Clone this repository:

    git clone git clone git@github.com:codeforkjeff/orgtree.git
    
Edit your settings file (in our case, orgtreeproject/settings.py) and add orgtree to the list of installed apps:

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # add this next line to whatever's already in INSTALLED_APPS
        'orgtree',
    )

Now you are ready to use the models in your own app. It's useful to look at the test suite and experiment with that code as well:

    ./manage.py test orgtree
