# MLB LLM Agent

This project is an MLB analytics assistant that answers baseball questions in natural language using an LLM and Python tools.

The goal is to help users quickly find baseball information without manually searching through large datasets or writing pandas code. A possible use case is helping MLB announcers, analysts, and broadcasters quickly look up useful stats before or during a game.

Example questions the system can answer:

- Who had the most home runs in May?
- How did Judge do against sliders?
- Compare Judge and Ohtani.
- What was Yamamoto’s ERA?
- Who has the best batting average vs left-handed pitchers?

## Project Overview

The system uses the LLM as a tool router. The user asks a baseball question, the LLM selects the correct Python tool, and the tool calculates the answer using MLB data. The final answer is then returned in natural language.

The LLM does not rely on memory for baseball statistics. Instead, the answer is grounded in Statcast and Baseball Reference data.

## Data Sources

This project uses:

- Statcast 2025 season data
- `batting_stats_bref(2025)`
- `pitching_stats_bref(2025)`

Statcast data is used for pitch-level and play-level analysis, including date filtering, pitch-type analysis, and matchups.

Baseball Reference data is used for official full-season hitter and pitcher stats.

## Tools Built

The project includes Python tools for:

- Hitter leaderboards
- Pitcher leaderboards
- Single hitter stats
- Single pitcher stats
- Hitter comparisons
- Pitcher comparisons
- Hitter vs pitcher matchups
- Hitter performance vs pitcher handedness
- Hitter performance by pitch type

## Files

- `CS668MLBProject.ipynb` — main project notebook
- `CleanData.py` — data cleaning functions
- `tools.py` — baseball analysis tools
- `requirements.txt` — Python dependencies
- `MLB_Agent_Project_Report.pdf` — final project report

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
