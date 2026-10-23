<!-- write-readme session transcript

  Detected: Mobile App (Flutter, pubspec.yaml + android/ + ios/)
  Solo project: yes (1 contributor, 0 stars)

  > The app display name is "Ganba!" but the package name is
  > "projecting_not_sending". Which should the README use as the title?
  Ganba!

  > Describe your project in 1-2 sentences.
  Personal climbing training tracker with periodized phases, rehab tracking, and benchmarks.

  Options:
    License:       [Skip]
    Contributing:  [Skip — solo project]
    Verbosity:     [Standard]
    Screenshots:   [Add later — no device screenshots in repo]

-->

# Ganba!

![Flutter](https://img.shields.io/badge/Flutter-3.12+-02569B?logo=flutter&logoColor=white)
![Dart](https://img.shields.io/badge/Dart-3.12+-0175C2?logo=dart&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20iOS-green)
![Version](https://img.shields.io/badge/version-0.1.0--alpha.1-orange)

A personal climbing training tracker for periodized training, rehab, and benchmarks. Offline-first — all data stored locally in SQLite, no account or network required.

<!-- screenshot:hero | type=mobile | description=Phone mockups showing dashboard, session logging, and stats screens | priority=MUST | format=png -->

## Features

- **Training Phases** -- Periodized blocks with auto-advancing phases and deload weeks
- **Session Logging** -- Log climbs with grade, outcome, style, and media attachments
- **Drill Timer** -- Foreground-service timer with work/rest intervals and sound cues
- **Progress Stats** -- Charts for grades, sessions, volume, and personal records
- **Pain Monitoring** -- Track injury areas with severity ratings and alert thresholds
- **Goal Setting** -- Goals tied to specific exercises with automatic progress tracking
- **Benchmarking** -- Record and retest performance benchmarks on a schedule
- **Training Plan** -- Visual canvas for scheduling sessions into weekly templates
- **Year in Review** -- Five-slide carousel summarizing your training year
- **Achievements** -- Unlockable achievements on a collectible wall

## Getting Started

Requires [Flutter SDK](https://docs.flutter.dev/get-started/install) 3.12+, Android Studio or Xcode, and a device or emulator.

```bash
git clone https://github.com/ephemerallyCaden/Ganba.git
cd Ganba
flutter pub get
flutter run
```

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
