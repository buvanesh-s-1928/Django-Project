"""
AURA STAGE // LUMINA STUDIO — Admin Console
Full CRUD with StagedFurnitureInline embedded inside EventBlueprintAdmin.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import EventBlueprint, EventTheme, FurnitureItem, StagedFurniture


# ------------------------------------------------------------------ #
#  Inline: pin furniture directly inside the blueprint editor         #
# ------------------------------------------------------------------ #
class StagedFurnitureInline(admin.TabularInline):
    model = StagedFurniture
    extra = 1
    autocomplete_fields = ["item"]
    fields = ("item", "quantity", "pin_x_pct", "pin_y_pct", "line_total", "placed_by", "note")
    readonly_fields = ("line_total",)

    @admin.display(description="Line ₹")
    def line_rupee(self, obj):
        return f"₹{obj.line_total:,.0f}"


@admin.register(EventTheme)
class EventThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "vibe", "budget_split_pct", "accent_swatch", "is_showcase")
    list_filter = ("vibe", "is_showcase")
    search_fields = ("code", "name", "tagline")
    prepopulated_fields = {"code": ("name",)}
    readonly_fields = ("created_at",)

    @admin.display(description="Accent")
    def accent_swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:22px;height:22px;border-radius:6px;'
            'background:{};border:1px solid #cbd5e1"></span>',
            obj.accent_hex,
        )


@admin.register(FurnitureItem)
class FurnitureItemAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "price_rupee", "footprint_sqft",
                    "guest_capacity", "aesthetic_score", "value_density_short", "in_stock")
    list_filter = ("category", "in_stock")
    search_fields = ("sku", "name", "material", "palette_tag")
    ordering = ("category", "-aesthetic_score")

    @admin.display(description="Price ₹", ordering="price_inr")
    def price_rupee(self, obj):
        return format_html("<b>₹{:,.0f}</b>", obj.price_inr)

    @admin.display(description="Value/₹")
    def value_density_short(self, obj):
        return obj.value_density()


@admin.register(EventBlueprint)
class EventBlueprintAdmin(admin.ModelAdmin):
    list_display = ("title", "theme", "guest_count", "budget_rupee", "spent_rupee",
                    "headroom_flag", "status", "engine_badge", "created_at")
    list_filter = ("status", "theme", "is_showcase")
    search_fields = ("title", "host_name")
    autocomplete_fields = ["theme"]
    inlines = [StagedFurnitureInline]
    readonly_fields = ("spent_inr", "ai_engine", "created_at", "updated_at", "photo_preview")
    fieldsets = (
        ("Identity", {"fields": ("title", "theme", "host_name", "event_date", "is_showcase")}),
        ("Spatial Inputs", {"fields": ("room_width_ft", "room_depth_ft", "guest_count")}),
        ("Money", {"fields": ("budget_inr", "spent_inr", "status")}),
        ("Room Photograph", {"fields": ("room_photo", "photo_url_remote",
                                        "photo_source", "photo_preview",
                                        "photo_width_px", "photo_height_px")}),
        ("AI Engine Output", {"fields": ("ai_engine", "ai_summary", "run_of_show")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Budget ₹", ordering="budget_inr")
    def budget_rupee(self, obj):
        return f"₹{obj.budget_inr:,.0f}"

    @admin.display(description="Spent ₹", ordering="spent_inr")
    def spent_rupee(self, obj):
        return f"₹{obj.spent_inr:,.0f}"

    @admin.display(description="Zero-Overrun")
    def headroom_flag(self, obj):
        if obj.overrun:
            return format_html('<span style="color:#b91c1c">▲ OVERSPENT</span>')
        return format_html(
            '<span style="color:#15803d">✔ ₹{:,.0f} headroom</span>', obj.budget_headroom
        )

    @admin.display(description="Engine")
    def engine_badge(self, obj):
        return format_html(
            '<code style="background:#eef2ff;padding:2px 6px;border-radius:4px">{}</code>',
            obj.ai_engine or "—",
        )

    @admin.display(description="Preview")
    def photo_preview(self, obj):
        url = obj.photo_display_url
        if url:
            return format_html(
                '<img src="{}" style="max-width:320px;border-radius:12px;'
                'border:1px solid #cbd5e1"/>', url
            )
        return "No photograph uploaded."

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalc_spent(commit=True)


@admin.register(StagedFurniture)
class StagedFurnitureAdmin(admin.ModelAdmin):
    list_display = ("__str__", "blueprint", "item", "quantity", "line_total", "placed_by")
    list_filter = ("placed_by",)
    search_fields = ("item__name", "item__sku", "blueprint__title")
    autocomplete_fields = ("blueprint", "item")
