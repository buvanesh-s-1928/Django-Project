"""
AURA STAGE // LUMINA STUDIO — Database Seeding
seed_aura_db(): idempotent first-launch population of themes, the 16-item
high-craft furniture catalog (₹1,500–₹16,500), and two showcase blueprints.

Invoked automatically from studio.apps.StudioConfig.ready() and exposed as
`python manage.py seed_aura`. All writes are guarded so migrate/runserver/
test runs never crash on a missing table or concurrent worker.
"""
import logging

logger = logging.getLogger("studio")

# ------------------------------------------------------------------ #
#  Default Event Themes                                               #
# ------------------------------------------------------------------ #
THEME_SEEDS = [
    {
        "code": "royal-reception",
        "name": "Royal Reception",
        "tagline": "Cobalt grandeur for the formal arrival.",
        "vibe": "royal",
        "accent_hex": "#1E3A8A",
        "seating_ratio": 0.50, "decor_ratio": 0.30, "hospitality_ratio": 0.20,
        "description": (
            "Deep royal-blue upholstery, brass-lit centrepieces and cream linen. "
            "Built for dignitary welcomes, product launches and gallery openings."
        ),
    },
    {
        "code": "warm-cream-soiree",
        "name": "Warm Cream Soirée",
        "tagline": "Editorial calm, candle-warm and intimate.",
        "vibe": "warm",
        "accent_hex": "#B45309",
        "seating_ratio": 0.45, "decor_ratio": 0.35, "hospitality_ratio": 0.20,
        "description": (
            "Ivory bouclé, jute textures and honey-toned lighting for house "
            "soirées, baby showers and slow-dinner gatherings."
        ),
    },
    {
        "code": "golden-mandap",
        "name": "Golden Mandap",
        "tagline": "Marigold-weight tradition with modern staging.",
        "vibe": "golden",
        "accent_hex": "#CA8A04",
        "seating_ratio": 0.55, "decor_ratio": 0.30, "hospitality_ratio": 0.15,
        "description": (
            "Sagai, haldi and reception staging: guldavris, brass diya stands "
            "and low floor seating with generous chai-and-mitha hospitality."
        ),
    },
    {
        "code": "verdant-veranda",
        "name": "Verdant Veranda",
        "tagline": "Garden-fresh brunch under leaf-light.",
        "vibe": "verdant",
        "accent_hex": "#15803D",
        "seating_ratio": 0.40, "decor_ratio": 0.35, "hospitality_ratio": 0.25,
        "description": (
            "Potted canopy greenery, rattan lounge clusters and long-table "
            "brunch service for daytime rooftop and lawn events."
        ),
    },
    {
        "code": "swiss-neutral",
        "name": "Swiss Neutral",
        "tagline": "Minimal grid. Maximum composure.",
        "vibe": "neutral",
        "accent_hex": "#334155",
        "seating_ratio": 0.50, "decor_ratio": 0.25, "hospitality_ratio": 0.25,
        "description": (
            "Monochrome boardroom-to vernissage conversion: modular desks, "
            "track lighting and still-water coffee stations."
        ),
    },
]

# ------------------------------------------------------------------ #
#  16 high-craft furniture items — ₹1,500 to ₹16,500                  #
# ------------------------------------------------------------------ #
ITEM_SEEDS = [
    # ---- SEATING -------------------------------------------------
    {"sku": "AUR-ST-001", "name": "Lumina Velvet Lounge Chair", "category": "seating",
     "price_inr": 12500, "footprint_sqft": 9, "guest_capacity": 1, "aesthetic_score": 9.4,
     "material": "Royal-blue velvet · solid teak frame", "palette_tag": "cobalt/teak",
     "theme_codes": "royal-reception,warm-cream-soiree,swiss-neutral",
     "blurb": "Deep-buttoned lounge chair; the anchor silhouette of any staged corner."},
    {"sku": "AUR-ST-002", "name": "Bouclé Modular Sofa Bay (3-seat)", "category": "seating",
     "price_inr": 16500, "footprint_sqft": 24, "guest_capacity": 3, "aesthetic_score": 9.1,
     "material": "Ivory bouclé · powder-coated steel plinth", "palette_tag": "cream",
     "theme_codes": "warm-cream-soiree,swiss-neutral,royal-reception",
     "blurb": "Three-seat cloud bay; reconfigurable modules for L-shaped conversation zones."},
    {"sku": "AUR-ST-003", "name": "Banquet Chiavari Chair (pair)", "category": "seating",
     "price_inr": 3400, "footprint_sqft": 4, "guest_capacity": 2, "aesthetic_score": 7.8,
     "material": "Beechwood · gold finish + ivory pad", "palette_tag": "gold/ivory",
     "theme_codes": "golden-mandap,royal-reception,warm-cream-soiree",
     "blurb": "Classic wedding-line seating, cushioned and stackable between acts."},
    {"sku": "AUR-ST-004", "name": "Rattan Veranda Loveseat", "category": "seating",
     "price_inr": 9800, "footprint_sqft": 14, "guest_capacity": 2, "aesthetic_score": 8.6,
     "material": "Hand-woven natural rattan", "palette_tag": "sand/olive",
     "theme_codes": "verdant-veranda,warm-cream-soiree",
     "blurb": "Airy two-seater for balcony and lawn edges; pairs with leaf-shadow light."},
    {"sku": "AUR-ST-005", "name": "Gulmohar Floor Cushion Set (×6)", "category": "seating",
     "price_inr": 5400, "footprint_sqft": 18, "guest_capacity": 6, "aesthetic_score": 8.2,
     "material": "Kantha-stitched cotton · stuffed", "palette_tag": "marigold/crimson",
     "theme_codes": "golden-mandap,verdant-veranda",
     "blurb": "Low-floor antha seating cluster for haldi circles and ghazal nights."},
    # ---- DECOR ---------------------------------------------------
    {"sku": "AUR-DC-006", "name": "Brass Centrepiece Trio", "category": "decor",
     "price_inr": 4200, "footprint_sqft": 2, "guest_capacity": 0, "aesthetic_score": 8.9,
     "material": "Hand-cast brass, unlacquered", "palette_tag": "brass",
     "theme_codes": "golden-mandap,royal-reception,warm-cream-soiree",
     "blurb": "Graduated table towers that catch candlelight across the room axis."},
    {"sku": "AUR-DC-007", "name": "Ivory Linen Table Runner (3 m)", "category": "decor",
     "price_inr": 1500, "footprint_sqft": 1, "guest_capacity": 0, "aesthetic_score": 7.4,
     "material": "Washed European linen", "palette_tag": "cream",
     "theme_codes": "warm-cream-soiree,swiss-neutral,verdant-veranda",
     "blurb": "The quiet editorial line beneath every long table; wrinkle-positive by design."},
    {"sku": "AUR-DC-008", "name": "Arch-Wire Frame Backdrop Panel", "category": "decor",
     "price_inr": 11200, "footprint_sqft": 16, "guest_capacity": 0, "aesthetic_score": 9.3,
     "material": "Matte-black welded wire arch", "palette_tag": "graphite",
     "theme_codes": "swiss-neutral,royal-reception,golden-mandap",
     "blurb": "Signature arched trellis wall — photo moment and stage spine in one object."},
    {"sku": "AUR-DC-009", "name": "Potted Canopy Greenery (Fiddle ×2)", "category": "decor",
     "price_inr": 3800, "footprint_sqft": 6, "guest_capacity": 0, "aesthetic_score": 8.0,
     "material": "Live ficus lyrata · terracotta vessel", "palette_tag": "green/terracotta",
     "theme_codes": "verdant-veranda,warm-cream-soiree",
     "blurb": "Two-metre leaf columns that soften corners and lift perceived air quality."},
    {"sku": "AUR-DC-010", "name": "Marigold & Tuberosa Garland Strand", "category": "decor",
     "price_inr": 2600, "footprint_sqft": 3, "guest_capacity": 0,
     "aesthetic_score": 8.5, "material": "Fresh-season hand-strung flowers",
     "palette_tag": "marigold/white", "theme_codes": "golden-mandap,verdant-veranda",
     "blurb": "4-m torana strand for doorways, mandap rails or buffet fronts."},
    # ---- LIGHTING ------------------------------------------------
    {"sku": "AUR-LT-011", "name": "Edison Halo Pendant Cluster", "category": "lighting",
     "price_inr": 7600, "footprint_sqft": 4, "guest_capacity": 0, "aesthetic_score": 9.2,
     "material": "Amber glass · braided cord (5-drop)", "palette_tag": "amber/black",
     "theme_codes": "warm-cream-soiree,golden-mandap,royal-reception",
     "blurb": "Suspended filament constellation; warms any ceiling plane at 2200K."},
    {"sku": "AUR-LT-012", "name": "Brass Diya Stand Ring (set of 8)", "category": "lighting",
     "price_inr": 2200, "footprint_sqft": 2, "guest_capacity": 0, "aesthetic_score": 8.3,
     "material": "Turned brass · oil-wick", "palette_tag": "brass/flame",
     "theme_codes": "golden-mandap,warm-cream-soiree",
     "blurb": "Ground-flame perimeter ring — the cheapest aura-per-rupee item in the catalog."},
    {"sku": "AUR-LT-013", "name": "Cryo Track Light Bar (2 m)", "category": "lighting",
     "price_inr": 9400, "footprint_sqft": 3, "guest_capacity": 0, "aesthetic_score": 8.7,
     "material": "Anodised aluminium · 3000K heads", "palette_tag": "ice/graphite",
     "theme_codes": "swiss-neutral,royal-reception",
     "blurb": "Gallery-grade wash lighting; aims art, speakers and signature walls."},
    # ---- HOSPITALITY ---------------------------------------------
    {"sku": "AUR-HO-014", "name": "Chai & Coffee Service Cart", "category": "hospitality",
     "price_inr": 8800, "footprint_sqft": 8, "guest_capacity": 0, "aesthetic_score": 8.4,
     "material": "Reclaimed teak trolley · brass rails", "palette_tag": "walnut/brass",
     "theme_codes": "golden-mandap,warm-cream-soiree,swiss-neutral,royal-reception,verdant-veranda",
     "blurb": "Rolling hospitality bar; keeps the queue moving without a fixed counter."},
    {"sku": "AUR-HO-015", "name": "Long-Table Brunch Spread Kit (12 covers)", "category": "hospitality",
     "price_inr": 6600, "footprint_sqft": 10, "guest_capacity": 12, "aesthetic_score": 7.9,
     "material": "Stoneware crocks · slate boards · linen napkins", "palette_tag": "stone/sage",
     "theme_codes": "verdant-veranda,warm-cream-soiree",
     "blurb": "Shared-platter kit sized for a twelve-cover Sunday veranda brunch."},
    {"sku": "AUR-HO-016", "name": "Mitha & High-Tea Display Tier", "category": "hospitality",
     "price_inr": 4900, "footprint_sqft": 3, "guest_capacity": 0, "aesthetic_score": 8.1,
     "material": "Three-tier brushed-steel stand", "palette_tag": "silver",
     "theme_codes": "royal-reception,golden-mandap,swiss-neutral",
     "blurb": "Vertical sweet-and-savoury tier; feeds four times the guests in a third of the table."},
]

# Clean up an accidental typo key before use.
for _seed in ITEM_SEEDS:
    _seed.pop("footprint_sqf", None)


def seed_aura_db(force=False):
    """Populate default themes, the 16-item catalog and 2 showcase blueprints.

    Idempotent: safe to call on every boot. Returns a small report dict.
    """
    from datetime import date, timedelta

    from .models import EventBlueprint, EventTheme, FurnitureItem, StagedFurniture

    report = {"themes": 0, "items": 0, "blueprints": 0, "skipped": False}

    if not force and EventTheme.objects.exists() and FurnitureItem.objects.exists():
        report["skipped"] = True
        return report

    # ── Themes ────────────────────────────────────────────────────
    for payload in THEME_SEEDS:
        obj, created = EventTheme.objects.update_or_create(
            code=payload["code"], defaults=payload
        )
        if created:
            report["themes"] += 1

    # ── Catalog ───────────────────────────────────────────────────
    for payload in ITEM_SEEDS:
        obj, created = FurnitureItem.objects.update_or_create(
            sku=payload["sku"], defaults=payload
        )
        if created:
            report["items"] += 1

    # ── Showcase blueprints ───────────────────────────────────────
    def _stage(bp_code, theme_code, title, host, budget, guests, w, d,
               picks, summary, ros_start="17:00"):
        """Create/update a showcase blueprint with pinned items (zero overrun)."""
        theme = EventTheme.objects.get(code=theme_code)
        bp, created = EventBlueprint.objects.update_or_create(
            title=title,
            defaults={
                "theme": theme, "host_name": host,
                "event_date": date.today() + timedelta(days=21),
                "room_width_ft": w, "room_depth_ft": d,
                "guest_count": guests, "budget_inr": budget,
                "status": EventBlueprint.Status.STAGED,
                "ai_engine": "knapsack-local",
                "ai_summary": summary,
                "is_showcase": True,
            },
        )
        bp.run_of_show = _default_run_of_show(bp, ros_start)
        bp.save(update_fields=["run_of_show"])

        StagedFurniture.objects.filter(blueprint=bp).delete()
        for sku, qty, x, y, note in picks:
            item = FurnitureItem.objects.get(sku=sku)
            StagedFurniture.objects.create(
                blueprint=bp, item=item, quantity=qty,
                pin_x_pct=x, pin_y_pct=y, note=note, placed_by="aura-engine",
            )
        bp.recalc_spent(commit=True)
        return bp, created

    # NOTE: every pick-set below is pre-verified for ZERO BUDGET OVERRUN.
    _stage(
        "showcase-royal", "royal-reception",
        "Showcase · Cobalt Courtyard Reception", "Indira Mehra",
        budget=60000, guests=28, w=18, d=22,
        picks=[
            ("AUR-ST-002", 1, 26.0, 62.0, "Anchor sofa bay against the north wall"),
            ("AUR-ST-003", 3, 70.0, 55.0, "Chiavari rows facing arrival axis"),
            ("AUR-DC-008", 1, 50.0, 22.0, "Arch backdrop on focal wall"),
            ("AUR-DC-006", 1, 40.0, 70.0, "Brass trio centrepiece on the head table"),
            ("AUR-LT-011", 1, 50.0, 10.0, "Halo cluster over lounge core"),
            ("AUR-HO-014", 1, 88.0, 40.0, "Chai cart at east service door"),
        ],
        summary=(
            "OFFLINE HEURISTIC AUDIT — 18 ft × 22 ft courtyard reads as a "
            "double-axis room: arrival path runs east→west, lounge core sits "
            "north. The knapsack engine allocated 50% seating / 30% decor / "
            "20% hospitality, landing ₹58,500 of ₹60,000 (₹1,500 contingency "
            "headroom, zero overrun). Sightlines clear at 32-inch pin heights; "
            "the arch backdrop anchors photography at the room's vanishing "
            "point."
        ),
    )

    _stage(
        "showcase-soiree", "warm-cream-soiree",
        "Showcase · Cream Loft Soirée", "Kabir Anand",
        budget=35000, guests=14, w=14, d=16,
        picks=[
            ("AUR-ST-001", 1, 30.0, 66.0, "Velvet lounge chair at the bay window"),
            ("AUR-DC-007", 2, 52.0, 74.0, "Runners on console + brunch table"),
            ("AUR-DC-009", 1, 90.0, 35.0, "Leaf column softening the NE corner"),
            ("AUR-LT-011", 1, 45.0, 12.0, "Halo pendant over the dining line"),
            ("AUR-LT-012", 1, 18.0, 82.0, "Diya ring on the entry threshold"),
            ("AUR-HO-016", 1, 72.0, 48.0, "Mitha tier at the tea station"),
        ],
        summary=(
            "OFFLINE HEURISTIC AUDIT — 14 ft × 16 ft loft with strong west "
            "daylight. Engine weighted comfort over spectacle: 45% seating, "
            "35% decor (incl. lighting carve-out), 20% hospitality. Total "
            "staged ₹34,000 of ₹35,000 (₹1,000 headroom, zero overrun). "
            "Warm-cream palette tags dominate; ground-flame diyas offset "
            "cool window glare after sunset."
        ),
        ros_start="18:30",
    )
    report["blueprints"] = 2

    logger.info("AURA seed complete → %s", report)
    return report


def _default_run_of_show(bp, start="17:00"):
    """Chronological run-of-show JSON built around guest count + theme."""
    hh, mm = map(int, start.split(":"))
    total_min = hh * 60 + mm

    def at(offset):
        t = total_min + offset
        return f"{(t // 60) % 24:02d}:{t % 60:02d}"

    vibe_line = {
        "royal-reception": "Welcome address & champagne toast",
        "warm-cream-soiree": "Candle-light circle & host remarks",
        "golden-mandap": "Aarti, garland exchange & pheras",
        "verdant-veranda": "Long-table brunch & garden games",
        "swiss-neutral": "Keynote, demo floor & curator walkthrough",
    }.get(bp.theme.code, "Host welcome & program opening")

    return [
        {"time": at(0),   "title": "Doors & Room Wake",
         "detail": "Lighting at 40%, staff spot-check of every pinned position."},
        {"time": at(30),  "title": "Guest Arrival",
         "detail": f"Chai/coffee cart live; {bp.guest_count} covers expected within 25 min."},
        {"time": at(60),  "title": vibe_line,
         "detail": "Track/Halo lighting to performance scene; photographer at arch backdrop."},
        {"time": at(95),  "title": "Table Reveal & Feast",
         "detail": "Hospitality pins go active; runner alignment check at each station."},
        {"time": at(140), "title": "Golden-Hour Interlude",
         "detail": "Diya/pendant dimming curve; ambient set for candid frames."},
        {"time": at(170), "title": "Closing & Send-off",
         "detail": "Inventory sweep of all staged SKUs; breakdown order per footprint size."},
    ]


# ------------------------------------------------------------------ #
#  Boot-safe wrapper used by AppConfig.ready()                        #
# ------------------------------------------------------------------ #
def ensure_aura_seed():
    """Call seed only when the schema is actually present and DB is SQLite."""
    import os
    import sys

    from django.conf import settings
    from django.db import OperationalError, connection

    # Skip during bare utility commands where seeding would be noise.
    if any(arg in ("makemigrations", "migrate --check", "collectstatic",
                   "flush", "test") for arg in sys.argv):
        return
    if os.environ.get("AURA_SKIP_SEED") == "1":
        return
    if connection.vendor != "sqlite":
        return

    try:
        table_names = set(connection.introspection.table_names())
        if "studio_eventtheme" not in table_names:
            return  # migrations not applied yet
        seed_aura_db()
    except (OperationalError, Exception) as exc:  # noqa: BLE001 — boot must never die
        logger.warning("AURA auto-seed skipped: %s", exc)
