import pandas as pd

def getHitterID(hitters, player_name):
    """
    Finds a hitter's MLB ID using their name.

    Inputs:
        hitters: dataframe from batting_stats_bref
        player_name: name typed by the user, like "Ohtani" or "Aaron Judge"

    Output:
        MLB player ID if found, otherwise None
    """

    matches = hitters[
        hitters["Name"].str.lower().str.contains(player_name.lower(), na=False)
    ]

    if matches.empty:
        return None
        
    return int(matches.iloc[0]["mlbID"])
    
#--------------------------------------------------------------------------------

def cleanPlayerName(name):
    """
    Fix player names with broken encoding like:
    Acu\\xc3\\xb1a -> Acuña
    Jos\\xc3\\xa9 -> José
    """

    if not isinstance(name, str):
        return name

    try:
        return name.encode("utf-8").decode("unicode_escape").encode("latin1").decode("utf-8")
    except:
        return name
        
#--------------------------------------------------------------------------------

def getHitterName(hitters, batter_id):
    """
    Finds a hitter's name using their MLB ID.

    Inputs:
        hitters: dataframe from batting_stats_bref
        batter_id: MLB player ID from Statcast

    Output:
        Player name if found, otherwise "Unknown Player"
    """

    matches = hitters[hitters["mlbID"] == batter_id]

    if matches.empty:
        return "Unknown Player"

    return matches.iloc[0]["Name"]

#--------------------------------------------------------------------------------

def filterByDate(df, start_date=None, end_date=None):
    """
    Filters Statcast data by game_date.

    Inputs:
        df: cleaned Statcast dataframe
        start_date: optional start date, format "YYYY-MM-DD"
        end_date: optional end date, format "YYYY-MM-DD"

    Output:
        filtered dataframe
    """

    temp = df.copy()

    temp["game_date"] = pd.to_datetime(temp["game_date"])

    if start_date is not None:
        temp = temp[temp["game_date"] >= pd.to_datetime(start_date)]

    if end_date is not None:
        temp = temp[temp["game_date"] <= pd.to_datetime(end_date)]

    return temp

#--------------------------------------------------------------------------------

def calculateHitterStats(df, hitters, start_date=None, end_date=None):
    """
    Creates one row per hitter with basic hitting stats.
    Uses Statcast data for calculations and hitters dataframe for names.
    """

    temp = filterByDate(df, start_date, end_date)

    hitter_stats = (
        temp.groupby("batter")
        .agg(
            PA=("is_plate_appearance", "sum"),
            AB=("is_at_bat", "sum"),
            H=("is_hit", "sum"),
            HR=("is_home_run", "sum"),
            TB=("total_bases", "sum"),
            BB=("is_walk", "sum"),
            SO=("is_strikeout", "sum")
        )
        .reset_index()
    )

    hitter_stats["BA"] = hitter_stats["H"] / hitter_stats["AB"]
    hitter_stats["SLG"] = hitter_stats["TB"] / hitter_stats["AB"]
    hitter_stats["K_rate"] = hitter_stats["SO"] / hitter_stats["PA"]
    hitter_stats["BB_rate"] = hitter_stats["BB"] / hitter_stats["PA"]

    hitter_stats["Name"] = hitter_stats["batter"].apply(
        lambda batter_id: getHitterName(hitters, batter_id)
    )

    hitter_stats = hitter_stats[hitter_stats["Name"] != "Unknown Player"]

    return hitter_stats

#--------------------------------------------------------------------------------

def calculatePitcherStats(df, pitchers=None, start_date=None, end_date=None):
    """
    Creates one row per pitcher with basic pitching stats.
    Uses cleaned Statcast data.
    """

    temp = filterByDate(df, start_date, end_date)

    pitcher_names = (
        temp.dropna(subset=["player_name"])
        .groupby("pitcher")["player_name"]
        .first()
        .reset_index()
        .rename(columns={"player_name": "Name"})
    )

    pitcher_stats = (
        temp.groupby("pitcher")
        .agg(
            BF=("is_plate_appearance", "sum"),
            AB=("is_at_bat", "sum"),
            H_allowed=("is_hit", "sum"),
            HR_allowed=("is_home_run", "sum"),
            BB_allowed=("is_walk", "sum"),
            SO=("is_strikeout", "sum")
        )
        .reset_index()
    )

    pitcher_stats = pitcher_stats.merge(
        pitcher_names,
        on="pitcher",
        how="left"
    )

    pitcher_stats["Name"] = pitcher_stats["Name"].fillna("Unknown Pitcher")

    pitcher_stats["BA_allowed"] = pitcher_stats["H_allowed"] / pitcher_stats["AB"]
    pitcher_stats["K_rate"] = pitcher_stats["SO"] / pitcher_stats["BF"]
    pitcher_stats["BB_rate"] = pitcher_stats["BB_allowed"] / pitcher_stats["BF"]
    pitcher_stats["HR_rate"] = pitcher_stats["HR_allowed"] / pitcher_stats["BF"]

    if pitchers is not None and start_date is None and end_date is None:
        official_pitching = pitchers[
            ["mlbID", "ERA", "IP", "WHIP", "SO9", "W", "L"]
        ].copy()

        official_pitching = official_pitching.rename(columns={
            "mlbID": "pitcher",
            "ERA": "ERA_official",
            "IP": "IP_official",
            "WHIP": "WHIP_official",
            "SO9": "SO9_official",
            "W": "W_official",
            "L": "L_official"
        })

        pitcher_stats["pitcher"] = pd.to_numeric(
            pitcher_stats["pitcher"], errors="coerce"
        ).astype("int64")

        official_pitching["pitcher"] = pd.to_numeric(
            official_pitching["pitcher"], errors="coerce"
        )

        official_pitching = official_pitching.dropna(subset=["pitcher"])
        official_pitching["pitcher"] = official_pitching["pitcher"].astype("int64")

        pitcher_stats = pitcher_stats.merge(
            official_pitching,
            on="pitcher",
            how="left"
        )

    return pitcher_stats

#--------------------------------------------------------------------------------

def getHitterLeaderboard(df, hitters, metric="HR", min_ab=100, start_date=None, end_date=None, top_n=10, ascending=False):
    """
    Returns a hitter leaderboard for a selected metric.

    Example metrics:
    HR, BA, SLG, H, BB, SO, K_rate, BB_rate
    """

    hitter_stats = calculateHitterStats(
        df,
        hitters,
        start_date=start_date,
        end_date=end_date
    )

    allowed_metrics = ["PA", "AB", "H", "HR", "TB", "BB", "SO", "BA", "SLG", "K_rate", "BB_rate"]

    if metric not in allowed_metrics:
        raise ValueError(f"Metric must be one of: {allowed_metrics}")

    hitter_stats = hitter_stats[hitter_stats["AB"] >= min_ab]

    result = hitter_stats.sort_values(metric, ascending=False).head(top_n)

    return result[["Name", "PA", "AB", "H", "HR", "TB", "BB", "SO", "BA", "SLG", "K_rate", "BB_rate"]]


#--------------------------------------------------------------------------------

def getPitcherLeaderboard(df, pitchers, metric="SO", min_bf=100, start_date=None, end_date=None, top_n=10, ascending=False):
    """
    Returns a pitcher leaderboard for a selected metric.

    Example metrics:
    SO, ERA_official, WHIP_official, BA_allowed, K_rate, BB_rate, HR_rate
    """

    pitcher_stats = calculatePitcherStats(
        df,
        pitchers,
        start_date=start_date,
        end_date=end_date
    )

    allowed_metrics = [
        "BF", "AB", "H_allowed", "HR_allowed", "BB_allowed", "SO",
        "BA_allowed", "K_rate", "BB_rate", "HR_rate"
    ]

    if start_date is None and end_date is None:
        allowed_metrics += [
            "ERA_official",
            "IP_official",
            "WHIP_official",
            "SO9_official",
            "W_official",
            "L_official"
        ]

    if metric not in allowed_metrics:
        raise ValueError(f"Metric must be one of: {allowed_metrics}")

    pitcher_stats = pitcher_stats[pitcher_stats["BF"] >= min_bf]

    result = pitcher_stats.sort_values(
        metric,
        ascending=ascending
    )

    if top_n is not None:
        result = result.head(top_n)

    return result

#--------------------------------------------------------------------------------

def compareHitters(df, hitters, player1, player2, start_date=None, end_date=None):
    """
    Compares two hitters using Statcast-calculated stats.

    Inputs:
        df: cleaned Statcast dataframe
        hitters: batting_stats_bref dataframe
        player1: first player name, example "Judge"
        player2: second player name, example "Ohtani"
        start_date: optional start date
        end_date: optional end date

    Output:
        dataframe with stats for both hitters
    """

    player1_id = getHitterID(hitters, player1)
    player2_id = getHitterID(hitters, player2)

    if player1_id is None:
        return f"Could not find hitter: {player1}"

    if player2_id is None:
        return f"Could not find hitter: {player2}"

    hitter_stats = calculateHitterStats(
        df,
        hitters,
        start_date=start_date,
        end_date=end_date
    )

    result = hitter_stats[
        hitter_stats["batter"].isin([player1_id, player2_id])
    ].copy()

    return result[
        ["Name", "PA", "AB", "H", "HR", "TB", "BB", "SO", "BA", "SLG", "K_rate", "BB_rate"]
    ]
    
#--------------------------------------------------------------------------------

import unicodedata

def normalizeName(name):
    """
    Makes name matching easier.

    Example:
        Rodón -> rodon
        José -> jose
    """

    if not isinstance(name, str):
        return ""
        
    name = unicodedata.normalize("NFKD", name)
    name = "".join(char for char in name if not unicodedata.combining(char))

    return name.lower()

#--------------------------------------------------------------------------------

def comparePitchers(df, pitchers, player1, player2, start_date=None, end_date=None):
    """
    Compares two pitchers using calculated pitcher stats.
    Uses normalized name matching instead of a separate pitcher ID helper.
    """

    pitcher_stats = calculatePitcherStats(
        df,
        pitchers,
        start_date=start_date,
        end_date=end_date
    )

    if pitcher_stats.empty:
        return "No data found for that date range."

    player1_norm = normalizeName(player1)
    player2_norm = normalizeName(player2)

    result = pitcher_stats[
        pitcher_stats["Name"].apply(normalizeName).str.contains(player1_norm, na=False) |
        pitcher_stats["Name"].apply(normalizeName).str.contains(player2_norm, na=False)
    ].copy()

    if result.empty:
        return "No matching pitchers found."

    columns = [
        "Name",
        "BF",
        "AB",
        "H_allowed",
        "HR_allowed",
        "BB_allowed",
        "SO",
        "BA_allowed",
        "K_rate",
        "BB_rate",
        "HR_rate"
    ]

    official_columns = [
        "ERA_official",
        "IP_official",
        "WHIP_official",
        "SO9_official",
        "W_official",
        "L_official"
    ]

    for col in official_columns:
        if col in result.columns:
            columns.append(col)

    return result[columns]

#--------------------------------------------------------------------------------

def getHitterLeaderboardVsPitcherHand(df,hitters,pitcher_hand="L",metric="BA",min_ab=50,top_n=10,ascending=False,start_date=None,end_date=None:
    """
    Returns a hitter leaderboard against left-handed or right-handed pitchers.

    Inputs:
        df: cleaned Statcast dataframe
        hitters: batting_stats_bref dataframe
        pitcher_hand: "L" or "R"
        metric: stat to rank by
        min_ab: minimum at-bats
        top_n: number of rows to return
        ascending: False = highest first, True = lowest first
        start_date: optional
        end_date: optional
    """

    temp = filterByDate(df, start_date, end_date)

    if pitcher_hand not in ["L", "R"]:
        raise ValueError("pitcher_hand must be 'L' or 'R'")

    temp = temp[temp["p_throws"] == pitcher_hand].copy()

    hitter_stats = calculateHitterStats(temp, hitters)

    allowed_metrics = [
        "PA", "AB", "H", "HR", "TB", "BB", "SO",
        "BA", "SLG", "K_rate", "BB_rate"
    ]

    if metric not in allowed_metrics:
        raise ValueError(f"Metric must be one of: {allowed_metrics}")

    hitter_stats = hitter_stats[hitter_stats["AB"] >= min_ab]

    result = hitter_stats.sort_values(metric, ascending=ascending)

    if top_n is not None:
        result = result.head(top_n)

    return result[
        ["Name", "PA", "AB", "H", "HR", "TB", "BB", "SO", "BA", "SLG", "K_rate", "BB_rate"]
    ]
    
#--------------------------------------------------------------------------------

def hitterVsPitcher(df, hitters, hitter_name, pitcher_name):
    """
    Shows how one hitter performed against one pitcher.
    Example: Judge vs Yamamoto
    """

    hitter_id = getHitterID(hitters, hitter_name)

    if hitter_id is None:
        return f"Could not find hitter: {hitter_name}"

    temp = df[
        (df["batter"] == hitter_id) &
        (df["player_name"].apply(normalizeName).str.contains(normalizeName(pitcher_name), na=False))
    ].copy()

    if temp.empty:
        return "No matchup data found."

    PA = temp["is_plate_appearance"].sum()
    AB = temp["is_at_bat"].sum()
    H = temp["is_hit"].sum()
    HR = temp["is_home_run"].sum()
    TB = temp["total_bases"].sum()
    BB = temp["is_walk"].sum()
    SO = temp["is_strikeout"].sum()

    BA = float(H / AB) if AB > 0 else 0.0
    SLG = float(TB / AB) if AB > 0 else 0.0

    return {
        "Hitter": getHitterName(hitters, hitter_id),
        "Pitcher": temp["player_name"].iloc[0],
        "PA": int(PA),
        "AB": int(AB),
        "H": int(H),
        "HR": int(HR),
        "BB": int(BB),
        "SO": int(SO),
        "BA": BA,
        "SLG": SLG
    }

#--------------------------------------------------------------------------------

def getHitterStatsVsPitchType(df, hitters, pitch_name, hitter_name=None, metric="BA", min_ab=20, top_n=None, descending=False):
    """
    Returns hitter stats vs a specific pitch type.

    If hitter_name is given, returns one hitter.
    If hitter_name is None, returns all hitters ranked by metric.
    """

    temp = df[
        df["pitch_name"]
        .fillna("")
        .str.lower()
        .str.contains(pitch_name.lower())
    ].copy()

    if temp.empty:
        return f"No data found for pitch type: {pitch_name}"

    if hitter_name is not None:
        hitter_id = getHitterID(hitters, hitter_name)

        if hitter_id is None:
            return f"Could not find hitter: {hitter_name}"

        temp = temp[temp["batter"] == hitter_id].copy()

        if temp.empty:
            return f"No data found for {hitter_name} vs {pitch_name}"

    stats = calculateHitterStats(temp, hitters)

    allowed_metrics = [
        "PA", "AB", "H", "HR", "TB", "BB", "SO",
        "BA", "SLG", "K_rate", "BB_rate"
    ]

    if metric not in allowed_metrics:
        if hitter_name is not None:
            metric = "BA"
        else:
            raise ValueError(f"Metric must be one of: {allowed_metrics}")

        
    if hitter_name is None:
        stats = stats[stats["AB"] >= min_ab]

        stats = stats.sort_values(
            metric,
            ascending=not descending
        )

        if top_n is not None:
            stats = stats.head(top_n)

    return stats[
        ["Name", "PA", "AB", "H", "HR", "TB", "BB", "SO", "BA", "SLG", "K_rate", "BB_rate"]
    ]

#--------------------------------------------------------------------------------

def getSingleHitterStats(df, hitters, hitter_name, start_date=None, end_date=None):
    """
    Gets one hitter's stats.

    If start_date or end_date is provided, uses cleaned Statcast data.
    If no date is provided, still uses cleaned Statcast data for consistency.
    """

    hitter_id = getHitterID(hitters, hitter_name)

    if hitter_id is None:
        return f"Could not find hitter: {hitter_name}"

    temp = filterByDate(df, start_date, end_date)

    temp = temp[temp["batter"] == hitter_id].copy()

    if temp.empty:
        return f"No data found for {hitter_name}."

    PA = temp["is_plate_appearance"].sum()
    AB = temp["is_at_bat"].sum()
    H = temp["is_hit"].sum()

    singles = (temp["events_clean"] == "single").sum()
    doubles = (temp["events_clean"] == "double").sum()
    triples = (temp["events_clean"] == "triple").sum()

    HR = temp["is_home_run"].sum()
    BB = temp["is_walk"].sum()
    SO = temp["is_strikeout"].sum()
    TB = temp["total_bases"].sum()

    BA = float(H / AB) if AB > 0 else 0.0
    SLG = float(TB / AB) if AB > 0 else 0.0
    K_rate = float(SO / PA) if PA > 0 else 0.0
    BB_rate = float(BB / PA) if PA > 0 else 0.0

    return {
        "Name": getHitterName(hitters, hitter_id),
        "Start Date": start_date,
        "End Date": end_date,
        "PA": int(PA),
        "AB": int(AB),
        "H": int(H),
        "Singles": int(singles),
        "Doubles": int(doubles),
        "Triples": int(triples),
        "HR": int(HR),
        "BB": int(BB),
        "SO": int(SO),
        "TB": int(TB),
        "BA": BA,
        "SLG": SLG,
        "K_rate": K_rate,
        "BB_rate": BB_rate
    }

#--------------------------------------------------------------------------------

def getSinglePitcherStats(df, pitchers, pitcher_name, start_date=None, end_date=None):
    """
    Gets one pitcher's stats.

    Full-season calls include official ERA/IP/WHIP/SO9 when available.
    Date-filtered calls use Statcast-calculated stats only.
    """

    pitcher_stats = calculatePitcherStats(
        df,
        pitchers,
        start_date=start_date,
        end_date=end_date
    )

    if pitcher_stats.empty:
        return f"No data found for {pitcher_name}."

    matches = pitcher_stats[
        pitcher_stats["Name"]
        .apply(normalizeName)
        .str.contains(normalizeName(pitcher_name), na=False)
    ].copy()

    if matches.empty:
        return f"Could not find pitcher: {pitcher_name}"

    player = matches.iloc[0]

    result = {
        "Name": player["Name"],
        "Start Date": start_date,
        "End Date": end_date,
        "BF": int(player["BF"]),
        "AB": int(player["AB"]),
        "H_allowed": int(player["H_allowed"]),
        "HR_allowed": int(player["HR_allowed"]),
        "BB_allowed": int(player["BB_allowed"]),
        "SO": int(player["SO"]),
        "BA_allowed": float(player["BA_allowed"]),
        "K_rate": float(player["K_rate"]),
        "BB_rate": float(player["BB_rate"]),
        "HR_rate": float(player["HR_rate"])
    }

    # Add official full-season stats only if they exist
    official_cols = [
        "ERA_official",
        "IP_official",
        "WHIP_official",
        "SO9_official",
        "W_official",
        "L_official"
    ]

    for col in official_cols:
        if col in player.index:
            result[col] = float(player[col])

    return result