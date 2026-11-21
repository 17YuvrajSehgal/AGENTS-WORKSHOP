"""Check the AIDev v5 dataset card's numbers against the pinned data.

Reads all_pull_request.parquet remotely (only the columns needed) and the
downloaded AIDev-pop tables locally. Prints every count next to the number
the dataset card (README at b8dc67d) states, and writes
data/p1_counts.json. Nothing here interprets a mismatch; it only reports.

Usage: python -I AGENTS-WORKSHOP/analysis/p1_counts.py
"""

import json
from pathlib import Path

import pandas as pd
from huggingface_hub import HfFileSystem

REV = "b37f9fd1613cfec55886105bb76721918d015dc7"  # tag v5
ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "data" / "aidev-v5"

# README "Quick Look" table, copied by hand from data/aidev-readme-b8dc67d.md
README = {
    "OpenAI Codex": (3_844_602, 7.3, 6.5, 86.2, 237_223, 355_920),
    "Copilot": (1_581_924, 14.2, 15.8, 69.9, 0, 347_971),
    "Claude Code": (1_567_100, 4.2, 7.8, 88.0, 114_516, 174_038),
    "Cursor": (317_453, 28.3, 14.3, 57.4, 62_246, 81_915),
    "Google Jules": (296_411, 21.0, 15.6, 63.4, 18, 41_125),
    "Devin": (77_791, 17.0, 23.3, 59.6, 0, 10_321),
    "Total": (7_685_281, 9.6, 9.5, 80.9, 393_349, 961_168),
}
COLS = ("prs", "pct_open", "pct_closed", "pct_merged", "developers", "repos")


def outcome_shares(df):
    merged = df["merged_at"].notna()
    is_open = df["state"].eq("open")
    closed = ~is_open & ~merged
    n = len(df)
    return (round(100 * is_open.sum() / n, 1), round(100 * closed.sum() / n, 1),
            round(100 * merged.sum() / n, 1))


def main():
    out = {"revision": REV}
    fs = HfFileSystem()
    with fs.open(f"datasets/hao-li/AIDev@{REV}/all_pull_request.parquet") as f:
        allpr = pd.read_parquet(
            f, columns=["id", "agent", "user", "repo_id", "state", "merged_at"])
    out["all_pr_ids_distinct"] = int(allpr["id"].nunique())
    print("all_pull_request rows:", len(allpr), "distinct ids:", out["all_pr_ids_distinct"])
    out["agent_values"] = allpr["agent"].value_counts().to_dict()
    print("agent values:", out["agent_values"])
    print("state values:", allpr["state"].value_counts().to_dict())

    rows = {}
    for agent, g in list(allpr.groupby("agent")) + [("Total", allpr)]:
        o, c, m = outcome_shares(g)
        rows[agent] = {"prs": len(g), "pct_open": o, "pct_closed": c,
                       "pct_merged": m, "distinct_user": g["user"].nunique(),
                       "repos": g["repo_id"].nunique()}
    out["quick_look_measured"] = rows

    print(f"\n{'agent':14s} {'field':11s} {'README':>11s} {'data':>11s}")
    for agent, ref in README.items():
        # the data spells agents with underscores (OpenAI_Codex, Claude_Code, ...)
        got = rows.get(agent.replace(" ", "_")) or rows.get(agent)
        if got is None:
            print(f"{agent:14s} NOT FOUND in agent column")
            continue
        for col, want in zip(COLS, ref):
            have = got["distinct_user" if col == "developers" else col]
            flag = "" if have == want else "   <-- differs"
            print(f"{agent:14s} {col:11s} {want:>11,} {have:>11,}{flag}")

    allrepo = pd.read_parquet(LOCAL / "all_repository.parquet",
                              columns=["id", "stars"])
    pr_repos = set(allpr["repo_id"].unique())
    out["all_repository_rows"] = len(allrepo)
    out["all_repository_distinct_id"] = int(allrepo["id"].nunique())
    out["pr_repo_ids_missing_from_all_repository"] = len(
        pr_repos - set(allrepo["id"]))
    out["all_repository_ids_without_prs"] = len(set(allrepo["id"]) - pr_repos)
    alluser = pd.read_parquet(LOCAL / "all_user.parquet", columns=["login"])
    out["all_user_rows"] = len(alluser)
    out["all_user_distinct_login"] = int(alluser["login"].nunique())
    print()
    for k in ("all_repository_rows", "all_repository_distinct_id",
              "pr_repo_ids_missing_from_all_repository",
              "all_repository_ids_without_prs", "all_user_rows",
              "all_user_distinct_login"):
        print(f"{k:45s} {out[k]:>11,}")

    # AIDev-pop: every repo must have more than 100 stars
    pop = pd.read_parquet(LOCAL / "pull_request.parquet",
                          columns=["id", "agent", "user", "repo_id", "state",
                                   "merged_at"])
    # README: AIDev-pop Copilot PRs must be authored by the `copilot` account;
    # Copilot, Devin and Jules PRs are authored by the agent's bot account
    out["pop_top_users_per_bot_agent"] = {
        a: pop.loc[pop["agent"] == a, "user"].value_counts().head(5).to_dict()
        for a in ("Copilot", "Devin", "Google_Jules")}
    out["pop_distinct_users_per_agent"] = pop.groupby("agent")["user"].nunique().to_dict()
    out["all_top_users_copilot"] = allpr.loc[allpr["agent"] == "Copilot", "user"].value_counts().head(5).to_dict()
    print("pop top users for bot agents:", out["pop_top_users_per_bot_agent"])
    print("pop distinct users per agent:", out["pop_distinct_users_per_agent"])
    print("full-set top users for Copilot:", out["all_top_users_copilot"])
    out["pr_repo_id_null"] = int(allpr["repo_id"].isna().sum())
    print("full-set PRs with null repo_id:", out["pr_repo_id_null"])
    repo = pd.read_parquet(LOCAL / "repository.parquet",
                           columns=["id", "stars", "language"])
    out["pop_prs"] = len(pop)
    out["pop_pr_ids_distinct"] = int(pop["id"].nunique())
    out["pop_repos_rows"] = len(repo)
    out["pop_repos_with_prs"] = int(pop["repo_id"].nunique())
    out["pop_pr_repo_ids_missing_from_repository"] = len(
        set(pop["repo_id"]) - set(repo["id"]))
    out["pop_repo_stars_min"] = int(repo["stars"].min())
    out["pop_repos_with_stars_le_100"] = int((repo["stars"] <= 100).sum())
    out["pop_prs_not_in_all_pull_request"] = int((~pop["id"].isin(allpr["id"])).sum())
    out["pop_by_agent"] = pop["agent"].value_counts().to_dict()
    out["pop_outcomes_pct_open_closed_merged"] = outcome_shares(pop)
    out["pop_language_top15"] = repo["language"].value_counts().head(15).to_dict()
    print()
    for k in ("pop_prs", "pop_pr_ids_distinct", "pop_repos_rows",
              "pop_repos_with_prs", "pop_pr_repo_ids_missing_from_repository",
              "pop_repo_stars_min", "pop_repos_with_stars_le_100",
              "pop_prs_not_in_all_pull_request"):
        print(f"{k:45s} {out[k]:>11,}")
    print("pop by agent:", out["pop_by_agent"])
    print("pop open/closed/merged %:", out["pop_outcomes_pct_open_closed_merged"])
    print("pop repo languages (top 15):", out["pop_language_top15"])

    (ROOT / "data" / "p1_counts.json").write_text(
        json.dumps(out, indent=1, default=int), encoding="utf-8")


if __name__ == "__main__":
    main()
