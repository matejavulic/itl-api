from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    url(r'^exec/$', views.Compile.as_view()), #.../compile/exec // call the dispatch() method to map request to get() or post() mthd
    
]
