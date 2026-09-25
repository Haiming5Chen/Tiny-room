"""Sourced dry sliding friction for PAIRS of surfaces.

Friction is a property of a pair of surfaces, not of one material. MuJoCo stores one
coefficient per geom and combines two of them with max(), so a 0.01 "skid" resting on
a 0.8 floor slides at 0.8: the skid material in this repository never skidded. This
table replaces that combination, contact by contact, for every pair it lists. Pairs it
does not list keep MuJoCo's combination and are reported as unsourced.

Rules for an entry:
- `kinetic` is the coefficient MuJoCo receives (it has one coefficient, not a static
  and a dynamic one). `static` is kept for reporting and for hold/slip estimates.
- Every value names its source, the conditions it was measured under, and a
  confidence: high (primary measurement with stated conditions), medium (handbook
  or engineering compilation), low (design guideline or analogue).
- `basis="analogue"` means no measurement of this pair was found and the value of a
  named, physically similar pair is used instead. Analogues are labelled, never
  presented as measurements.
- Published values for the same nominal pair routinely differ by a factor of two;
  surface finish, contact pressure and speed explain most of it. The notes carry the
  spread so nobody mistakes a single number here for the truth.

Standard library only: this module is data and must stay importable without MuJoCo.
"""
from dataclasses import dataclass
import hashlib
import json

SURFACES = {
    "rubber": "Tread, bumper or pad rubber of the NR/SBR class, roughly 60-70 Shore A",
    "ptfe": "PTFE glide or skid",
    "aluminium": "Aluminium alloy, bare or anodized",
    "steel": "Carbon or mild steel, as received",
    "wood": "Dry planed, varnished or painted wood",
    "abs": "ABS or a similar rigid thermoplastic",
    "hdpe": "High-density polyethylene",
    "concrete": "Smooth dry concrete",
}

CONFIDENCE = ("high", "medium", "low")
BASIS = ("measured", "handbook", "guideline", "analogue")


@dataclass(frozen=True)
class Source:
    citation: str
    url: str
    checked: str  # date the value was read at the URL


SOURCES = {
    "xu2025": Source(
        "R. Xu, N. Miyashita, B.N.J. Persson, 'Rubber wear on concrete: Dry and in-water "
        "conditions', Wear 578-579 (2025) 206200",
        "https://www.sciencedirect.com/science/article/pii/S0043164825004697", "2026-09-25"),
    "gdv": Source(
        "GDV (German Insurance Association), Container Handbook, section 4.4.5, sliding "
        "friction coefficients, Tables 1a-1d (the GDV's own tests; published as guidelines)",
        "https://www.containerhandbuch.de/chb_e/stra/stra_04_04_05.html", "2026-09-25"),
    "ctu": Source(
        "IMO/ILO/UNECE CTU Code friction factors as reproduced in Volvo Group & MariTerm AB, "
        "'Transport Quality Manual' (2014-07-04). Friction factor = 92.5% of static friction; "
        "dynamic friction is taken as 75% of the factor",
        "https://www.volvogroup.com/content/dam/volvo-group/markets/master/suppliers/"
        "useful-links-and-documents-for-existing-suppliers/logistics-solutions/download/"
        "Volvo%20-%20Transport%20Quality%20Manual%20-%202014-07-04.pdf", "2026-09-25"),
    "chemours": Source(
        "Chemours, 'Teflon PTFE fluoropolymer resin: Properties Handbook' (2018), Table 15, "
        "against polished steel, 21-27 C",
        "https://www.crp.co.uk/wp-content/uploads/2020/06/Teflon_PTFE_Properties_Handbook.pdf",
        "2026-09-25"),
    "asm": Source(
        "P.J. Blau, 'Appendix: Static and Kinetic Friction Coefficients for Selected "
        "Materials', ASM Handbook Vol. 18 (ASM International, 1992); unlubricated solids "
        "at room temperature in ambient air",
        "https://ptacts.uspto.gov/ptacts/public-informations/petitions/1556742/"
        "download-documents?artifactId=pQFfRojsfRbry4mMyGsRGib2V60lbp6mAkqr8z76Os-9GTEFRsGxurE",
        "2026-09-25"),
    "villar2022": Source(
        "Villar-Garcia et al., Forests 13(7):1078 (2022); sawn chestnut at 12% moisture, "
        "0.5 MPa, 8 mm/min; S235 steel plate Ra 0.33 um",
        "https://www.mdpi.com/1999-4907/13/7/1078", "2026-09-25"),
    "devries2018": Source(
        "B. DeVries, 'Variant Friction Coefficients of Lagging and Implications for Conveyor "
        "Design', Beltcon 18 (2018); plain rubber lagging vs belt cover rubber, clean and "
        "dry, 50.8 mm/min, fit mu = 1.3004 exp(-0.002 p[kPa])",
        "https://www.beltcon.org.za/wp-content/uploads/2024/12/"
        "B18-18-De-Vries-Varient-friction-lagging-Rev-5-GS.pdf", "2026-09-25"),
    "budinski2018": Source(
        "K.G. Budinski, S.T. Budinski, 'On the Mechanism of Shoe Versus Walking-Surface "
        "Friction', STLE Annual Meeting 2018; sled test, five rubbers (CBR, PUR, SBR, PCR, "
        "PCR/EPDM)",
        "https://www.stle.org/images/pdf/STLE_ORG/AM2018%20Presentations/"
        "Materials%20Tribology/STLE2018_Materials%20Tribology%20IV_Session%206D_"
        "K.%20Budinski_On%20the%20Mechanism%20of%20Shoe%20Versus%20Walking%20Surface%20Friction.pdf",
        "2026-09-25"),
    "rabbat1979": Source(
        "B.G. Rabbat, H.G. Russell, 'Tests to Evaluate Coefficient of Static Friction Between "
        "Steel and Concrete', Construction Technology Laboratories (PCA), February 1979; "
        "push-off tests, dry interface, 60 psi",
        "https://www.nrc.gov/docs/ML1926/ML19261A846.pdf", "2026-09-25"),
    "kumar2020": Source(
        "S. Kumar, B.S. Roy, 'Tribological properties of acrylonitrile butadiene styrene in "
        "self-mated contacts and against steel disc', Materials Today: Proceedings 26(2) "
        "(2020); pin-on-disc, ASTM G99-05, dry",
        "https://www.sciencedirect.com/science/article/abs/pii/S2214785320312669", "2026-09-25"),
}


@dataclass(frozen=True)
class PairFriction:
    kinetic: float
    static: float | None
    sources: tuple
    confidence: str
    basis: str
    note: str


def _key(a, b):
    return (a, b) if a <= b else (b, a)


def _pair(a, b, kinetic, static, sources, confidence, basis, note):
    return _key(a, b), PairFriction(kinetic, static, tuple(sources), confidence, basis, note)


PAIRS = dict((
    # -- rubber: the wheels, bumpers and gripper pads ---------------------------------
    _pair("rubber", "concrete", .95, None, ("xu2025",), "high", "measured",
          "SBR on smooth concrete, 0.16-0.61 MPa, 3 mm/s, 20 C: mean 0.95; filled SBR and "
          "NR on rough concrete 1.02-1.07. Textbook tables give 0.6-0.85."),
    _pair("rubber", "wood", .75, None, ("gdv",), "low", "guideline",
          "Rubber friction mat on matt varnished wood, sliding. A cargo-securing "
          "guideline, not a laboratory measurement of tread rubber."),
    _pair("rubber", "aluminium", .40, None, ("gdv",), "low", "guideline",
          "Rubber friction mat on aluminium, sliding. Silicone pads on aluminium measure "
          "0.4-0.6 in soft-robotics work; elastomer friction falls as pressure rises."),
    _pair("rubber", "steel", .52, None, ("budinski2018",), "medium", "measured",
          "Average of five rubbers sled-tested on smooth ground steel. Rubber supplier "
          "tables give 0.6-0.9."),
    _pair("rubber", "abs", .50, None, ("gdv",), "low", "analogue",
          "No rubber-on-ABS value found. Uses the guideline for a rubber mat on polyamide "
          "(PA), the nearest rigid thermoplastic listed."),
    _pair("rubber", "hdpe", .70, None, ("gdv",), "low", "guideline",
          "Rubber friction mat (gum) on polyethylene, sliding."),
    _pair("rubber", "rubber", 1.10, None, ("devries2018",), "medium", "measured",
          "Clean dry rubber on rubber: 1.2 at 35 kPa, 1.1 at about 85 kPa, 0.3 at 700 kPa. "
          "Strongly pressure dependent."),
    _pair("rubber", "ptfe", .30, None, ("budinski2018",), "medium", "measured",
          "Average of five rubbers sled-tested on a PTFE counterface."),
    # -- PTFE: the skids ---------------------------------------------------------------
    _pair("ptfe", "steel", .10, .08, ("chemours",), "high", "measured",
          "Static 0.05-0.08 at 500 psi; dynamic 0.10 at 10 fpm, 0.13 at 100 fpm. PTFE's "
          "static coefficient is lower than its dynamic one at low speed."),
    _pair("ptfe", "aluminium", .10, .08, ("chemours",), "low", "analogue",
          "No measurement found. PTFE's friction is set largely by its own low shear "
          "strength once a transfer film forms, so the polished-steel value is used."),
    _pair("ptfe", "wood", .10, .08, ("chemours",), "low", "analogue",
          "No measurement found; polished-steel value used as an analogue. Likely an "
          "underestimate on rough wood, where no transfer film forms at first."),
    _pair("ptfe", "concrete", .10, .08, ("chemours",), "low", "analogue",
          "No measurement found; polished-steel value used as an analogue. Likely an "
          "underestimate on rough concrete."),
    # -- metals ------------------------------------------------------------------------
    _pair("aluminium", "aluminium", .34, .42, ("asm",), "medium", "handbook",
          "6061-T6 on 6061-T6, flat on flat. Tables from 1929-1940 give 1.05-1.4 for "
          "rigorously clean aluminium; as-received surfaces measure far lower."),
    _pair("aluminium", "steel", .32, .41, ("asm",), "medium", "handbook",
          "6061-T6 against 1032 steel, flat on flat: 0.35/0.25 and 0.47/0.38 depending "
          "on which specimen moves; the mean is used."),
    _pair("aluminium", "wood", .19, .27, ("ctu",), "medium", "guideline",
          "Planed wood on grooved aluminium, friction factor 0.25 (static 0.27, dynamic "
          "0.19). Consistent with modern wood-on-smooth-steel measurements (0.17-0.26)."),
    _pair("aluminium", "hdpe", .11, .16, ("ctu",), "low", "guideline",
          "Plastic pallet on grooved aluminium, friction factor 0.15. The plastic is not "
          "named; pallets of this kind are usually HDPE or PP."),
    _pair("steel", "steel", .23, .31, ("asm",), "medium", "handbook",
          "1032 steel on 1032 steel, flat on flat. Rigorously cleaned steel measures "
          "0.7-0.8; as-received surfaces 0.2-0.3."),
    _pair("steel", "wood", .17, .19, ("villar2022",), "high", "measured",
          "Chestnut sawn timber on S235 plate (Ra 0.33 um), 0.5 MPa, 8 mm/min. Rough "
          "steel measures up to 0.8."),
    _pair("steel", "concrete", .57, .69, ("rabbat1979",), "medium", "measured",
          "Rolled steel plate on cast concrete, dry, 60 psi: peak 0.69, effective (after "
          "the peak) 0.57. The effective value is used as the sliding coefficient."),
    _pair("steel", "abs", .37, .40, ("kumar2020", "asm"), "medium", "measured",
          "ABS pin on steel disc 0.37-0.45 (Kumar & Roy); ABS against carbon steel, ball "
          "on flat, static 0.40 and kinetic 0.27 (ASM)."),
    _pair("steel", "hdpe", .23, .36, ("asm",), "medium", "handbook",
          "HDPE against carbon steel, ball on flat."),
    # -- wood, plastics, concrete ------------------------------------------------------
    _pair("wood", "wood", .36, .47, ("villar2022",), "high", "measured",
          "Sawn chestnut on sawn chestnut; grain orientation made no significant "
          "difference. Planed faces measure lower (0.1-0.3), Morin's oak 0.48."),
    _pair("wood", "concrete", .40, .59, ("gdv", "ctu"), "medium", "guideline",
          "Concrete/wood sliding 0.4 (GDV); sawn timber on smooth concrete friction "
          "factor 0.55, static 0.59 (CTU Code)."),
    _pair("wood", "hdpe", .15, .22, ("ctu",), "low", "guideline",
          "Plastic pallet on plywood, friction factor 0.2. The plastic is not named."),
    _pair("abs", "abs", .74, None, ("kumar2020",), "medium", "measured",
          "ABS pin on ABS disc, 0.74-0.98 depending on load and speed; the lower bound is "
          "used. Self-mated ABS is unusually sticky; printed PLA on PLA measures 0.12-0.38."),
    _pair("concrete", "concrete", .40, None, ("gdv",), "low", "guideline",
          "Concrete on concrete, sliding. Measured static values run 0.5-0.9 for as-cast "
          "surfaces."),
))


def validate_surface(name):
    if name not in SURFACES:
        raise ValueError(f"Unknown contact surface {name!r}; known: {', '.join(sorted(SURFACES))}")
    return name


def lookup(a, b):
    """The sourced pair for two surfaces, or None when no source covers it."""
    if a is None or b is None:
        return None
    return PAIRS.get(_key(a, b))


def fingerprint():
    """Changes whenever any value, source or surface changes; for stored comparisons."""
    data = {"surfaces": SURFACES,
            "pairs": {"|".join(k): [v.kinetic, v.static, list(v.sources), v.confidence, v.basis]
                      for k, v in sorted(PAIRS.items())}}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def markdown_table():
    """The table as documentation, generated so the docs cannot drift from the data."""
    rows = ["| Pair | Kinetic (used) | Static | Basis | Confidence | Source |",
            "| --- | --- | --- | --- | --- | --- |"]
    for (a, b), p in sorted(PAIRS.items()):
        static = "-" if p.static is None else f"{p.static:.2f}"
        rows.append(f"| {a} / {b} | {p.kinetic:.2f} | {static} | {p.basis} | {p.confidence} | "
                    f"{', '.join(p.sources)} |")
    return "\n".join(rows)
