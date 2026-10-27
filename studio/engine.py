"""
AURA STAGE // LUMINA STUDIO — The Budget-Matching Engine
=========================================================
Two cooperating brains:

1. `gemini_vision_audit()`  — optional Google AI Studio Vision call to
   `gemini-2.5-flash` via stdlib urllib ONLY (no requests / google SDK).
   Reads the uploaded room photograph, returns a spatial narrative +
   placement hints as JSON.

2. `knapsack_optimize()`    — deterministic local optimizer that ALWAYS
   runs and guarantees ZERO BUDGET OVERRUN:
     • bounded multi-choice knapsack over the SQLite catalog
     • theme-driven category budget envelopes (seating/decor/hospitality)
     • guest-capacity coverage target + footprint fit against room area
     • utility = aesthetic score × value density, so every rupee buys aura
     • spatial pin allocator spreads survivors across photo quadrants

If Gemini is unavailable (no key / offline / bad JSON), a robust heuristic
narrative is generated locally instead. The plan NEVER fails.
"""
from __future__ import annotations

import base64
import json
import logging
import math
import re
import urllib.error
import urllib.request
from decimal import Decimal

from django.conf import settings

from .models import EventBlueprint, EventTheme, FurnitureItem, StagedFurniture

logger = logging.getLogger("studio")

CATEGORY_ORDER = ["seating", "decor", "lighting", "hospitality"]


# ====================================================================== #
#  1. GEMINI VISION (stdlib urllib)                                       #
# ====================================================================== #
GEMINI_SYSTEM_PROMPT = """You are AURA, the spatial director inside LUMINA STUDIO.
You will receive ONE photograph of an Indian home event space plus structured
inputs (room size, guests, ₹ budget, theme). Respond with STRICT JSON only:
{
  "summary": "<3-5 sentence editorial spatial audit of the photo: light, depth, focal wall, traffic axis, ceiling>",
  "focal_wall_pct": {"x": <0-100>, "y": <0-100>},
  "traffic_axis": "<e-w|n-s|diagonal-ne-sw|diagonal-nw-se|central-island>",
  "light_read": "<bright-daylight|mixed|dim-warm|dim-cool>",
  "risk_notes": ["<max 2 short staging risks>"]
}
No markdown fences, no commentary outside the JSON object."""


def gemini_vision_audit(blueprint: EventBlueprint, api_key: str) -> dict | None:
    """Query gemini-2.5-flash with the room photo. Returns parsed dict or None.

    Uses only urllib/json/base64 — zero installs. Any network/parse failure
    returns None so the caller falls back to the offline heuristic.
    """
    if not api_key or not blueprint.room_photo:
        return None

    try:
        with blueprint.room_photo.open("rb") as fh:
            raw = fh.read()
    except OSError as exc:
        logger.warning("AURA: cannot read room photo: %s", exc)
        return None

    # Cap payload at ~3.5 MB base64 to stay under request limits.
    if len(raw) > 2_600_000:
        return None

    mime = "image/jpeg"
    lowered = blueprint.room_photo.name.lower()
    if lowered.endswith(".png"):
        mime = "image/png"
    elif lowered.endswith(".webp"):
        mime = "image/webp"

    context = (
        f"ROOM: {blueprint.room_width_ft}ft x {blueprint.room_depth_ft}ft "
        f"({blueprint.room_area_sqft} sqft). GUESTS: {blueprint.guest_count}. "
        f"BUDGET: Rs {blueprint.budget_inr}. THEME: {blueprint.theme.name} — "
        f"{blueprint.theme.tagline}. SPLIT: {blueprint.theme.budget_split_pct()}."
    )

    url = settings.GEMINI_ENDPOINT.format(model=settings.GEMINI_MODEL)
    payload = {
        "systemInstruction": {"parts": [{"text": GEMINI_SYSTEM_PROMPT}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime,
                                 "data": base64.b64encode(raw).decode("ascii")}},
                {"text": context},
            ],
        }],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url + f"?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.GEMINI_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        logger.warning("AURA: Gemini vision call failed (%s) → offline fallback.", exc)
        return None

    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        logger.warning("AURA: unexpected Gemini payload shape.")
        return None

    return _lenient_json(text)


def _lenient_json(text: str) -> dict | None:
    """Extract the first JSON object from model output, tolerating fences."""
    text = text.strip()
    fenced = re.search(r"\{.*\}", text, re.DOTALL)
    if not fenced:
        return None
    try:
        data = json.loads(fenced.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) and "summary" in data else None


# ====================================================================== #
#  2. OFFLINE HEURISTIC AUDIT                                             #
# ====================================================================== #
def heuristic_audit(blueprint: EventBlueprint) -> dict:
    """Deterministic pseudo-vision narrative built from structured inputs."""
    bp = blueprint
    area = bp.room_area_sqft
    per_head = area / max(bp.guest_count, 1)
    aspect = float(bp.room_width_ft) / max(float(bp.room_depth_ft), 1)

    if per_head >= 2.2:
        density = "generous circulation; lounge clusters can breathe"
        axis = "central-island"
    elif per_head >= 1.4:
        density = "balanced standing room; keep one clear service lane"
        axis = "e-w"
    else:
        density = ("tight standing load — prioritise vertical decor and "
                   "low-footprint seating")
        axis = "n-s"

    light = "mixed"
    if area > 260:
        light = "bright-daylight"
    elif area < 140:
        light = "dim-warm"

    risks = []
    if bp.guest_count * 1.5 > area:
        risks.append("Guest load exceeds dance-floor comfort; stagger arrivals.")
    if aspect > 1.6 or aspect < 0.62:
        risks.append("Room is strongly rectangular — avoid centring all pins.")
    if float(bp.budget_inr) / max(bp.guest_count, 1) < 900:
        risks.append("Budget-per-guest is lean; lighting carries the atmosphere.")

    summary = (
        f"OFFLINE HEURISTIC AUDIT — {bp.room_width_ft} ft × {bp.room_depth_ft} ft "
        f"space ({area} sqft) for {bp.guest_count} guests reads as {density}. "
        f"Focal wall inferred at the far-centre plane; primary traffic axis: "
        f"{axis.replace('-', ' → ')}. Light read: {light}. Under the "
        f"“{bp.theme.name}” split ({bp.theme.budget_split_pct()}), the local "
        f"knapsack engine allocates envelopes per category and holds total "
        f"spend at or below ₹{int(bp.budget_inr):,} — zero overrun enforced "
        f"at every solve."
    )
    return {
        "summary": summary,
        "focal_wall_pct": {"x": 50, "y": 22},
        "traffic_axis": axis,
        "light_read": light,
        "risk_notes": risks[:2],
    }


# ====================================================================== #
#  3. KNAPSACK BUDGET OPTIMIZER (guarantees zero overrun)                #
# ====================================================================== #
def _utility(item: FurnitureItem, needed_seats: int, envelope_share: float) -> float:
    """Editorial utility: aura per ₹k, boosted by seat coverage & theme fit."""
    price = float(item.price_inr) or 1.0
    base = item.aesthetic_score / (price / 1000.0)          # aura per ₹1k
    if item.guest_capacity and needed_seats > 0:
        base *= 1 + min(item.guest_capacity, needed_seats) / max(needed_seats, 1) * 0.6
    if envelope_share > 0.30:                                # category scarcity bonus
        base *= 1.12
    return round(base, 4)


def knapsack_optimize(blueprint: EventBlueprint, audit: dict | None = None) -> list[dict]:
    """Bounded multi-choice knapsack over the catalog.

    Returns a list of pick dicts: {item_id, sku, name, category, qty, unit_price,
    line_total, pin_x_pct, pin_y_pct, note}. Total is ALWAYS ≤ budget.
    """
    bp = blueprint
    budget = float(bp.budget_inr)
    reserve = budget * 0.02                      # hold 2% contingency buffer
    spendable = budget - reserve

    ratios = bp.theme.ratio_map()
    seats_target = bp.guest_count
    room_area = bp.room_area_sqft

    items = list(FurnitureItem.objects.filter(in_stock=True))
    theme_items = [i for i in items if i.suits_theme(bp.theme.code)] or items

    picks: list[dict] = []
    spent = 0.0
    seats_covered = 0
    floor_used = 0.0
    used_ids: set[int] = set()

    # Pass 1 — fill each category envelope greedily by utility density.
    for cat in CATEGORY_ORDER:
        share = ratios.get(cat, ratios.get("decor", 0.2) if cat == "lighting" else 0.15)
        if cat == "decor":
            share = ratios["decor"] * 0.55       # decor minus lighting carve-out
        envelope = spendable * share
        cat_spend = 0.0
        pool = sorted(
            (i for i in theme_items if i.category == cat),
            key=lambda i: _utility(i, max(seats_target - seats_covered, 0), share),
            reverse=True,
        )
        for item in pool:
            if cat_spend >= envelope * 0.97:
                break
            price = float(item.price_inr)
            # How many of this SKU fit remaining envelope AND global budget?
            room_left = room_area - floor_used
            max_qty = 1
            if cat == "seating" and item.guest_capacity:
                need = max(seats_target - seats_covered, 0)
                max_qty = min(int(math.ceil(need / item.guest_capacity)), 4)
            elif item.footprint_sqft and room_left > 0:
                max_qty = min(max(int(room_left // float(item.footprint_sqft)), 1), 3)
            qty = max_qty
            while qty > 0 and (cat_spend + price * qty > envelope
                               or spent + price * qty > spendable
                               or floor_used + float(item.footprint_sqft) * qty > room_area * 0.8):
                qty -= 1
            if qty <= 0:
                continue
            picks.append({"item_id": item.pk, "sku": item.sku, "name": item.name,
                          "category": cat, "qty": qty, "unit_price": price,
                          "line_total": round(price * qty, 2), "_item": item})
            cat_spend += price * qty
            spent += price * qty
            floor_used += float(item.footprint_sqft) * qty
            used_ids.add(item.pk)
            if cat == "seating":
                seats_covered += item.guest_capacity * qty

    # Pass 2 — top up leftover budget with best global value-dense items
    # (fills rounding gaps without ever crossing the hard budget line).
    leftovers = sorted(
        (i for i in theme_items if i.pk not in used_ids),
        key=lambda i: i.value_density(), reverse=True,
    )
    for item in leftovers:
        price = float(item.price_inr)
        if spent + price <= spendable and \
           floor_used + float(item.footprint_sqft) <= room_area * 0.8:
            picks.append({"item_id": item.pk, "sku": item.sku, "name": item.name,
                          "category": item.category, "qty": 1, "unit_price": price,
                          "line_total": price, "_item": item})
            spent += price
            floor_used += float(item.footprint_sqft)
            used_ids.add(item.pk)
            if len(picks) >= 9:
                break

    # Hard invariant guard — never exceed budget.
    picks = _shrink_to_fit(picks, budget)

    # Spatial pin allocation across the photo canvas.
    _allocate_pins(picks, audit or {})
    for p in picks:
        p.pop("_item", None)
    return picks


def _shrink_to_fit(picks: list[dict], budget: float) -> list[dict]:
    total = sum(p["line_total"] for p in picks)
    # Drop lowest-utility tail items until we're strictly within budget.
    ordered = sorted(picks, key=lambda p: p["line_total"])
    while total > budget and ordered:
        worst = ordered.pop(0)
        total -= worst["line_total"]
        picks.remove(worst)
    return picks


_PIN_GRID = {
    "seating":      [(26, 64), (70, 60), (18, 74), (80, 72)],
    "decor":        [(50, 24), (38, 70), (62, 70), (50, 82)],
    "lighting":     [(50, 10), (28, 14), (72, 14)],
    "hospitality":  [(88, 42), (12, 42), (90, 80)],
}


def _allocate_pins(picks: list[dict], audit: dict) -> None:
    """Spread chosen SKUs onto plausible photo coordinates (percentages)."""
    focal = (audit.get("focal_wall_pct") or {})
    fx = float(focal.get("x", 50))
    fy = float(focal.get("y", 22))
    cursor = {c: 0 for c in _PIN_GRID}

    for p in sorted(picks, key=lambda q: (q["category"], -q["line_total"])):
        cat = p["category"]
        grid = _PIN_GRID.get(cat, _PIN_GRID["decor"])
        if cat == "decor" and p["sku"].startswith("AUR-DC-008"):
            # Signature arch backdrop claims the inferred focal wall.
            px, py = fx, fy
        else:
            idx = cursor.get(cat, 0) % len(grid)
            px, py = grid[idx]
            cursor[cat] = idx + 1
        p["pin_x_pct"] = round(min(max(px + (idx % 3) * 1.5, 4), 96), 2)
        p["pin_y_pct"] = round(min(max(py, 6), 92), 2)
        p["note"] = f"{cat.capitalize()} pin · aura {p['_item'].aesthetic_score:.1f}" if "_item" in p else f"{cat.capitalize()} stage pin"


# ====================================================================== #
#  4. RUN OF SHOW                                                         #
# ====================================================================== #
def build_run_of_show(blueprint: EventBlueprint, audit: dict) -> list[dict]:
    """Chronological timeline enriched by the audit's traffic/light reads."""
    from .seeds import _default_run_of_show

    ros = _default_run_of_show(blueprint, start="18:00")
    axis = audit.get("traffic_axis", "e-w").replace("-", " → ")
    light = audit.get("light_read", "mixed")
    ros.insert(2, {
        "time": "18:45",
        "title": "Spatial Flow Check",
        "detail": f"Staff rehearse the {axis} traffic axis; lighting preset tuned to “{light}” read.",
    })
    return ros


# ====================================================================== #
#  5. ORCHESTRATOR — solve + persist                                      #
# ====================================================================== #
def run_generation_pipeline(blueprint: EventBlueprint, api_key: str = "") -> dict:
    """Full engine pass: audit → knapsack → persist pins → response payload."""
    engine = "knapsack-local"
    audit = None
    if api_key:
        audit = gemini_vision_audit(blueprint, api_key)
        if audit:
            engine = "gemini-2.5-flash + knapsack"
    if audit is None:
        audit = heuristic_audit(blueprint)

    picks = knapsack_optimize(blueprint, audit)

    # Persist: wipe old engine pins, write new ones atomically.
    StagedFurniture.objects.filter(blueprint=blueprint).delete()
    with_staged = False
    for p in picks:
        obj = StagedFurniture.objects.create(
            blueprint=blueprint,
            item=FurnitureItem.objects.get(pk=p["item_id"]),
            quantity=p["qty"],
            pin_x_pct=p["pin_x_pct"],
            pin_y_pct=p["pin_y_pct"],
            placed_by="aura-engine",
            note=p.get("note", ""),
        )
        with_staged = True

    blueprint.ai_engine = engine
    blueprint.ai_summary = audit["summary"]
    blueprint.run_of_show = build_run_of_show(blueprint, audit)
    blueprint.status = EventBlueprint.Status.STAGED
    blueprint.save(update_fields=["ai_engine", "ai_summary", "run_of_show",
                                  "status", "updated_at"])
    if with_staged:
        blueprint.recalc_spent(commit=True)

    staged = (
        StagedFurniture.objects.filter(blueprint=blueprint)
        .select_related("item")
        .order_by("pin_y_pct", "pin_x_pct")
    )
    bom = [{
        "sku": s.item.sku,
        "name": s.item.name,
        "category": s.item.category,
        "qty": s.quantity,
        "unit_price": float(s.item.price_inr),
        "line_total": float(s.line_total),
        "pin": {"x": float(s.pin_x_pct), "y": float(s.pin_y_pct)},
        "note": s.note,
    } for s in staged]

    spent = float(blueprint.spent_inr)
    budget = float(blueprint.budget_inr)
    return {
        "blueprint_id": blueprint.pk,
        "engine": engine,
        "audit": audit,
        "bom": bom,
        "totals": {
            "budget": budget,
            "spent": spent,
            "headroom": round(budget - spent, 2),
            "utilisation_pct": round(spent / budget * 100, 1) if budget else 0,
            "zero_overrun": spent <= budget,
        },
        "run_of_show": blueprint.run_of_show_list(),
        "photo_url": blueprint.room_photo.url if blueprint.room_photo else None,
    }
