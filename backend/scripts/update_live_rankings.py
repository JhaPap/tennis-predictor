"""
Update player current_rank values from live ATP rankings.
Clears all existing ranks first, then sets the top 100 from live data.
Run from backend/ with venv active:
    python scripts/update_live_rankings.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import SessionLocal
from db.models import Player

# Live ATP rankings as of 2026-02-26
LIVE_RANKINGS = [
    (1,   "Carlos Alcaraz"),
    (2,   "Jannik Sinner"),
    (3,   "Novak Djokovic"),
    (4,   "Alexander Zverev"),
    (5,   "Lorenzo Musetti"),
    (6,   "Alex de Minaur"),
    (7,   "Taylor Fritz"),
    (8,   "Ben Shelton"),
    (9,   "Felix Auger-Aliassime"),
    (10,  "Alexander Bublik"),
    (11,  "Daniil Medvedev"),
    (12,  "Jakub Mensik"),
    (13,  "Casper Ruud"),
    (14,  "Jack Draper"),
    (15,  "Karen Khachanov"),
    (16,  "Andrey Rublev"),
    (17,  "Holger Rune"),
    (18,  "Alejandro Davidovich Fokina"),
    (19,  "Francisco Cerundolo"),
    (20,  "Flavio Cobolli"),
    (21,  "Luciano Darderi"),
    (22,  "Jiri Lehecka"),
    (23,  "Tommy Paul"),
    (24,  "Valentin Vacherot"),
    (25,  "Learner Tien"),
    (26,  "Tallon Griekspoor"),
    (27,  "Frances Tiafoe"),
    (28,  "Arthur Rinderknech"),
    (29,  "Cameron Norrie"),
    (30,  "Tomas Martin Etcheverry"),
    (31,  "Arthur Fils"),
    (32,  "Brandon Nakashima"),
    (33,  "Corentin Moutet"),
    (34,  "Ugo Humbert"),
    (35,  "Joao Fonseca"),
    (36,  "Jaume Munar"),
    (37,  "Sebastian Korda"),
    (38,  "Gabriel Diallo"),
    (39,  "Denis Shapovalov"),
    (40,  "Jenson Brooksby"),
    (41,  "Alejandro Tabilo"),
    (42,  "Grigor Dimitrov"),
    (43,  "Stefanos Tsitsipas"),
    (44,  "Alex Michelsen"),
    (45,  "Alexei Popyrin"),
    (46,  "Fabian Marozsan"),
    (47,  "Zizou Bergs"),
    (48,  "Adrian Mannarino"),
    (49,  "Nuno Borges"),
    (50,  "Tomas Machac"),
    (51,  "Marin Cilic"),
    (52,  "Terence Atmane"),
    (53,  "Giovanni Mpetshi Perricard"),
    (54,  "Daniel Altmaier"),
    (55,  "Marton Fucsovics"),
    (56,  "Kamil Majchrzak"),
    (57,  "Botic van de Zandschulp"),
    (58,  "Valentin Royer"),
    (59,  "Lorenzo Sonego"),
    (60,  "Sebastian Baez"),
    (61,  "Vit Kopriva"),
    (62,  "Ignacio Buse"),
    (63,  "Damir Dzumhur"),
    (64,  "Matteo Berrettini"),
    (65,  "Camilo Ugo Carabelli"),
    (66,  "Reilly Opelka"),
    (67,  "Marcos Giron"),
    (68,  "Juan Manuel Cerundolo"),
    (69,  "Miomir Kecmanovic"),
    (70,  "Hubert Hurkacz"),
    (71,  "Aleksandar Kovacevic"),
    (72,  "Ethan Quinn"),
    (73,  "Thiago Agustin Tirante"),
    (74,  "Emilio Nava"),
    (75,  "Arthur Cazaux"),
    (76,  "Raphael Collignon"),
    (77,  "Eliot Spizzirri"),
    (78,  "Mariano Navone"),
    (79,  "Yannick Hanfmann"),
    (80,  "Jan-Lennard Struff"),
    (81,  "Alexandre Muller"),
    (82,  "Francisco Comesana"),
    (83,  "James Duckworth"),
    (84,  "Filip Misolic"),
    (85,  "Matteo Arnaldi"),
    (86,  "Jesper de Jong"),
    (87,  "Jacob Fearnley"),
    (88,  "Alexander Shevchenko"),
    (89,  "Aleksandar Vukic"),
    (90,  "Cristian Garin"),
    (91,  "Adam Walton"),
    (92,  "Stan Wawrinka"),
    (93,  "Roberto Bautista Agut"),
    (94,  "Mattia Bellucci"),
    (95,  "Patrick Kypson"),
    (96,  "Alexander Blockx"),
    (97,  "Hugo Gaston"),
    (98,  "Roman Andres Burruchaga"),
    (99,  "Zachary Svajda"),
    (100, "Carlos Taberner"),
]

# Manual name corrections for compound surnames and edge cases
# Full name → DB format
MANUAL = {
    "Carlos Alcaraz":              "Alcaraz C.",
    "Jannik Sinner":               "Sinner J.",
    "Novak Djokovic":              "Djokovic N.",
    "Alexander Zverev":            "Zverev A.",
    "Lorenzo Musetti":             "Musetti L.",
    "Alex de Minaur":              "De Minaur A.",
    "Taylor Fritz":                "Fritz T.",
    "Ben Shelton":                 "Shelton B.",
    "Felix Auger-Aliassime":       "Auger-Aliassime F.",
    "Alexander Bublik":            "Bublik A.",
    "Daniil Medvedev":             "Medvedev D.",
    "Casper Ruud":                 "Ruud C.",
    "Jack Draper":                 "Draper J.",
    "Karen Khachanov":             "Khachanov K.",
    "Andrey Rublev":               "Rublev A.",
    "Holger Rune":                 "Rune H.",
    "Alejandro Davidovich Fokina": "Davidovich Fokina A.",
    "Francisco Cerundolo":         "Cerundolo F.",
    "Flavio Cobolli":              "Cobolli F.",
    "Luciano Darderi":             "Darderi L.",
    "Jiri Lehecka":                "Lehecka J.",
    "Tommy Paul":                  "Paul T.",
    "Valentin Vacherot":           "Vacherot V.",
    "Tallon Griekspoor":           "Griekspoor T.",
    "Frances Tiafoe":              "Tiafoe F.",
    "Arthur Rinderknech":          "Rinderknech A.",
    "Cameron Norrie":              "Norrie C.",
    "Tomas Martin Etcheverry":     "Etcheverry T.",
    "Arthur Fils":                 "Fils A.",
    "Brandon Nakashima":           "Nakashima B.",
    "Corentin Moutet":             "Moutet C.",
    "Ugo Humbert":                 "Humbert U.",
    "Jaume Munar":                 "Munar J.",
    "Sebastian Korda":             "Korda S.",
    "Gabriel Diallo":              "Diallo G.",
    "Denis Shapovalov":            "Shapovalov D.",
    "Jenson Brooksby":             "Brooksby J.",
    "Alejandro Tabilo":            "Tabilo A.",
    "Grigor Dimitrov":             "Dimitrov G.",
    "Stefanos Tsitsipas":          "Tsitsipas S.",
    "Alex Michelsen":              "Michelsen A.",
    "Alexei Popyrin":              "Popyrin A.",
    "Fabian Marozsan":             "Marozsan F.",
    "Zizou Bergs":                 "Bergs Z.",
    "Adrian Mannarino":            "Mannarino A.",
    "Nuno Borges":                 "Borges N.",
    "Tomas Machac":                "Machac T.",
    "Marin Cilic":                 "Cilic M.",
    "Daniel Altmaier":             "Altmaier D.",
    "Marton Fucsovics":            "Fucsovics M.",
    "Kamil Majchrzak":             "Majchrzak K.",
    "Botic van de Zandschulp":     "Van De Zandschulp B.",
    "Valentin Royer":              "Royer V.",
    "Lorenzo Sonego":              "Sonego L.",
    "Sebastian Baez":              "Baez S.",
    "Damir Dzumhur":               "Dzumhur D.",
    "Matteo Berrettini":           "Berrettini M.",
    "Camilo Ugo Carabelli":        "Ugo Carabelli C.",
    "Reilly Opelka":               "Opelka R.",
    "Marcos Giron":                "Giron M.",
    "Juan Manuel Cerundolo":       "Cerundolo J.M.",
    "Miomir Kecmanovic":           "Kecmanovic M.",
    "Hubert Hurkacz":              "Hurkacz H.",
    "Aleksandar Kovacevic":        "Kovacevic A.",
    "Thiago Agustin Tirante":      "Tirante T.A.",
    "Arthur Cazaux":               "Cazaux A.",
    "Mariano Navone":              "Navone M.",
    "Yannick Hanfmann":            "Hanfmann Y.",
    "Jan-Lennard Struff":          "Struff J.L.",
    "Alexandre Muller":            "Muller A.",
    "Francisco Comesana":          "Comesana F.",
    "James Duckworth":             "Duckworth J.",
    "Filip Misolic":               "Misolic F.",
    "Matteo Arnaldi":              "Arnaldi M.",
    "Jesper de Jong":              "De Jong J.",
    "Alexander Shevchenko":        "Shevchenko A.",
    "Aleksandar Vukic":            "Vukic A.",
    "Cristian Garin":              "Garin C.",
    "Adam Walton":                 "Walton A.",
    "Stan Wawrinka":               "Wawrinka S.",
    "Roberto Bautista Agut":       "Bautista Agut R.",
    "Mattia Bellucci":             "Bellucci M.",
    "Hugo Gaston":                 "Gaston H.",
    "Carlos Taberner":             "Taberner C.",
    "Giovanni Mpetshi Perricard":  "Mpetshi Perricard G.",
    "Joao Fonseca":                "Fonseca J.",
    "Learner Tien":                "Tien L.",
    "Jakub Mensik":                "Mensik J.",
    "Ignacio Buse":                "Buse I.",
    "Vit Kopriva":                 "Kopriva V.",
    "Ethan Quinn":                 "Quinn E.",
    "Emilio Nava":                 "Nava E.",
    "Raphael Collignon":           "Collignon R.",
    "Eliot Spizzirri":             "Spizzirri E.",
    "Jacob Fearnley":              "Fearnley J.",
    "Patrick Kypson":              "Kypson P.",
    "Alexander Blockx":            "Blockx A.",
    "Roman Andres Burruchaga":     "Burruchaga R.A.",
    "Zachary Svajda":              "Svajda Z.",
    "Terence Atmane":              "Atmane T.",
}


def heuristic_normalize(full_name: str) -> str:
    """Fallback: last word = surname, first word initial."""
    parts = full_name.split()
    return f"{parts[-1]} {parts[0][0]}."


def main():
    db = SessionLocal()
    try:
        # Step 1: Clear ALL current ranks
        db.query(Player).update({"current_rank": None})
        db.commit()
        print("Cleared all existing ranks.")

        # Build a lookup: db_name_lower → Player
        all_players = db.query(Player).all()
        by_name = {p.name.lower(): p for p in all_players}

        matched = 0
        unmatched = []

        for rank, full_name in LIVE_RANKINGS:
            db_name = MANUAL.get(full_name) or heuristic_normalize(full_name)
            player = by_name.get(db_name.lower())

            if player is None:
                # Try last-name-only fallback
                last = db_name.split()[0].lower()
                candidates = [p for name, p in by_name.items() if name.startswith(last)]
                if len(candidates) == 1:
                    player = candidates[0]

            if player:
                player.current_rank = rank
                matched += 1
                print(f"  #{rank:3d}  {full_name:35s} → {player.name}")
            else:
                unmatched.append((rank, full_name, db_name))

        db.commit()

        print(f"\nMatched: {matched}/100")
        if unmatched:
            print(f"\nUnmatched ({len(unmatched)}) — add to MANUAL dict:")
            for rank, full, db_fmt in unmatched:
                print(f"  #{rank:3d}  {full:35s}  (tried: '{db_fmt}')")

    finally:
        db.close()


if __name__ == "__main__":
    main()
