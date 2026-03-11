"""
Script to add Dubai, Acapulco, and Chile Open 2026 matches to atp_tennis.csv.
Fetched from ATP Tour results archive on 2026-03-02.
Run from TennisPredictor/ root: python3 scripts/add_new_matches.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "atp_tennis.csv"

# ── Player name mapping (ATP "First Last" → existing DB "Last F." format) ─────
NAMES = {
    # Dubai
    "Daniil Medvedev": "Medvedev D.",
    "Tallon Griekspoor": "Griekspoor T.",
    "Felix Auger-Aliassime": "Auger-Aliassime F.",
    "Andrey Rublev": "Rublev A.",
    "Jiri Lehecka": "Lehecka J.",
    "Jenson Brooksby": "Brooksby J.",
    "Arthur Rinderknech": "Rinderknech A.",
    "Jakub Mensik": "Mensik J.",
    "Alexander Bublik": "Bublik A.",
    "Jack Draper": "Draper J.",
    "Ugo Humbert": "Humbert U.",
    "Karen Khachanov": "Khachanov K.",
    "Alexei Popyrin": "Popyrin A.",
    "Pablo Carreno Busta": "Carreno Busta P.",
    "Giovanni Mpetshi Perricard": "Mpetshi Perricard G.",
    "Stan Wawrinka": "Wawrinka S.",
    "Juncheng Shang": "Shang J.",
    "Valentin Royer": "Royer V.",
    "Hubert Hurkacz": "Hurkacz H.",
    "Alexander Shevchenko": "Shevchenko A.",
    "Luca Nardi": "Nardi L.",
    "Zizou Bergs": "Bergs Z.",
    "Fabian Marozsan": "Marozsan F.",
    "Zhizhen Zhang": "Zhang Z.",
    "Quentin Halys": "Halys Q.",
    "Benjamin Hassan": "Hassan B.",
    "Moez Echargui": "Echargui M.",
    "Otto Virtanen": "Virtanen O.",
    "Stefanos Tsitsipas": "Tsitsipas S.",
    "Kamil Majchrzak": "Majchrzak K.",
    "Denis Shapovalov": "Shapovalov D.",
    "Botic van de Zandschulp": "Van De Zandschulp B.",
    "Jan-Lennard Struff": "Struff J-L.",
    "Christopher O'Connell": "O'Connell C.",
    "Nikoloz Basilashvili": "Basilashvili N.",
    "Jan Choinski": "Choinski J.",
    "Aleksandar Vukic": "Vukic A.",
    "Shintaro Mochizuki": "Mochizuki S.",
    "Jesper de Jong": "De Jong J.",
    "Abdulrahman Al Janahi": "Al Janahi A.",
    "Marco Trungelliti": "Trungelliti M.",
    # Acapulco
    "Alexander Zverev": "Zverev A.",
    "Casper Ruud": "Ruud C.",
    "Flavio Cobolli": "Cobolli F.",
    "Frances Tiafoe": "Tiafoe F.",
    "Miomir Kecmanovic": "Kecmanovic M.",
    "Brandon Nakashima": "Nakashima B.",
    "Valentin Vacherot": "Vacherot V.",
    "Yibing Wu": "Wu Y.",
    "Mattia Bellucci": "Bellucci M.",
    "Terence Atmane": "Atmane T.",
    "Alejandro Davidovich Fokina": "Davidovich Fokina A.",
    "Grigor Dimitrov": "Dimitrov G.",
    "Gael Monfils": "Monfils G.",
    "Corentin Moutet": "Moutet C.",
    "Nuno Borges": "Borges N.",
    "Rinky Hijikata": "Hijikata R.",
    "Sho Shimabukuro": "Shimabukuro S.",
    "Adrian Mannarino": "Mannarino A.",
    "Daniel Altmaier": "Altmaier D.",
    "Coleman Wong": "Wong C.",
    "James Duckworth": "Duckworth J.",
    "Damir Dzumhur": "Dzumhur D.",
    "Adam Walton": "Walton A.",
    "Dalibor Svrcina": "Svrcina D.",
    "Cameron Norrie": "Norrie C.",
    "Aleksandar Kovacevic": "Kovacevic A.",
    "Tristan Schoolkate": "Schoolkate T.",
    "Elias Ymer": "Ymer E.",
    "Patrick Kypson": "Kypson P.",
    "Alex de Minaur": "De Minaur A.",
    "Rafael Jodar": "Jodar R.",
    "Rodrigo Pacheco Mendez": "Pacheco Mendez R.",
    "Mariano Navone": "Navone M.",
    "Zachary Svajda": "Svajda Z.",
    "Nicolas Mejia": "Mejia N.",
    "Stefan Kozlov": "Kozlov S.",
    "Alan Magadan": "Magadan A.",
    "Alex Hernandez": "Hernandez A.",
    "Juan Pablo Ficovich": "Ficovich J.P.",
    "Bernard Tomic": "Tomic B.",
    "Rafael De Alba": "De Alba R.",
    "Mackenzie McDonald": "McDonald M.",
    # Santiago
    "Francisco Cerundolo": "Cerundolo F.",
    "Luciano Darderi": "Darderi L.",
    "Sebastian Baez": "Baez S.",
    "Alejandro Tabilo": "Tabilo A.",
    "Yannick Hanfmann": "Hanfmann Y.",
    "Emilio Nava": "Nava E.",
    "Camilo Ugo Carabelli": "Ugo Carabelli C.",
    "Andrea Pellegrino": "Pellegrino A.",
    "Vilius Gaubas": "Gaubas V.",
    "Elmer Moller": "Moller E.",
    "Cristian Garin": "Garin C.",
    "Thiago Agustin Tirante": "Tirante T.A.",
    "Adolfo Daniel Vallejo": "Vallejo A.",
    "Roman Andres Burruchaga": "Burruchaga R.",
    "Pedro Martinez": "Martinez P.",
    "Matias Soto": "Soto M.",
    "Nicolas Jarry": "Jarry N.",
    "Juan Manuel Cerundolo": "Cerundolo J.M.",
    "Dusan Lajovic": "Lajovic D.",
    "Alex Barrena": "Barrena A.",
    "Francesco Passaro": "Passaro F.",
    "Tomas Barrios Vera": "Barrios Vera T.",
    "Vit Kopriva": "Kopriva V.",
    "Ignacio Buse": "Buse I.",
    "Francisco Comesana": "Comesana F.",
    "Dino Prizmic": "Prizmic D.",
    "Matteo Berrettini": "Berrettini M.",
}


def n(name: str) -> str:
    """Map ATP full name to DB short name. Falls back to 'Last F.' convention."""
    if name in NAMES:
        return NAMES[name]
    parts = name.split()
    if len(parts) == 1:
        return name
    last = parts[-1]
    first_initial = parts[0][0]
    return f"{last} {first_initial}."


def score_fmt(s: str) -> str:
    """'6-4, 6-2' → '6-4 6-2'"""
    return s.replace(", ", " ")


def make_row(tournament, date, series, surface, round_name, winner, loser, score,
             best_of=3, court="Outdoor"):
    w, l = n(winner), n(loser)
    return {
        "Tournament": tournament,
        "Date": date,
        "Series": series,
        "Court": court,
        "Surface": surface,
        "Round": round_name,
        "Best of": best_of,
        "Player_1": w,
        "Player_2": l,
        "Winner": w,
        "Rank_1": np.nan,
        "Rank_2": np.nan,
        "Pts_1": np.nan,
        "Pts_2": np.nan,
        "Odd_1": np.nan,
        "Odd_2": np.nan,
        "Score": score,
    }


# ── Match data ─────────────────────────────────────────────────────────────────

MATCHES = []

# ── DUBAI DUTY FREE 2026 ─────────────────────────────────────────────────────
# ATP 500 | Hard outdoor | Feb 23-28, 2026
DXB = dict(tournament="Dubai Duty Free", series="ATP500", surface="Hard", court="Outdoor")

# 1st Round (R32) – Feb 23-24
for winner, loser, score in [
    ("Alexander Bublik",         "Jan-Lennard Struff",        "6-3 6-4"),
    ("Daniil Medvedev",          "Juncheng Shang",             "6-1 6-3"),
    ("Andrey Rublev",            "Valentin Royer",             "6-3 6-4"),
    ("Jakub Mensik",             "Hubert Hurkacz",             "6-4 7-6(7)"),
    ("Karen Khachanov",          "Alexander Shevchenko",       "6-7(5) 6-2 6-3"),
    ("Jiri Lehecka",             "Luca Nardi",                 "4-6 6-4 6-2"),
    ("Jenson Brooksby",          "Zizou Bergs",                "6-3 6-4"),
    ("Pablo Carreno Busta",      "Denis Shapovalov",           "6-2 6-4"),
    ("Tallon Griekspoor",        "Otto Virtanen",              "6-3 6-4"),
    ("Ugo Humbert",              "Stefanos Tsitsipas",         "6-4 7-5"),
    ("Alexei Popyrin",           "Kamil Majchrzak",            "3-6 6-3 7-5"),
    ("Arthur Rinderknech",       "Fabian Marozsan",            "3-6 6-3 6-4"),
    ("Felix Auger-Aliassime",    "Zhizhen Zhang",              "6-3 7-6(4)"),
    ("Jack Draper",              "Quentin Halys",              "7-6(8) 6-3"),
    ("Giovanni Mpetshi Perricard","Moez Echargui",             "7-6(3) 6-7(3) 7-6(4)"),
    ("Stan Wawrinka",            "Benjamin Hassan",            "7-5 6-3"),
]:
    MATCHES.append(make_row(**DXB, date="2026-02-23", round_name="1st Round", winner=winner, loser=loser, score=score))

# 2nd Round (R16) – Feb 25
for winner, loser, score in [
    ("Felix Auger-Aliassime",    "Giovanni Mpetshi Perricard", "6-4 6-4"),
    ("Tallon Griekspoor",        "Alexander Bublik",           "6-3 7-6(4)"),
    ("Daniil Medvedev",          "Stan Wawrinka",              "6-2 6-3"),
    ("Arthur Rinderknech",       "Jack Draper",                "7-5 6-7(4) 6-4"),
    ("Andrey Rublev",            "Ugo Humbert",                "6-4 6-7(5) 6-3"),
    ("Jakub Mensik",             "Alexei Popyrin",             "6-3 6-2"),
    ("Jenson Brooksby",          "Karen Khachanov",            "7-6(6) 6-4"),
    ("Jiri Lehecka",             "Pablo Carreno Busta",        "7-6(6) 6-4"),
]:
    MATCHES.append(make_row(**DXB, date="2026-02-25", round_name="2nd Round", winner=winner, loser=loser, score=score))

# Quarterfinals – Feb 26
for winner, loser, score in [
    ("Felix Auger-Aliassime",    "Jiri Lehecka",               "6-3 7-6(2)"),
    ("Daniil Medvedev",          "Jenson Brooksby",            "6-2 6-1"),
    ("Andrey Rublev",            "Arthur Rinderknech",         "6-2 6-4"),
    ("Tallon Griekspoor",        "Jakub Mensik",               "6-3 3-6 6-2"),
]:
    MATCHES.append(make_row(**DXB, date="2026-02-26", round_name="Quarterfinals", winner=winner, loser=loser, score=score))

# Semifinals – Feb 27
for winner, loser, score in [
    ("Daniil Medvedev",          "Felix Auger-Aliassime",      "6-4 6-2"),
    ("Tallon Griekspoor",        "Andrey Rublev",              "7-5 7-6(6)"),
]:
    MATCHES.append(make_row(**DXB, date="2026-02-27", round_name="Semifinals", winner=winner, loser=loser, score=score))

# Final – Feb 28 (Griekspoor withdrew, walkover to Medvedev)
MATCHES.append(make_row(**DXB, date="2026-02-28", round_name="The Final",
                        winner="Daniil Medvedev", loser="Tallon Griekspoor", score="W/O"))


# ── ABIERTO MEXICANO TELCEL (ACAPULCO) 2026 ──────────────────────────────────
# ATP 500 | Clay outdoor | Feb 23-28, 2026
ACA = dict(tournament="Acapulco Open", series="ATP500", surface="Clay", court="Outdoor")

# 1st Round (R32) – Feb 23-24
for winner, loser, score in [
    ("Alexander Zverev",         "Corentin Moutet",            "6-2 6-4"),
    ("Yibing Wu",                "Casper Ruud",                "7-6(2) 7-6(1)"),
    ("Flavio Cobolli",           "Rodrigo Pacheco Mendez",     "7-6(3) 7-6(3)"),
    ("Frances Tiafoe",           "Nuno Borges",                "6-4 6-4"),
    ("Terence Atmane",           "Grigor Dimitrov",            "6-3 6-3"),
    ("Mattia Bellucci",          "Rinky Hijikata",             "7-6(5) 6-3"),
    ("Gael Monfils",             "Damir Dzumhur",              "6-4 7-6(5)"),
    ("Sho Shimabukuro",          "Adrian Mannarino",           "6-3 6-4"),
    ("Dalibor Svrcina",          "James Duckworth",            "6-4 6-1"),
    ("Patrick Kypson",           "Alex de Minaur",             "6-1 6-7(4) 7-6(4)"),
    ("Alejandro Davidovich Fokina","Daniel Altmaier",          "7-5 6-3"),
    ("Valentin Vacherot",        "Coleman Wong",               "4-6 6-3 6-2"),
    ("Rafael Jodar",             "Cameron Norrie",             "6-3 6-2"),
    ("Miomir Kecmanovic",        "Tristan Schoolkate",         "6-2 6-2"),
    ("Aleksandar Kovacevic",     "Adam Walton",                "7-6(1) 7-6(3)"),
    ("Brandon Nakashima",        "Elias Ymer",                 "6-3 6-4"),
]:
    MATCHES.append(make_row(**ACA, date="2026-02-23", round_name="1st Round", winner=winner, loser=loser, score=score))

# 2nd Round (R16) – Feb 25
for winner, loser, score in [
    ("Miomir Kecmanovic",        "Alexander Zverev",           "6-3 6-7(3) 7-6(4)"),
    ("Mattia Bellucci",          "Alejandro Davidovich Fokina","6-3 6-3"),
    ("Flavio Cobolli",           "Dalibor Svrcina",            "6-4 6-4"),
    ("Valentin Vacherot",        "Gael Monfils",               "6-3 6-3"),
    ("Frances Tiafoe",           "Aleksandar Kovacevic",       "6-4 3-6 7-6(7)"),
    ("Terence Atmane",           "Rafael Jodar",               "6-2 4-6 6-1"),
    ("Brandon Nakashima",        "Patrick Kypson",             "6-4 6-4"),
    ("Yibing Wu",                "Sho Shimabukuro",            "6-3 7-6(4)"),
]:
    MATCHES.append(make_row(**ACA, date="2026-02-25", round_name="2nd Round", winner=winner, loser=loser, score=score))

# Quarterfinals – Feb 26
for winner, loser, score in [
    ("Flavio Cobolli",           "Yibing Wu",                  "7-6(4) 6-1"),
    ("Brandon Nakashima",        "Valentin Vacherot",          "2-6 6-2 6-3"),
    ("Frances Tiafoe",           "Mattia Bellucci",            "6-3 6-4"),
    ("Miomir Kecmanovic",        "Terence Atmane",             "6-3 6-3"),
]:
    MATCHES.append(make_row(**ACA, date="2026-02-26", round_name="Quarterfinals", winner=winner, loser=loser, score=score))

# Semifinals – Feb 27
for winner, loser, score in [
    ("Flavio Cobolli",           "Miomir Kecmanovic",          "7-6(5) 3-6 6-4"),
    ("Frances Tiafoe",           "Brandon Nakashima",          "3-6 7-6(6) 6-4"),
]:
    MATCHES.append(make_row(**ACA, date="2026-02-27", round_name="Semifinals", winner=winner, loser=loser, score=score))

# Final – Feb 28
MATCHES.append(make_row(**ACA, date="2026-02-28", round_name="The Final",
                        winner="Flavio Cobolli", loser="Frances Tiafoe", score="7-6(4) 6-4"))


# ── BCI SEGUROS CHILE OPEN (SANTIAGO) 2026 ───────────────────────────────────
# ATP 250 | Clay outdoor | Feb 23-28, 2026
CHI = dict(tournament="Chile Open", series="ATP250", surface="Clay", court="Outdoor")

# 1st Round (R32) – Feb 23 (seeds 1-4 had byes; 12 non-bye matches)
for winner, loser, score in [
    ("Emilio Nava",              "Matteo Berrettini",          "6-3 6-4"),
    ("Alejandro Tabilo",         "Tomas Barrios Vera",         "7-5 6-3"),
    ("Cristian Garin",           "Juan Manuel Cerundolo",      "3-6 6-3 6-3"),
    ("Vilius Gaubas",            "Matias Soto",                "6-2 6-3"),
    ("Elmer Moller",             "Roman Andres Burruchaga",    "7-6(4) 0-6 6-4"),
    ("Mariano Navone",           "Vit Kopriva",                "6-3 6-0"),
    ("Thiago Agustin Tirante",   "Ignacio Buse",               "2-6 7-6(0) 7-6(2)"),
    ("Adolfo Daniel Vallejo",    "Francesco Passaro",          "6-3"),
    ("Francisco Comesana",       "Pedro Martinez",             "6-4 2-6 7-6(4)"),
    ("Yannick Hanfmann",         "Dusan Lajovic",              "6-0 6-3"),
    ("Andrea Pellegrino",        "Alex Barrena",               "6-2 2-6 6-1"),
    ("Dino Prizmic",             "Nicolas Jarry",              "6-3 5-7 6-2"),
]:
    MATCHES.append(make_row(**CHI, date="2026-02-23", round_name="1st Round", winner=winner, loser=loser, score=score))

# 2nd Round (R16) – Feb 25 (seeds 1-4 enter; 8 matches)
for winner, loser, score in [
    ("Francisco Cerundolo",      "Elmer Moller",               "6-2 6-2"),
    ("Sebastian Baez",           "Cristian Garin",             "7-6(2) 1-6 7-5"),
    ("Alejandro Tabilo",         "Thiago Agustin Tirante",     "4-6 6-3 6-3"),
    ("Emilio Nava",              "Adolfo Daniel Vallejo",      "7-5 6-3"),
    ("Luciano Darderi",          "Mariano Navone",             "6-3 3-6 6-4"),
    ("Yannick Hanfmann",         "Camilo Ugo Carabelli",       "6-4 6-3"),
    ("Andrea Pellegrino",        "Francisco Comesana",         "7-6(3) 6-7(2) 6-3"),
    ("Vilius Gaubas",            "Dino Prizmic",               "5-7 7-5 6-3"),
]:
    MATCHES.append(make_row(**CHI, date="2026-02-25", round_name="2nd Round", winner=winner, loser=loser, score=score))

# Quarterfinals – Feb 26
for winner, loser, score in [
    ("Francisco Cerundolo",      "Emilio Nava",                "6-1 6-1"),
    ("Luciano Darderi",          "Andrea Pellegrino",          "6-3 3-6 6-2"),
    ("Sebastian Baez",           "Alejandro Tabilo",           "7-6(2) 6-1"),
    ("Yannick Hanfmann",         "Vilius Gaubas",              "3-6 6-2 6-2"),
]:
    MATCHES.append(make_row(**CHI, date="2026-02-26", round_name="Quarterfinals", winner=winner, loser=loser, score=score))

# Semifinals – Feb 27
for winner, loser, score in [
    ("Yannick Hanfmann",         "Francisco Cerundolo",        "6-3 6-4"),
    ("Luciano Darderi",          "Sebastian Baez",             "6-4 6-3"),
]:
    MATCHES.append(make_row(**CHI, date="2026-02-27", round_name="Semifinals", winner=winner, loser=loser, score=score))

# Final – Feb 28
MATCHES.append(make_row(**CHI, date="2026-02-28", round_name="The Final",
                        winner="Luciano Darderi", loser="Yannick Hanfmann", score="7-6 7-5"))


# ── Merge and save ─────────────────────────────────────────────────────────────
def main():
    new_df = pd.DataFrame(MATCHES)
    new_df["Date"] = pd.to_datetime(new_df["Date"])

    existing = pd.read_csv(CSV_PATH, low_memory=False)
    existing["Date"] = pd.to_datetime(existing["Date"], errors="coerce")

    # Dedup: drop new rows that already exist (same tournament+date+players)
    key_cols = ["Tournament", "Date", "Player_1", "Player_2"]
    existing_keys = set(
        zip(existing["Tournament"], existing["Date"].astype(str),
            existing["Player_1"], existing["Player_2"])
    )
    new_df = new_df[~new_df.apply(
        lambda r: (r["Tournament"], str(r["Date"]), r["Player_1"], r["Player_2"]) in existing_keys, axis=1
    )]

    print(f"Existing rows:  {len(existing):,}")
    print(f"New rows added: {len(new_df)}")

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.sort_values("Date").reset_index(drop=True)

    combined["Date"] = combined["Date"].dt.strftime("%Y-%m-%d")
    combined.to_csv(CSV_PATH, index=False)

    cutoff = combined["Date"].max()
    print(f"Saved → {CSV_PATH}")
    print(f"New last date:  {cutoff}")
    print(f"Total rows:     {len(combined):,}")
    print()
    print("Next steps — run from backend/ with venv activated:")
    print("  python -m pipeline.clean")
    print("  python -m pipeline.elo")
    print("  python -m pipeline.features")
    print("  python -m db.seed")


if __name__ == "__main__":
    main()
