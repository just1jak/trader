#!/usr/bin/env python3
"""
Fetch public YouTube captions and distill repeated trading concepts into a
traceable strategy research spec.

The fetch step uses yt-dlp when it is installed. The distill step is stdlib-only
and can run against existing .vtt/.txt/.json transcript files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


DEFAULT_OUT_DIR = Path("paper-trading/data/transcripts/riley_coleman")

RULE_DEFINITIONS = [
    {
        "id": "trade_from_key_zones",
        "type": "context",
        "description": "Only look for trades at pre-identified support, resistance, structure, liquidity, or supply/demand zones.",
        "mechanical_translation": "Build rolling support/resistance zones from prior swing highs/lows; ignore signals that occur away from those zones.",
        "keywords": [
            "support",
            "resistance",
            "level",
            "zone",
            "supply",
            "demand",
            "liquidity",
            "structure",
            "key area",
        ],
    },
    {
        "id": "wait_for_rejection_confirmation",
        "type": "entry",
        "description": "Wait for price rejection or confirmation before entering instead of buying/selling the first touch.",
        "mechanical_translation": "Require a rejection candle, wick rejection, engulfing candle, close back through the level, or volume confirmation after a zone test.",
        "keywords": [
            "rejection",
            "reject",
            "confirmation",
            "confirm",
            "wick",
            "engulf",
            "close above",
            "close below",
            "failed",
            "trap",
        ],
    },
    {
        "id": "break_and_retest",
        "type": "entry",
        "description": "Treat break-and-retest behavior as a separate setup from pure reversal entries.",
        "mechanical_translation": "After a level breaks with momentum, mark it as pending and enter only if price retests that level within a fixed bar window.",
        "keywords": [
            "break and retest",
            "retest",
            "breakout",
            "breakdown",
            "breaks through",
            "hold above",
            "hold below",
            "flip",
        ],
    },
    {
        "id": "use_market_structure_bias",
        "type": "filter",
        "description": "Use market structure, trend, channel, or directional bias to avoid fighting the dominant move.",
        "mechanical_translation": "Add a trend filter based on swing structure, EMA slope, higher highs/lows, or channel direction.",
        "keywords": [
            "trend",
            "market structure",
            "higher high",
            "higher low",
            "lower high",
            "lower low",
            "channel",
            "direction",
            "bias",
        ],
    },
    {
        "id": "session_timing_filter",
        "type": "filter",
        "description": "Prefer specific futures/scalping windows instead of trading every minute of the session.",
        "mechanical_translation": "Restrict entries to configured session windows and reject low-liquidity chop periods.",
        "keywords": [
            "open",
            "session",
            "morning",
            "afternoon",
            "lunch",
            "1 minute",
            "one minute",
            "timing",
            "window",
            "new york",
        ],
    },
    {
        "id": "fixed_risk_reward_management",
        "type": "risk",
        "description": "Define stop, target, and risk/reward before entry.",
        "mechanical_translation": "Attach bracket orders with ATR/structure stop, fixed R multiple target, max hold bars, and no-entry if reward is too small.",
        "keywords": [
            "risk reward",
            "risk-to-reward",
            "stop loss",
            "stop",
            "target",
            "take profit",
            "profit target",
            "manage",
            "position size",
            "bracket",
        ],
    },
    {
        "id": "avoid_bad_context",
        "type": "risk",
        "description": "Avoid trades during unclear, choppy, or news-driven conditions.",
        "mechanical_translation": "Add no-trade filters for low range/volume chop, major scheduled events, and setups without clean invalidation.",
        "keywords": [
            "avoid",
            "mistake",
            "chop",
            "choppy",
            "news",
            "do not trade",
            "don't trade",
            "low volume",
            "unclear",
            "bad trade",
        ],
    },
]


TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?)\s+-->\s+(?P<end>\d{1,2}:\d{2}:\d{2}(?:\.\d{3})?)"
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


@dataclass
class TranscriptSegment:
    start: float
    end: float | None
    text: str


@dataclass
class VideoTranscript:
    video_id: str
    title: str
    url: str
    source_file: str
    segments: list[TranscriptSegment]


def parse_timestamp(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def fmt_timestamp(seconds: float | None) -> str:
    if seconds is None or math.isnan(seconds):
        return "00:00:00"
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def clean_caption_text(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("[Music]", " ").replace("[Applause]", " ")
    return SPACE_RE.sub(" ", text).strip()


def parse_vtt(path: Path) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    current_start: float | None = None
    current_end: float | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, current_end, current_lines
        if current_start is None:
            current_lines = []
            return
        text = clean_caption_text(" ".join(current_lines))
        if text:
            segments.append(TranscriptSegment(current_start, current_end, text))
        current_start = None
        current_end = None
        current_lines = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            flush()
            continue
        match = TIMESTAMP_RE.search(line)
        if match:
            flush()
            current_start = parse_timestamp(match.group("start"))
            current_end = parse_timestamp(match.group("end"))
            continue
        if current_start is not None and not line.isdigit():
            current_lines.append(line)
    flush()
    return merge_repeated_segments(segments)


def merge_repeated_segments(segments: list[TranscriptSegment]) -> list[TranscriptSegment]:
    merged: list[TranscriptSegment] = []
    previous_text = ""
    for segment in segments:
        text = segment.text.strip()
        if not text or text == previous_text:
            continue
        if previous_text and text.startswith(previous_text):
            text = text[len(previous_text) :].strip()
        if not text:
            continue
        merged.append(TranscriptSegment(segment.start, segment.end, text))
        previous_text = segment.text.strip()
    return merged


def parse_json_transcript(path: Path) -> list[TranscriptSegment]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "segments" in payload:
        raw_segments = payload["segments"]
    elif isinstance(payload, list):
        raw_segments = payload
    else:
        raw_segments = []

    segments = []
    for item in raw_segments:
        text = clean_caption_text(str(item.get("text", "")))
        if not text:
            continue
        start = float(item.get("start", item.get("start_time", 0)) or 0)
        end = item.get("end", item.get("end_time"))
        segments.append(TranscriptSegment(start=start, end=float(end) if end is not None else None, text=text))
    return segments


def parse_txt_transcript(path: Path) -> list[TranscriptSegment]:
    text = clean_caption_text(path.read_text(encoding="utf-8", errors="replace"))
    parts = re.split(r"(?<=[.!?])\s+", text)
    segments = []
    for index, part in enumerate(parts):
        if part:
            segments.append(TranscriptSegment(start=float(index * 15), end=None, text=part))
    return segments


def discover_transcripts(transcripts_dir: Path) -> list[VideoTranscript]:
    all_transcript_files = sorted(
        [
            path
            for path in transcripts_dir.rglob("*")
            if path.suffix.lower() in {".vtt", ".txt", ".json"} and not path.name.endswith(".meta.json")
        ]
    )
    transcript_files = choose_preferred_transcripts(all_transcript_files)
    videos: list[VideoTranscript] = []
    for path in transcript_files:
        if path.suffix.lower() == ".vtt":
            segments = parse_vtt(path)
        elif path.suffix.lower() == ".json":
            try:
                segments = parse_json_transcript(path)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        else:
            segments = parse_txt_transcript(path)

        if not segments:
            continue

        meta = read_metadata_for(path)
        video_id = str(meta.get("id") or path.parent.name or path.stem)
        title = str(meta.get("title") or path.stem)
        url = str(meta.get("webpage_url") or meta.get("url") or "")
        videos.append(
            VideoTranscript(
                video_id=video_id,
                title=title,
                url=url,
                source_file=str(path),
                segments=segments,
            )
        )
    return videos


def choose_preferred_transcripts(paths: list[Path]) -> list[Path]:
    by_video: dict[Path, list[Path]] = defaultdict(list)
    for path in paths:
        if path.name in {"metadata.json"} or path.name.endswith(".info.json"):
            continue
        by_video[path.parent].append(path)

    preferred = []
    for _, candidates in sorted(by_video.items(), key=lambda item: str(item[0])):
        preferred.append(sorted(candidates, key=transcript_preference)[0])
    return preferred


def transcript_preference(path: Path) -> tuple[int, str]:
    name = path.name.lower()
    if ".en-orig." in name:
        rank = 0
    elif ".en." in name:
        rank = 1
    elif path.suffix.lower() == ".vtt":
        rank = 2
    elif path.suffix.lower() == ".json":
        rank = 3
    else:
        rank = 4
    return rank, name


def read_metadata_for(path: Path) -> dict:
    candidates = [
        path.with_suffix(".meta.json"),
        path.parent / "metadata.json",
        path.parent / f"{path.stem}.meta.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
    return {}


def iter_urls(urls_file: Path | None, urls: list[str]) -> Iterable[str]:
    seen = set()
    for url in urls:
        stripped = url.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            yield stripped
    if urls_file:
        for raw_line in urls_file.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped not in seen:
                seen.add(stripped)
                yield stripped


def find_yt_dlp() -> str | None:
    path_candidate = shutil.which("yt-dlp")
    if path_candidate:
        return path_candidate

    venv_candidate = Path(sys.executable).with_name("yt-dlp")
    if venv_candidate.exists():
        return str(venv_candidate)

    return None


def fetch_video(url: str, out_dir: Path) -> dict:
    yt_dlp = find_yt_dlp()
    if not yt_dlp:
        raise RuntimeError("yt-dlp is not installed or not on PATH.")

    out_dir.mkdir(parents=True, exist_ok=True)
    metadata_cmd = [
        yt_dlp,
        "--extractor-args",
        "youtube:player_client=android",
        "--skip-download",
        "--no-simulate",
        "--write-auto-subs",
        "--write-subs",
        "--sub-langs",
        "en-orig,en,en-US,en.*",
        "--sub-format",
        "vtt",
        "--write-info-json",
        "--print",
        "%()j",
        "--no-warnings",
        "--paths",
        str(out_dir),
        "-o",
        "%(id)s/%(id)s.%(ext)s",
        url,
    ]
    result = subprocess.run(metadata_cmd, capture_output=True, text=True, check=True)
    json_lines = [line for line in result.stdout.splitlines() if line.strip().startswith("{")]
    metadata = json.loads(json_lines[-1]) if json_lines else {}
    video_id = str(metadata.get("id") or "unknown")
    video_dir = out_dir / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    (video_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def flatten_playlist(url: str, limit: int | None = None) -> list[str]:
    yt_dlp = find_yt_dlp()
    if not yt_dlp:
        raise RuntimeError("yt-dlp is not installed or not on PATH.")

    cmd = [yt_dlp, "--flat-playlist", "--dump-single-json", "--no-warnings", url]
    payload = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    entries = payload.get("entries") or []
    urls = []
    for entry in entries:
        webpage_url = entry.get("url") or entry.get("webpage_url")
        if not webpage_url:
            continue
        if not str(webpage_url).startswith("http"):
            webpage_url = f"https://www.youtube.com/watch?v={webpage_url}"
        urls.append(str(webpage_url))
        if limit and len(urls) >= limit:
            break
    return urls


def fetch(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    urls = list(iter_urls(Path(args.urls_file) if args.urls_file else None, args.url or []))
    if args.channel_url:
        urls.extend(flatten_playlist(args.channel_url, limit=args.limit))
    if args.limit:
        urls = urls[: args.limit]
    if not urls:
        raise SystemExit("No video URLs supplied. Use --url, --urls-file, or --channel-url.")

    failures = []
    for index, url in enumerate(urls, start=1):
        print(f"[{index}/{len(urls)}] fetching {url}", file=sys.stderr)
        try:
            metadata = fetch_video(url, out_dir)
            print(f"  saved {metadata.get('id')} - {metadata.get('title')}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - CLI should keep going per-video.
            failures.append({"url": url, "error": str(exc)})
            print(f"  failed: {exc}", file=sys.stderr)

    if failures:
        failure_path = out_dir / "fetch_failures.json"
        failure_path.write_text(json.dumps(failures, indent=2), encoding="utf-8")
        print(f"Wrote fetch failures to {failure_path}", file=sys.stderr)


def normalized_text(segments: list[TranscriptSegment]) -> str:
    return clean_caption_text(" ".join(segment.text for segment in segments))


def extract_evidence(videos: list[VideoTranscript]) -> tuple[list[dict], dict[str, Counter]]:
    evidence = []
    coverage: dict[str, Counter] = {rule["id"]: Counter() for rule in RULE_DEFINITIONS}
    seen = set()
    for video in videos:
        for segment in rolling_segments(video.segments, window=3):
            text = clean_caption_text(" ".join(part.text for part in segment))
            lower = text.lower()
            for rule in RULE_DEFINITIONS:
                matches = [keyword for keyword in rule["keywords"] if keyword in lower]
                if not matches:
                    continue
                start = segment[0].start
                seen_key = (rule["id"], video.video_id, int(start), tuple(matches))
                if seen_key in seen:
                    continue
                seen.add(seen_key)
                snippet = text[:300]
                evidence.append(
                    {
                        "rule_id": rule["id"],
                        "rule_type": rule["type"],
                        "video_id": video.video_id,
                        "title": video.title,
                        "url": video.url,
                        "timestamp": fmt_timestamp(start),
                        "start_seconds": start,
                        "matched_keywords": matches,
                        "snippet": snippet,
                    }
                )
                coverage[rule["id"]][video.video_id] += 1
    return evidence, coverage


def rolling_segments(segments: list[TranscriptSegment], window: int) -> Iterable[list[TranscriptSegment]]:
    if len(segments) <= window:
        if segments:
            yield segments
        return
    for index in range(0, len(segments) - window + 1):
        yield segments[index : index + window]


def build_strategy_spec(videos: list[VideoTranscript], evidence: list[dict], coverage: dict[str, Counter]) -> dict:
    source_count = len(videos)
    evidence_by_rule = Counter(item["rule_id"] for item in evidence)
    candidate_rules = []
    for rule in RULE_DEFINITIONS:
        rule_coverage = coverage[rule["id"]]
        video_coverage = len(rule_coverage)
        evidence_count = evidence_by_rule[rule["id"]]
        confidence = 0.0
        if source_count:
            confidence = min(1.0, (video_coverage / source_count) * 0.7 + min(evidence_count, 20) / 20 * 0.3)
        candidate_rules.append(
            {
                "rule_id": rule["id"],
                "type": rule["type"],
                "description": rule["description"],
                "mechanical_translation": rule["mechanical_translation"],
                "evidence_count": evidence_count,
                "video_coverage": video_coverage,
                "confidence": round(confidence, 3),
            }
        )

    candidate_rules.sort(key=lambda item: (item["confidence"], item["evidence_count"]), reverse=True)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_count": source_count,
        "sources": [
            {
                "video_id": video.video_id,
                "title": video.title,
                "url": video.url,
                "source_file": video.source_file,
                "segments": len(video.segments),
            }
            for video in videos
        ],
        "candidate_rules": candidate_rules,
        "ambiguities": [
            "Discretionary chart drawing must be converted into fixed swing/zone definitions before backtesting.",
            "Any mention of profitability or win rate must be ignored unless reproduced after costs in our data.",
            "If transcripts emphasize order flow, Level 2/time-and-sales data is required; OHLCV proxies should be marked as lower confidence.",
        ],
    }


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_markdown_brief(path: Path, spec: dict, evidence: list[dict]) -> None:
    lines = [
        "# Transcript-Derived Strategy Brief",
        "",
        "This is a research artifact for private backtesting. It is not trading advice, a performance claim, or a transcript republication.",
        "",
        f"Generated at: `{spec['generated_at']}`",
        f"Videos with usable transcript segments: `{spec['source_count']}`",
        "",
        "## Candidate Rules",
        "",
    ]
    for rule in spec["candidate_rules"]:
        lines.extend(
            [
                f"### {rule['rule_id']}",
                "",
                f"- Type: `{rule['type']}`",
                f"- Confidence: `{rule['confidence']}`",
                f"- Evidence count: `{rule['evidence_count']}` across `{rule['video_coverage']}` videos",
                f"- Rule: {rule['description']}",
                f"- Mechanical translation: {rule['mechanical_translation']}",
                "",
            ]
        )

    lines.extend(["## Highest-Signal Evidence Pointers", ""])
    by_rule = defaultdict(list)
    for item in evidence:
        by_rule[item["rule_id"]].append(item)
    for rule in spec["candidate_rules"]:
        lines.append(f"### {rule['rule_id']}")
        for item in diverse_evidence(by_rule[rule["rule_id"]], limit=5):
            source = item["url"] or item["video_id"]
            lines.append(f"- `{item['timestamp']}` [{item['title']}]({source}) - keywords: {', '.join(item['matched_keywords'])}")
        lines.append("")

    lines.extend(["## Ambiguities To Resolve Before Coding", ""])
    for item in spec["ambiguities"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def diverse_evidence(items: list[dict], limit: int) -> list[dict]:
    selected = []
    seen_videos = set()
    for item in sorted(items, key=lambda row: (row["video_id"], row["start_seconds"])):
        if item["video_id"] in seen_videos:
            continue
        selected.append(item)
        seen_videos.add(item["video_id"])
        if len(selected) >= limit:
            return selected
    for item in items:
        if item in selected:
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def distill(args: argparse.Namespace) -> None:
    transcripts_dir = Path(args.transcripts_dir)
    out_dir = Path(args.out_dir)
    videos = discover_transcripts(transcripts_dir)
    if not videos:
        raise SystemExit(f"No transcript files found under {transcripts_dir}.")

    evidence, coverage = extract_evidence(videos)
    spec = build_strategy_spec(videos, evidence, coverage)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "strategy_spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    write_jsonl(out_dir / "evidence.jsonl", evidence)
    write_markdown_brief(out_dir / "strategy_brief.md", spec, evidence)

    print(f"Distilled {len(videos)} videos and {len(evidence)} evidence pointers into {out_dir}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch public captions with yt-dlp.")
    fetch_parser.add_argument("--url", action="append", help="Single video URL. Can be repeated.")
    fetch_parser.add_argument("--urls-file", help="Text file with one video URL per line.")
    fetch_parser.add_argument("--channel-url", help="Channel/playlist URL to flatten before fetching.")
    fetch_parser.add_argument("--limit", type=int, help="Maximum videos to fetch.")
    fetch_parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Transcript output directory.")
    fetch_parser.set_defaults(func=fetch)

    distill_parser = subparsers.add_parser("distill", help="Distill saved transcripts into a strategy spec.")
    distill_parser.add_argument("--transcripts-dir", default=str(DEFAULT_OUT_DIR), help="Directory containing transcript files.")
    distill_parser.add_argument(
        "--out-dir",
        default="paper-trading/data/strategy-research/riley_coleman",
        help="Directory for strategy_spec.json, evidence.jsonl, and strategy_brief.md.",
    )
    distill_parser.set_defaults(func=distill)

    all_parser = subparsers.add_parser("all", help="Fetch captions and then distill them.")
    all_parser.add_argument("--url", action="append", help="Single video URL. Can be repeated.")
    all_parser.add_argument("--urls-file", help="Text file with one video URL per line.")
    all_parser.add_argument("--channel-url", help="Channel/playlist URL to flatten before fetching.")
    all_parser.add_argument("--limit", type=int, help="Maximum videos to fetch.")
    all_parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Transcript output directory.")
    all_parser.add_argument(
        "--research-out-dir",
        default="paper-trading/data/strategy-research/riley_coleman",
        help="Directory for distilled research artifacts.",
    )

    def fetch_then_distill(args: argparse.Namespace) -> None:
        fetch(args)
        distill(
            argparse.Namespace(
                transcripts_dir=args.out_dir,
                out_dir=args.research_out_dir,
            )
        )

    all_parser.set_defaults(func=fetch_then_distill)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
