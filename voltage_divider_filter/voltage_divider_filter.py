#!/usr/bin/env python3
"""Voltage divider + capacitor low-pass filter calculator (standard values).

Formula:  C = (R1 + R2) / (R1 * R2 * 2 * pi * f)
Divider:  Vout = Vin * R2 / (R1 + R2)

Resistors use the E12 series, capacitors use the series set in CAP_SERIES.
All combinations are tested (brute force) and the 5 best are listed.
SI suffixes accepted: p, n, u, m, k, M (or meg), G   e.g. 4.7k, 100n, 1meg
"""
import math
import sys

E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E6 = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]

R_SERIES = E12
CAP_SERIES = E12          # change to E6 for a coarser capacitor set

R_DECADES = range(0, 8)   # 1 ohm   .. 8.2 Mohm
C_DECADES = range(-12, -2)  # 1 pF  .. 820 uF

SUFFIXES = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
            "k": 1e3, "K": 1e3, "M": 1e6, "meg": 1e6, "G": 1e9}


def parse(text):
    s = text.strip()
    for unit in ("Hz", "hz", "ohm", "Ohm", "Ω", "V", "F"):
        if s.endswith(unit):
            s = s[: -len(unit)].strip()
    if s.lower().endswith("meg"):
        return float(s[:-3]) * 1e6
    if s and s[-1] in SUFFIXES:
        return float(s[:-1]) * SUFFIXES[s[-1]]
    return float(s)


def fmt(value, unit):
    for factor, prefix in ((1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""),
                           (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p")):
        if abs(value) >= factor * 0.9999:
            return f"{value / factor:.4g} {prefix}{unit}"
    return f"{value:.4g} {unit}"


def in_series(value, series):
    mant = value / 10 ** math.floor(math.log10(value))
    return any(abs(mant - s) / s < 1e-6 for s in series + [10.0])


def values(series, decades):
    return [m * 10 ** d for d in decades for m in series]


def ask(prompt):
    while True:
        try:
            v = parse(input(prompt))
            if v > 0:
                return v
            print("  Value must be greater than 0.")
        except ValueError:
            print("  Invalid number. Examples: 5, 4.7k, 100n, 1meg")


def ask_base(base):
    name, unit, series, ex = (("C", "F", CAP_SERIES, "100n") if base == "c" else
                              (base.upper(), "Ω", R_SERIES, "10k"))
    series_name = "capacitor series" if base == "c" else "E12 series"
    while True:
        v = ask(f"{name} ({unit}, e.g. {ex}): ")
        if in_series(v, series):
            return v
        print(f"  WARNING: {fmt(v, unit)} is not in the {series_name}.")
        if input("  Are you sure you want to use it? [y/N]: ").strip().lower() in ("y", "yes"):
            return v


def main():
    print("=== RC Voltage Divider Low-Pass Filter (standard values) ===\n")
    vin = ask("Input voltage (V): ")
    while True:
        vout = ask("Output voltage (V): ")
        if vout < vin:
            break
        print("  Output voltage must be lower than input voltage.")
    f = ask("Low-pass cut-off frequency (Hz): ")
    while True:
        base = input("Base component [c / r1 / r2]: ").strip().lower()
        if base in ("c", "r1", "r2"):
            break
        print("  Please enter c, r1 or r2.")
    fixed = ask_base(base)

    r_vals = values(R_SERIES, R_DECADES)
    c_vals = values(CAP_SERIES, C_DECADES)
    w = 2 * math.pi

    # Candidate (r1, r2, c) combinations; the base component is held fixed.
    if base == "c":
        combos = ((r1, r2, fixed) for r1 in r_vals for r2 in r_vals)
    elif base == "r1":
        combos = ((fixed, r2, c) for r2 in r_vals for c in c_vals)
    else:
        combos = ((r1, fixed, c) for r1 in r_vals for c in c_vals)

    results = []
    for r1, r2, c in combos:
        vo = vin * r2 / (r1 + r2)
        fc = (r1 + r2) / (r1 * r2 * w * c)
        ev = (vo - vout) / vout
        ef = (fc - f) / f
        score = math.hypot(ev, ef)   # combined relative error
        results.append((score, r1, r2, c, vo, ev, fc, ef))
    results.sort(key=lambda x: x[0])

    print(f"\nTested {len(results)} combinations.")
    print(f"Target: Vout = {vout:.4g} V, fc = {fmt(f, 'Hz')}\n")
    print("Best 5 combinations:")
    print(f"{'#':<3}{'R1':>10}{'R2':>10}{'C':>10}{'Vout':>10}{'err':>8}{'fc':>12}{'err':>8}")
    for i, (_, r1, r2, c, vo, ev, fc, ef) in enumerate(results[:5], 1):
        print(f"{i:<3}{fmt(r1, 'Ω'):>10}{fmt(r2, 'Ω'):>10}{fmt(c, 'F'):>10}"
              f"{vo:>8.4g} V{ev * 100:>+7.2f}%{fmt(fc, 'Hz'):>12}{ef * 100:>+7.2f}%")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(1)