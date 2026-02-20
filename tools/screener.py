"""
╔══════════════════════════════════════════════════╗
║           CRYPTO SCREENER · CoinGecko API        ║
║        6 Kategori Trading Signal Screener        ║
╚══════════════════════════════════════════════════╝
Requirements: pip install requests
Usage       : python crypto_screener.py
"""

import requests
import time
from datetime import datetime

# ─────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────
TOTAL_PAGES   = 4       # 4 halaman x 250 = ~1000 coin
PER_PAGE      = 250
DELAY_BETWEEN = 1.5     # detik antar request (hindari rate limit)
CURRENCY      = "usd"

# ─────────────────────────────────────────
#  DEFINISI KATEGORI
#  format range: [min, max] atau None (bebas)
# ─────────────────────────────────────────
CATEGORIES = {
    "intraday_long": {
        "label"   : "INTRADAY LONG",
        "icon"    : "▲ ",
        "type"    : "long",
        "h24"     : (2, 8),
        "d7"      : (-3, 5),
        "d30"     : (-10, 10),
        "vol_mcap": (0.03, 0.15),
        "from_ath": (-75, -40),   # additional
    },
    "semi_swing_long": {
        "label"   : "SEMI-SWING LONG",
        "icon"    : "▲▲",
        "type"    : "long",
        "h24"     : (0, 10),
        "d7"      : (5, 20),
        "d30"     : (-5, 25),
        "vol_mcap": (0.02, 0.12),
        "from_ath": (-85, -50),
    },
    "swing_long": {
        "label"   : "SWING LONG",
        "icon"    : "▲▲▲",
        "type"    : "long",
        "h24"     : None,         # bebas
        "d7"      : (10, 40),
        "d30"     : (15, 60),
        "vol_mcap": (0.01, 0.08),
        "from_ath": (-95, -75),
    },
    "intraday_short": {
        "label"   : "INTRADAY SHORT",
        "icon"    : "▼ ",
        "type"    : "short",
        "h24"     : (-8, -3),
        "d7"      : (-12, -5),
        "d30"     : (-20, -10),
        "vol_mcap": (0.03, 0.12),
        "from_ath": (-75, -50),
    },
    "semi_swing_short": {
        "label"   : "SEMI-SWING SHORT",
        "icon"    : "▼▼",
        "type"    : "short",
        "h24"     : (-10, -2),
        "d7"      : (-25, -10),
        "d30"     : (-40, -20),
        "vol_mcap": (0.02, 0.10),
        "from_ath": (-85, -60),
    },
    "swing_short": {
        "label"   : "SWING SHORT",
        "icon"    : "▼▼▼",
        "type"    : "short",
        "h24"     : None,
        "d7"      : (-40, -15),
        "d30"     : (-60, -30),
        "vol_mcap": (0.01, 0.06),
        "from_ath": (-95, -70),
    },
}

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def in_range(value, rng):
    """Return True jika value dalam range. None range = bebas."""
    if rng is None:
        return True
    if value is None:
        return False
    return rng[0] <= value <= rng[1]

def fmt_pct(value):
    if value is None:
        return "   N/A  "
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

def fmt_price(value):
    if value is None:
        return "N/A"
    if value < 0.001:
        return f"${value:.6f}"
    if value < 1:
        return f"${value:.4f}"
    if value < 1000:
        return f"${value:.2f}"
    return f"${value:,.0f}"

def fmt_mcap(value):
    if value is None:
        return "N/A"
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    if value >= 1e6:
        return f"${value/1e6:.1f}M"
    return f"${value:,.0f}"

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: color(t, "92")
RED    = lambda t: color(t, "91")
YELLOW = lambda t: color(t, "93")
CYAN   = lambda t: color(t, "96")
WHITE  = lambda t: color(t, "97")
DIM    = lambda t: color(t, "2")
BOLD   = lambda t: color(t, "1")

def pct_colored(value):
    txt = fmt_pct(value)
    if value is None:
        return DIM(txt)
    return GREEN(txt) if value >= 0 else RED(txt)


# ─────────────────────────────────────────
#  FETCH DATA
# ─────────────────────────────────────────
def fetch_coins():
    all_coins = []
    url = "https://api.coingecko.com/api/v3/coins/markets"

    for page in range(1, TOTAL_PAGES + 1):
        print(f"  Fetching halaman {page}/{TOTAL_PAGES}...", end="\r")
        params = {
            "vs_currency"              : CURRENCY,
            "order"                    : "market_cap_desc",
            "per_page"                 : PER_PAGE,
            "page"                     : page,
            "sparkline"                : "false",
            "price_change_percentage"  : "24h,7d,30d",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                print(YELLOW("\n  ⚠ Rate limit! Tunggu 60 detik..."))
                time.sleep(60)
                resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            all_coins.extend(data)
        except requests.RequestException as e:
            print(RED(f"\n  ✗ Error halaman {page}: {e}"))
            break

        if page < TOTAL_PAGES:
            time.sleep(DELAY_BETWEEN)

    print(f"  ✓ Total coin diambil: {len(all_coins)}{' ' * 20}")
    return all_coins


# ─────────────────────────────────────────
#  SCREENING
# ─────────────────────────────────────────
def screen_coin(coin):
    """Return list kategori yang cocok beserta metadata."""
    h24      = coin.get("price_change_percentage_24h")
    d7       = coin.get("price_change_percentage_7d_in_currency")
    d30      = coin.get("price_change_percentage_30d_in_currency")
    vol      = coin.get("total_volume")
    mcap     = coin.get("market_cap")
    ath      = coin.get("ath")
    price    = coin.get("current_price")

    vol_mcap = (vol / mcap) if (vol and mcap and mcap > 0) else None
    from_ath = ((price - ath) / ath * 100) if (ath and price and ath > 0) else None

    matches = []
    for key, cat in CATEGORIES.items():
        main_pass = (
            in_range(h24,      cat["h24"])      and
            in_range(d7,       cat["d7"])       and
            in_range(d30,      cat["d30"])      and
            in_range(vol_mcap, cat["vol_mcap"])
        )
        if main_pass:
            ath_pass = in_range(from_ath, cat["from_ath"]) if from_ath is not None else None
            matches.append({
                "key"     : key,
                "ath_pass": ath_pass,
                "vol_mcap": vol_mcap,
                "from_ath": from_ath,
            })
    return matches


def run_screening(coins):
    results = {key: [] for key in CATEGORIES}
    for coin in coins:
        for match in screen_coin(coin):
            results[match["key"]].append({
                "coin"    : coin,
                **match,
            })
    return results


# ─────────────────────────────────────────
#  PRINT RESULTS
# ─────────────────────────────────────────
def print_header():
    print()
    print(BOLD(WHITE("╔══════════════════════════════════════════════════════════════╗")))
    print(BOLD(WHITE("║   CRYPTO SCREENER  ·  " + CYAN("CoinGecko API") + WHITE("    ║"))))
    print(BOLD(WHITE("╚══════════════════════════════════════════════════════════════╝")))
    print(DIM(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    print()

def print_category(cat_key, items):
    cat = CATEGORIES[cat_key]
    label = cat["label"]
    icon  = cat["icon"]
    is_long = cat["type"] == "long"

    # category header
    bar_color = GREEN if is_long else RED
    print(bar_color(f"\n{'─' * 65}"))
    print(BOLD(bar_color(f"  {icon}  {label}  [{len(items)} sinyal]")))
    print(bar_color(f"{'─' * 65}"))

    if not items:
        print(DIM("  — tidak ada coin yang memenuhi kriteria —"))
        return

    # table header
    header = (
        f"  {'COIN':<10} {'HARGA':>10} {'24h%':>9} {'7d%':>9} "
        f"{'30d%':>9} {'VOL/MCAP':>9} {'FROM ATH':>10} {'MCAP':>8}  {'ATH✓'}"
    )
    print(DIM(header))
    print(DIM("  " + "·" * 90))

    for item in items:
        coin     = item["coin"]
        vol_mcap = item["vol_mcap"]
        from_ath = item["from_ath"]
        ath_pass = item["ath_pass"]

        symbol = coin.get("symbol", "").upper()
        h24    = coin.get("price_change_percentage_24h")
        d7     = coin.get("price_change_percentage_7d_in_currency")
        d30    = coin.get("price_change_percentage_30d_in_currency")

        # ATH indicator
        if ath_pass is True:
            ath_ind = GREEN("✓")
        elif ath_pass is False:
            ath_ind = RED("✗")
        else:
            ath_ind = DIM("—")

        from_ath_str = (fmt_pct(from_ath) if from_ath is not None else "   N/A  ")
        vol_mcap_str = (f"{vol_mcap:.4f}" if vol_mcap is not None else "   N/A")

        row = (
            f"  {BOLD(WHITE(symbol)):<20} "
            f"{fmt_price(coin.get('current_price')):>10}  "
            f"{pct_colored(h24):>18}  "
            f"{pct_colored(d7):>18}  "
            f"{pct_colored(d30):>18}  "
            f"{CYAN(vol_mcap_str):>18}  "
            f"{DIM(from_ath_str):>18}  "
            f"{DIM(fmt_mcap(coin.get('market_cap'))):>8}  "
            f"{ath_ind}"
        )
        print(row)

def print_summary(results, total_coins):
    total_signals = sum(len(v) for v in results.values())
    print(f"\n{'─' * 65}")
    print(BOLD(WHITE("  SUMMARY")))
    print(f"{'─' * 65}")
    print(f"  Coin di-scan  : {CYAN(str(total_coins))}")
    print(f"  Total sinyal  : {GREEN(str(total_signals)) if total_signals > 0 else DIM('0')}")
    print()
    for key, items in results.items():
        cat = CATEGORIES[key]
        is_long = cat["type"] == "long"
        count_str = GREEN(str(len(items))) if is_long else RED(str(len(items)))
        print(f"  {cat['icon']}  {cat['label']:<20} : {count_str}")
    print()
    print(DIM("  ATH ✓ = memenuhi filter tambahan (from ATH)"))
    print(DIM("  ATH ✗ = tidak memenuhi, tapi coin tetap valid (filter tambahan)"))
    print()


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    print_header()
    print(CYAN("  Mengambil data dari CoinGecko..."))

    coins = fetch_coins()
    if not coins:
        print(RED("  ✗ Gagal mengambil data."))
        return

    print(CYAN("  Menjalankan screening..."))
    results = run_screening(coins)

    # Print per category
    for cat_key in CATEGORIES:
        print_category(cat_key, results[cat_key])

    print_summary(results, len(coins))


if __name__ == "__main__":
    main()
