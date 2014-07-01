orgtree
=======

Django app demonstrating an organization tree implemented using a closure table design

Background
----------

A good discussion of closure tables can be found in Bill Karwin's book, [SQL Antipatterns](http://pragprog.com/book/bksqla/sql-antipatterns). In a nutshell, this design makes it easy to fetch a subtree from the tree in a single query, without having to use recursion, as is the case with the more typical "naive" approach of storing a foreign key to a parent in each node record.

The code in this repository is a simplified, more generic version of code I wrote for a work project.

Installation
------------

This code is best used for illustration purposes, but it you can easily install it as a Django app to play with it and see how it works.

If you don't already have a Django project, make one:

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

You can now use the code in your own app. It's useful to run the tests and experiment with them as well:

    ./manage.py test orgtree
