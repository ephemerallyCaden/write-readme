<!-- write-readme session transcript

  Detected: Mobile App (Flutter, pubspec.yaml + android/ + ios/)
  Solo project: yes (1 contributor, 0 stars)
  Existing screenshots: yes — ganba-screens/ contains 30 golden test renders

  > The app display name is "Ganba!" but the package name is
  > "projecting_not_sending". Which should the README use as the title?
  Ganba!

  > Describe your project in 1-2 sentences.
  Personal climbing training tracker with periodized phases, rehab tracking, and benchmarks.

  Options:
    License:       [Skip]
    Contributing:  [Skip — solo project]
    Verbosity:     [Standard]
    Screenshots:   [Use existing — ganba-screens/ has rendered screens]

-->

# Ganba!

![Flutter](https://img.shields.io/badge/Flutter-3.12+-02569B?logo=flutter&logoColor=white)
![Dart](https://img.shields.io/badge/Dart-3.12+-0175C2?logo=dart&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20iOS-green)
![Version](https://img.shields.io/badge/version-0.1.0--alpha.1-orange)

A personal climbing training tracker for periodized training, rehab, and benchmarks. Offline-first — all data stored locally in SQLite, no account or network required.

<p align="center">
  <img src="ganba-screens/dashboard_bento_dark.png" alt="Ganba dashboard showing streak, weekly schedule, pain areas, and benchmark retests" width="220">
  &nbsp;&nbsp;
  <img src="ganba-screens/session_poster_dark.png" alt="Session summary with climb recap chart, trophy climbs, and style breakdown" width="220">
  &nbsp;&nbsp;
  <img src="ganba-screens/goals_screen_dark.png" alt="Goals screen tracking weighted pull progress and hangboard benchmarks" width="220">
</p>

## Getting Started

Requires [Flutter SDK](https://docs.flutter.dev/get-started/install) 3.12+, Android Studio or Xcode, and a device or emulator.

```bash
git clone https://github.com/ephemerallyCaden/Ganba.git
cd Ganba
flutter pub get
flutter run
```

## Features

- **Training Phases** -- Periodized blocks with auto-advancing phases and deload weeks
- **Session Logging** -- Log climbs with grade, outcome, style, and media attachments
- **Session Summary** -- Post-session breakdown with climb recap charts, trophy climbs, and style distribution
- **Drill Timer** -- Foreground-service timer with work/rest intervals and sound cues
- **Progress Stats** -- Charts for grades, sessions, volume, and personal records
- **Pain Monitoring** -- Track injury areas with severity ratings and alert thresholds
- **Goal Setting** -- Goals tied to specific exercises with automatic progress tracking
- **Benchmarking** -- Record and retest performance benchmarks on a schedule
- **Training Plan** -- Visual canvas for scheduling sessions into weekly templates
- **Year in Review** -- Five-slide carousel summarizing your training year
- **Achievements** -- Unlockable achievements on a collectible wall

<details>
<summary>More screenshots</summary>

<p align="center">
  <img src="ganba-screens/plan_canvas_light.png" alt="Training plan canvas showing weekly schedule with session types" width="220">
  &nbsp;&nbsp;
  <img src="ganba-screens/stats_k_dark.png" alt="Progress stats screen with grade charts, session history, and personal records" width="220">
  &nbsp;&nbsp;
  <img src="ganba-screens/streak_sheet_dark.png" alt="Streak tracking sheet" width="220">
</p>

<p align="center">
  <img src="ganba-screens/calendar_mock_dark.png" alt="Calendar view showing session history" width="220">
  &nbsp;&nbsp;
  <img src="ganba-screens/settings_screen_dark.png" alt="Settings screen" width="220">
  &nbsp;&nbsp;
  <img src="ganba-screens/blocks_list_dark.png" alt="Training blocks list view" width="220">
</p>

</details>

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Flutter (Dart 3.12+) |
| State | Riverpod |
| Database | sqflite (SQLite) |
| Charts | fl_chart |
| Notifications | flutter_local_notifications |
| Media | image_picker, video_player |

## Status

Early alpha (`0.1.0-alpha.1`). Under active development. Not yet on app stores.

## License

All rights reserved.
