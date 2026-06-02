def cleanData(statcast_df):
    """
    Cleans Statcast data and adds baseball metric columns.

    Keeps only regular season games.
    """

    df = statcast_df.copy()

    # Make sure required columns exist
    required_columns = ["events", "batter", "game_type"]

    for col in re quired_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Keep only regular season games
    df = df[df["game_type"] == "R"].copy()

    # Clean event values
    df["events_clean"] = (
        df["events"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # Events that count as real plate appearances
    # truncated_pa is intentionally excluded
    pa_events = {
        "single",
        "double",
        "triple",
        "home_run",
        "strikeout",
        "strikeout_double_play",
        "walk",
        "intent_walk",
        "intentional_walk",
        "hit_by_pitch",
        "field_out",
        "force_out",
        "grounded_into_double_play",
        "field_error",
        "fielders_choice",
        "fielders_choice_out",
        "sac_fly",
        "sac_bunt",
        "sac_fly_double_play",
        "sac_bunt_double_play",
        "catcher_interf",
        "catchers_interference"
    }

    # Events that are plate appearances but NOT official at-bats
    non_at_bat_events = {
        "walk",
        "intent_walk",
        "intentional_walk",
        "hit_by_pitch",
        "sac_fly",
        "sac_bunt",
        "sac_fly_double_play",
        "sac_bunt_double_play",
        "catcher_interf",
        "catchers_interference"
    }

    # Hit definitions
    hit_events = {
        "single",
        "double",
        "triple",
        "home_run"
    }

    total_bases_map = {
        "single": 1,
        "double": 2,
        "triple": 3,
        "home_run": 4
    }

    strikeout_events = {
        "strikeout",
        "strikeout_double_play"
    }

    # Metrics 
    df["is_plate_appearance"] = df["events_clean"].isin(pa_events).astype(int)

    df["is_at_bat"] = (
        df["events_clean"].isin(pa_events) &
        ~df["events_clean"].isin(non_at_bat_events)
    ).astype(int)

    df["is_hit"] = df["events_clean"].isin(hit_events).astype(int)

    df["is_home_run"] = (df["events_clean"] == "home_run").astype(int)

    df["total_bases"] = (
        df["events_clean"]
        .map(total_bases_map)
        .fillna(0)
        .astype(int)
    )

    df["is_walk"] = df["events_clean"].isin([
        "walk",
        "intent_walk",
        "intentional_walk"
    ]).astype(int)

    df["is_strikeout"] = df["events_clean"].isin(strikeout_events).astype(int)

    return df
