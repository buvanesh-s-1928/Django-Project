"""studio URL routes — page + JSON API surface."""
from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.index, name="index"),

    # Engine
    path("api/generate-plan/", views.generate_plan, name="generate-plan"),
    path("api/copilot/", views.copilot, name="copilot"),

    # Reads
    path("api/blueprints/", views.blueprint_list, name="blueprints"),
    path("api/blueprint/<int:pk>/", views.blueprint_detail, name="blueprint-detail"),
    path("api/catalog/", views.catalog_api, name="catalog"),

    # Pinboard mutations
    path("api/blueprint/<int:pk>/pin/", views.move_pin, name="move-pin"),
    path("api/blueprint/<int:pk>/add-item/", views.add_item_to_room, name="add-item"),
    path("api/blueprint/<int:pk>/remove-pin/", views.remove_pin, name="remove-pin"),

    # Ops
    path("api/reseed/", views.reseed, name="reseed"),
]
