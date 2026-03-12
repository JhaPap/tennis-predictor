import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Database,
  Brain,
  BarChart3,
  Target,
  Layers,
  Activity,
  Gauge,
  GitBranch,
  Shield,
  Sparkles,
  Swords,
  TrendingUp,
  CalendarDays,
  History,
  Users,
  AlertTriangle,
  ListOrdered,
} from "lucide-react";

const FEATURES = [
  {
    category: "Elo Ratings",
    count: 2,
    items: ["Overall Elo difference", "Surface-specific Elo difference"],
  },
  {
    category: "Rankings",
    count: 3,
    items: ["ATP rank difference", "Log rank ratio", "Points difference"],
  },
  {
    category: "Win Rates",
    count: 10,
    items: [
      "Overall win rate (both players)",
      "Surface win rate (both players)",
      "Last 20 matches form",
      "Last 5 matches form",
      "Overall & surface differentials",
    ],
  },
  {
    category: "Head-to-Head",
    count: 4,
    items: [
      "H2H wins & total matches",
      "Surface-specific H2H record",
      "H2H win percentage",
    ],
  },
  {
    category: "Match Context",
    count: 7,
    items: [
      "Surface type (Hard, Clay, Grass)",
      "Grand Slam & Best-of-5 flags",
      "Indoor/outdoor indicator",
      "Round & tournament tier",
    ],
  },
  {
    category: "Activity & Rest",
    count: 6,
    items: [
      "Days since last match (both players)",
      "Year-to-date match count",
      "Surface-specific match volume",
    ],
  },
  {
    category: "Tournament-Specific",
    count: 5,
    items: [
      "Historical win rate at this tournament",
      "Matches played at this tournament",
      "Tournament win rate differential",
    ],
  },
  {
    category: "Serve & Return",
    count: 12,
    items: [
      "Ace rate (both players)",
      "Double fault rate (both players)",
      "First serve percentage (both players)",
      "First & second serve win % (both players)",
      "Return points won % (both players)",
      "Serve & return edge differentials",
    ],
  },
  {
    category: "Clutch Performance",
    count: 5,
    items: [
      "Break point save rate (both players)",
      "Break point conversion rate (both players)",
      "BP edge: save rate vs opponent conversion",
    ],
  },
  {
    category: "Net Play",
    count: 2,
    items: [
      "Net points win rate (both players)",
    ],
  },
  {
    category: "Shot Quality",
    count: 4,
    items: [
      "Unforced error rate per point (both players)",
      "Winner rate per point (both players)",
    ],
  },
];

const STATS = [
  { label: "Matches Analyzed", value: "67,199", icon: Database, color: "text-blue-400" },
  { label: "Active Players", value: "457", icon: Activity, color: "text-orange-400" },
  { label: "Engineered Features", value: "60", icon: Layers, color: "text-purple-400" },
  { label: "Test Accuracy", value: "65.0%", icon: Target, color: "text-red-400" },
  { label: "AUC Score", value: "0.722", icon: Gauge, color: "text-cyan-400" },
  { label: "Years of Data", value: "26+", icon: BarChart3, color: "text-primary" },
];

const PLATFORM_FEATURES = [
  {
    icon: Target,
    color: "bg-blue-500/20 text-blue-400",
    title: "Match Predictor",
    description:
      "Select any two active ATP players, set the surface, series, and round, and receive an instant win probability with a confidence rating (High/Medium/Low) based on data quality and prediction margin.",
  },
  {
    icon: AlertTriangle,
    color: "bg-orange-500/20 text-orange-400",
    title: "Upset Alert",
    description:
      "When the higher-ranked player holds ≥40% win probability, an orange Upset Alert badge fires automatically — flagging matches where the data suggests the favourite is more vulnerable than their ranking implies.",
  },
  {
    icon: Sparkles,
    color: "bg-primary/20 text-primary",
    title: "AI Match Analysis",
    description:
      "Powered by Claude (Anthropic), a one-click narrative breaks down why the model favours one player: surface Elo gaps, recent form, H2H trends, and serve/return edges — explained in plain English.",
  },
  {
    icon: Swords,
    color: "bg-yellow-500/20 text-yellow-400",
    title: "Bracket Simulator",
    description:
      "Seed any 8 players into a tournament draw and run 10,000 Monte Carlo simulations to estimate each player's title probability. Seeding follows the standard ATP draw structure: 1 vs 8, 4 vs 5, 3 vs 6, 2 vs 7 — keeping the top seeds on opposite halves.",
  },
  {
    icon: Users,
    color: "bg-purple-500/20 text-purple-400",
    title: "Player Profiles",
    description:
      "Each player page shows overall and surface Elo ratings, serve & return stats benchmarked against league averages, an Elo history chart, and a Form Heatmap — colour-coded win/loss dots grouped by month across the last 12 months of match data.",
  },
  {
    icon: TrendingUp,
    color: "bg-green-500/20 text-green-400",
    title: "Elo Trend Arrows",
    description:
      "The leaderboard shows a Trend column (▲/▼) reflecting each player's Elo change over their last 20 matches — a recent-form indicator independent of ATP points or ranking movements.",
  },
  {
    icon: History,
    color: "bg-cyan-500/20 text-cyan-400",
    title: "Model Calibration Chart",
    description:
      "The History page includes a calibration chart built from the 2024+ test set. It plots actual win rate against predicted confidence in 5% buckets — showing whether a \"70% prediction\" truly wins 70% of the time.",
  },
  {
    icon: ListOrdered,
    color: "bg-rose-500/20 text-rose-400",
    title: "H2H Match Detail",
    description:
      "Clicking the Head-to-Head card on any prediction opens a full history of meetings: tournament, surface, round, score, and ATP rankings at the time of each match.",
  },
  {
    icon: CalendarDays,
    color: "bg-indigo-500/20 text-indigo-400",
    title: "Featured Matchups",
    description:
      "The home page surfaces recent top-100 matchups from the database. Each row shows the score and surface with a direct \"Predict\" link that pre-fills both players on the prediction page.",
  },
];

export default function AboutPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          About Tennis Predictor
        </h1>
        <p className="text-muted-foreground mt-2 max-w-2xl leading-relaxed">
          An ML-powered ATP match prediction platform built on 26 years of
          professional tennis data. XGBoost + Elo ratings drive a 65.0% accurate
          model across 60 engineered features — including serve/return stats,
          break-point clutch performance, net play, and shot quality from the Match
          Charting Project. Claude (Anthropic) layers natural-language analysis on top.
          A suite of interactive tools — bracket simulator, form heatmaps, calibration
          charts, and more — make the model's reasoning explorable and transparent.
        </p>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        {STATS.map((stat) => (
          <Card key={stat.label} className="border-0">
            <CardContent className="pt-5 pb-4 text-center space-y-1">
              <stat.icon className={`h-5 w-5 mx-auto ${stat.color}`} />
              <div className="text-2xl font-bold tracking-tight">{stat.value}</div>
              <div className="text-xs text-muted-foreground">{stat.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* How It Works */}
      <section className="space-y-5">
        <h2 className="text-2xl font-bold tracking-tight">How It Works</h2>
        <div className="grid gap-5 sm:grid-cols-2 md:grid-cols-4">
          <Card className="border-0">
            <CardContent className="pt-6 space-y-3">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-blue-500/20 text-blue-400">
                <Database className="h-5 w-5" />
              </div>
              <h3 className="font-semibold">1. Data Collection</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Every ATP match from 2000 to 2026 is ingested — 67,199
                matches across Hard, Clay, Grass, and Carpet courts. Players
                active since 2023 (457 total) are eligible for predictions.
              </p>
            </CardContent>
          </Card>
          <Card className="border-0">
            <CardContent className="pt-6 space-y-3">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-purple-500/20 text-purple-400">
                <Brain className="h-5 w-5" />
              </div>
              <h3 className="font-semibold">2. Feature Engineering</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                60 features are computed per match: Elo ratings (overall +
                per-surface), rankings, head-to-head records, recent form,
                tournament history, match context, serve &amp; return stats,
                break-point clutch rates, net play win rate, and shot quality
                metrics — all sourced from the Match Charting Project. Every
                feature uses only pre-match data to prevent leakage.
              </p>
            </CardContent>
          </Card>
          <Card className="border-0">
            <CardContent className="pt-6 space-y-3">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-primary/20 text-primary">
                <Target className="h-5 w-5" />
              </div>
              <h3 className="font-semibold">3. Model Prediction</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                An XGBoost classifier, tuned with 200 Optuna trials and
                calibrated with isotonic regression, outputs a win probability.
                Achieves 65.0% accuracy and 0.722 AUC on held-out 2024+
                matches.
              </p>
            </CardContent>
          </Card>
          <Card className="border-0">
            <CardContent className="pt-6 space-y-3">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-rose-500/20 text-rose-400">
                <Sparkles className="h-5 w-5" />
              </div>
              <h3 className="font-semibold">4. AI Analysis</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Claude (Anthropic) receives the full feature vector and
                prediction output and generates a natural-language breakdown
                — explaining surface Elo gaps, form trends, and H2H edges in
                plain English.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Platform Features */}
      <section className="space-y-5">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Platform Features</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Every tool built into the app and what it does.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PLATFORM_FEATURES.map(({ icon: Icon, color, title, description }) => (
            <Card key={title} className="border-0">
              <CardContent className="pt-5 space-y-3">
                <div className={`inline-flex items-center justify-center h-9 w-9 rounded-lg ${color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* The Model */}
      <section className="space-y-5">
        <h2 className="text-2xl font-bold tracking-tight">The Model</h2>
        <div className="grid gap-5 md:grid-cols-2">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-purple-400" />
                Training Pipeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
              <p>
                The model uses a{" "}
                <span className="font-medium text-foreground">strict temporal split</span> to
                simulate real-world usage:
              </p>
              <ul className="space-y-1.5 ml-1">
                <li className="flex gap-2">
                  <span className="text-primary font-semibold shrink-0">Train</span>
                  <span>Matches through 2021 (≈9,200 active-player matches)</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary font-semibold shrink-0">Validate</span>
                  <span>2022–2023 (≈4,950 matches) for hyperparameter tuning</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary font-semibold shrink-0">Test</span>
                  <span>2024+ (≈5,550 matches) for final evaluation and calibration chart</span>
                </li>
              </ul>
              <p>
                Hyperparameters are optimized with{" "}
                <span className="font-medium text-foreground">Optuna</span> (200
                trials, maximizing validation AUC). Predicted probabilities are
                then calibrated with{" "}
                <span className="font-medium text-foreground">isotonic regression</span> so
                that a 70% prediction truly wins about 70% of the time — verifiable
                on the History page&apos;s calibration chart.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-amber-400" />
                Elo Rating System
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
              <p>
                Each player has{" "}
                <span className="font-medium text-foreground">5 independent Elo tracks</span>:
                one overall rating and one for each surface (Hard, Clay,
                Grass, Carpet). All start at 1500 and update after every match.
              </p>
              <p>
                K-factors scale by tournament importance so that Grand Slam
                results move ratings more than smaller events:
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <div className="flex justify-between">
                  <span>Grand Slam</span>
                  <span className="font-mono font-medium text-foreground">K=32</span>
                </div>
                <div className="flex justify-between">
                  <span>Masters 1000</span>
                  <span className="font-mono font-medium text-foreground">K=24</span>
                </div>
                <div className="flex justify-between">
                  <span>Masters Cup</span>
                  <span className="font-mono font-medium text-foreground">K=20</span>
                </div>
                <div className="flex justify-between">
                  <span>ATP 500</span>
                  <span className="font-mono font-medium text-foreground">K=16</span>
                </div>
                <div className="flex justify-between">
                  <span>ATP 250</span>
                  <span className="font-mono font-medium text-foreground">K=10</span>
                </div>
              </div>
              <p>
                The leaderboard&apos;s <span className="font-medium text-foreground">Trend column</span> shows
                each player&apos;s Elo change over their last 20 matches as a
                recent-form signal, separate from the underlying ATP rankings.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* AI Analysis */}
      <section className="space-y-5">
        <h2 className="text-2xl font-bold tracking-tight">AI Analysis with Claude</h2>
        <Card className="border-0">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-rose-500/20 text-rose-400 shrink-0">
                <Sparkles className="h-5 w-5" />
              </div>
              <div className="space-y-2 text-sm text-muted-foreground leading-relaxed">
                <p>
                  <span className="font-medium text-foreground">Claude (Anthropic) generates match narratives on demand.</span>{" "}
                  After a prediction is made, clicking &quot;Generate AI Analysis&quot; sends the
                  full feature vector — Elo differentials, surface win rates, H2H record,
                  serve stats, and confidence level — to Claude as structured context.
                </p>
                <p>
                  The model returns a paragraph-length breakdown explaining the key edges
                  in plain English: why one player&apos;s surface Elo advantage matters, whether
                  recent form contradicts the historical H2H, and what the serve/return
                  numbers suggest about how the match will play out.
                </p>
                <p>
                  This combines structured ML output with LLM reasoning — the XGBoost
                  model decides <em>who</em> wins; Claude explains <em>why</em>.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Features breakdown */}
      <section className="space-y-5">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            60 Engineered Features
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Every prediction is built from these feature categories, all
            computed from pre-match data only. Clutch, net play, and shot
            quality stats are sourced from the Match Charting Project.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ category, count, items }) => (
            <Card key={category} className="border-0">
              <CardContent className="pt-5 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-sm">{category}</h3>
                  <span className="text-xs text-muted-foreground rounded-full bg-muted px-2 py-0.5">
                    {count}
                  </span>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {items.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="text-primary mt-1.5 shrink-0">&#8226;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Anti-leakage & Integrity */}
      <section className="space-y-5">
        <h2 className="text-2xl font-bold tracking-tight">Data Integrity</h2>
        <Card className="border-0">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-amber-500/20 text-amber-400 shrink-0">
                <Shield className="h-5 w-5" />
              </div>
              <div className="space-y-2 text-sm text-muted-foreground leading-relaxed">
                <p>
                  <span className="font-medium text-foreground">Anti-leakage by design.</span>{" "}
                  Every feature — Elo ratings, win rates, H2H records — is
                  computed from a player&apos;s record <em>before</em> the match
                  in question. Pre-match snapshots are saved during Elo
                  computation and used as the ground truth for training.
                </p>
                <p>
                  The temporal train/test split ensures the model is never
                  evaluated on data it has seen during training. The test set
                  (2024+) simulates predicting future matches with only
                  historical information available — and its accuracy is
                  verifiable in the live calibration chart on the History page.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Tech Stack */}
      <section className="space-y-5 pb-4">
        <h2 className="text-2xl font-bold tracking-tight">Tech Stack</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card className="border-0">
            <CardContent className="pt-5 space-y-2">
              <h3 className="font-semibold text-sm">Backend</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Python, FastAPI, SQLAlchemy, SQLite, XGBoost, scikit-learn,
                Optuna, Pandas, NumPy, Anthropic SDK (Claude)
              </p>
            </CardContent>
          </Card>
          <Card className="border-0">
            <CardContent className="pt-5 space-y-2">
              <h3 className="font-semibold text-sm">Frontend</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui,
                TanStack React Query, Recharts, Lucide Icons
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
