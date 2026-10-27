"""
AURA STAGE // LUMINA STUDIO — Data Models
Four relational tables powering the AI Event Planner & Spatial Budget Engine:

    EventTheme        → category-level budget split ratios (seating/decor/hospitality)
    FurnitureItem     → high-craft catalog with ₹ pricing, footprint, capacity, aesthetics
    EventBlueprint    → user project: room dims, guests, budget, photo, AI summary, run-of-show
    StagedFurniture   → join table pinning catalog items onto a blueprint at (x%, y%)

SQLite-friendly, zero third-party dependencies. Room photos use FileField
(so Pillow is never required).
"""
import json

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


# ===================================================================== #
#  1. EventTheme — mood archetypes with budget DNA                      #
# ===================================================================== #
class EventTheme(models.Model):
    """An event archetype that dictates how the ₹ budget is sliced."""

    class Vibe(models.TextChoices):
        WARM = "warm", "Warm Cream"
        ROYAL = "royal", "Royal Blue"
        NEUTRAL = "neutral", "Swiss Neutral"
        GOLDEN = "golden", "Golden Hour"
        VERDANT = "verdant", "Verdant Garden"

    code = models.SlugField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=80)
    tagline = models.CharField(max_length=160, blank=True)
    vibe = models.CharField(max_length=16, choices=Vibe.choices, default=Vibe.WARM)
    accent_hex = models.CharField(max_length=9, default="#1E3A8A")

    # Budget split ratios — must sum to ~1.0 (validated on save).
    seating_ratio = models.DecimalField(max_digits=4, decimal_places=3, default=0.50)
    decor_ratio = models.DecimalField(max_digits=4, decimal_places=3, default=0.30)
    hospitality_ratio = models.DecimalField(max_digits=4, decimal_places=3, default=0.20)

    description = models.TextField(blank=True)
    is_showcase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Event Theme"
        verbose_name_plural = "Event Themes"

    def __str__(self):
        return f"{self.name} [{self.code}] · {self.budget_split_pct()}"

    def budget_split_pct(self):
        return (
            f"{int(self.seating_ratio * 100)}% seat / "
            f"{int(self.decor_ratio * 100)}% decor / "
            f"{int(self.hospitality_ratio * 100)}% hosp."
        )

    def ratio_map(self):
        """Category → share of budget, consumed by the Knapsack optimizer."""
        return {
            "seating": float(self.seating_ratio),
            "decor": float(self.decor_ratio),
            "hospitality": float(self.hospitality_ratio),
            "lighting": float(self.decor_ratio) * 0.45,  # carved out of decor
        }

    def clean(self):
        super().clean()
        total = self.seating_ratio + self.decor_ratio + self.hospitality_ratio
        if abs(float(total) - 1.0) > 0.02:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "Budget split ratios must sum to 1.00 (got "
                f"{total:.2f})."
            )


# ===================================================================== #
#  2. FurnitureItem — the high-craft spatial catalog                    #
# ===================================================================== #
class FurnitureItem(models.Model):
    """A real, pinnable product with price, physical footprint and aura score."""

    class Category(models.TextChoices):
        SEATING = "seating", "Seating"
        DECOR = "decor", "Decor"
        LIGHTING = "lighting", "Lighting"
        HOSPITALITY = "hospitality", "Hospitality"

    sku = models.CharField(max_length=24, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.DECOR, db_index=True
    )
    price_inr = models.DecimalField(
        max_digits=9, decimal_places=2, validators=[MinValueValidator(1)]
    )
    footprint_sqft = models.DecimalField(max_digits=7, decimal_places=2, default=6)
    guest_capacity = models.PositiveSmallIntegerField(default=2)
    aesthetic_score = models.FloatField(default=7.5)  # 0–10 editorial rating
    material = models.CharField(max_length=80, blank=True)
    palette_tag = models.CharField(max_length=40, blank=True)
    theme_codes = models.CharField(
        max_length=160, blank=True, help_text="CSV of EventTheme.codes this item suits."
    )
    blurb = models.CharField(max_length=220, blank=True)
    in_stock = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "-aesthetic_score", "price_inr"]
        indexes = [models.Index(fields=["category", "price_inr"])]
        verbose_name = "Furniture Item"
        verbose_name_plural = "Furniture Catalog"

    def __str__(self):
        return f"{self.sku} · {self.name} ₹{self.price_inr:,.0f}"

    def value_density(self):
        """Aesthetic payoff per rupee — the knapsack 'utility' signal."""
        price = float(self.price_inr) or 1.0
        return round(self.aesthetic_score / price * 1000, 3)

    def suits_theme(self, theme_code: str) -> bool:
        codes = [c.strip() for c in self.theme_codes.split(",") if c.strip()]
        return (not codes) or (theme_code in codes)


# ===================================================================== #
#  3. EventBlueprint — the user's spatial project                       #
# ===================================================================== #
def room_photo_upload_to(instance, filename):
    safe = "".join(ch for ch in filename if ch.isalnum() or ch in "._-")[:48]
    return f"room_photos/{timezone.now():%Y%m%d}_{instance.pk or 'new'}_{safe}"


class EventBlueprint(models.Model):
    """A saved stage plan: room dimensions, guest load, ₹ budget, photo + AI output."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        STAGED = "staged", "AI Staged"
        LOCKED = "locked", "Budget Locked"

    title = models.CharField(max_length=140)
    theme = models.ForeignKey(
        EventTheme, on_delete=models.PROTECT, related_name="blueprints"
    )
    host_name = models.CharField(max_length=120, blank=True, default="")
    event_date = models.DateField(null=True, blank=True)

    # Spatial inputs
    room_width_ft = models.DecimalField(max_digits=6, decimal_places=1, default=14)
    room_depth_ft = models.DecimalField(max_digits=6, decimal_places=1, default=16)
    guest_count = models.PositiveSmallIntegerField(default=24)

    # Money
    budget_inr = models.DecimalField(
        max_digits=11, decimal_places=2, validators=[MinValueValidator(1000)]
    )
    spent_inr = models.DecimalField(max_digits=11, decimal_places=2, default=0)

    # Room photograph — FileField keeps us Pillow-free.
    room_photo = models.FileField(
        upload_to=room_photo_upload_to, null=True, blank=True, max_length=255
    )
    photo_width_px = models.PositiveIntegerField(null=True, blank=True)
    photo_height_px = models.PositiveIntegerField(null=True, blank=True)

    # Engine outputs
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    ai_summary = models.TextField(
        blank=True, help_text="Gemini Vision spatial audit or offline heuristic narrative."
    )
    ai_engine = models.CharField(max_length=40, blank=True, default="knapsack-local")
    run_of_show = models.JSONField(
        default=list, blank=True, help_text="Chronological timeline as JSON list."
    )
    is_showcase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Event Blueprint"
        verbose_name_plural = "Event Blueprints"

    def __str__(self):
        return f"{self.title} · ₹{self.budget_inr:,.0f} · {self.guest_count} guests"

    @property
    def room_area_sqft(self):
        return round(float(self.room_width_ft) * float(self.room_depth_ft), 1)

    @property
    def budget_headroom(self):
        return float(self.budget_inr) - float(self.spent_inr)

    @property
    def overrun(self) -> bool:
        return self.budget_headroom < 0

    def run_of_show_list(self):
        raw = self.run_of_show
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (ValueError, TypeError):
                raw = []
        return raw if isinstance(raw, list) else []

    def recalc_spent(self, commit=True):
        """Recompute spent_inr from staged furniture — Zero Overrun invariant."""
        agg = self.staged_set.aggregate(total=models.Sum("line_total"))
        self.spent_inr = agg["total"] or 0
        if not self.overrun and self.staged_set.exists():
            self.status = self.Status.LOCKED if self.budget_headroom < 500 else self.Status.STAGED
        if commit:
            self.save(update_fields=["spent_inr", "status", "updated_at"])


# ===================================================================== #
#  4. StagedFurniture — items pinned onto the room photo                #
# ===================================================================== #
class StagedFurniture(models.Model):
    """Relational join placing a catalog item at (pin_x_pct, pin_y_pct) on a blueprint."""

    blueprint = models.ForeignKey(
        EventBlueprint, on_delete=models.CASCADE, related_name="staged_set"
    )
    item = models.ForeignKey(
        FurnitureItem, on_delete=models.PROTECT, related_name="placements"
    )
    pin_x_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=50,
        validators=[MinValueValidator(0)],
        help_text="Horizontal pin position, 0–100% of photo width.",
    )
    pin_y_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=50,
        validators=[MinValueValidator(0)],
        help_text="Vertical pin position, 0–100% of photo height.",
    )
    quantity = models.PositiveSmallIntegerField(default=1)
    line_total = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    placed_by = models.CharField(
        max_length=24, default="aura-engine",
        help_text="'aura-engine' for AI placement, 'manual' for user drag/pins.",
    )
    note = models.CharField(max_length=160, blank=True)
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pin_y_pct", "pin_x_pct"]
        verbose_name = "Staged Furniture Pin"
        verbose_name_plural = "Staged Furniture Pins"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pin_x_pct__lte=100) & models.Q(pin_y_pct__lte=100),
                name="aura_pin_within_photo_bounds",
            ),
            models.UniqueConstraint(
                fields=["blueprint", "item"], name="aura_one_pin_per_item_per_room"
            ),
        ]

    def __str__(self):
        return (
            f"📍 {self.item.name} @ ({self.pin_x_pct}%, {self.pin_y_pct}%) "
            f"×{self.quantity} → ₹{self.line_total:,.0f}"
        )

    def save(self, *args, **kwargs):
        self.line_total = self.item.price_inr * self.quantity
        super().save(*args, **kwargs)
