<!-- write-readme session transcript

  Detected: CLI Tool (Java, pom.xml + mainClass + JLine)
  Academic project: yes (com.university groupId, instructions.md assessment brief)
  Solo project: yes (1 contributor, 0 stars)

  > Describe your project in 1-2 sentences.
  Console-based digital ID management for food service workers with role-based access across 7 organisation types.

  Options:
    License:       [Skip — academic project]
    Contributing:  [Skip — academic integrity]
    Verbosity:     [Standard]

-->

# Food Service Digital ID Management System

[![CI](https://github.com/ephemerallyCaden/IOT452U-DigitalID/actions/workflows/ci.yml/badge.svg)](https://github.com/ephemerallyCaden/IOT452U-DigitalID/actions/workflows/ci.yml)
![Java](https://img.shields.io/badge/Java-17-orange)
![Maven](https://img.shields.io/badge/Maven-3.8%2B-blue)

A console-based system for managing digital worker identities and food safety certifications across 7 organisation types, 26+ use cases, and 12 geographic regions. Built with a ports-and-adapters architecture.

Developed as part of the IOT452U Software Engineering module.

## Getting Started

Requires Java 17+ and Maven 3.8+.

```bash
git clone https://github.com/ephemerallyCaden/IOT452U-DigitalID.git
cd IOT452U-DigitalID
mvn clean compile exec:java -Dexec.mainClass="com.digitalid.Application"
```

Run tests:

```bash
mvn test

# With coverage report
mvn verify
# Report at target/site/jacoco/index.html
```

## Usage

On startup, select an organisation type from the interactive menu:

```
  Central Authority Service
  Financial Service
  Fast Food Service
  Fine Dining Service
  Delivery Service
  Coffee Shop Service
  Street Vendor Service

  arrow keys navigate · Enter select · Q quit
```

Each organisation has access to a different set of tools. The Central Authority has full identity and certification management. Other organisations have read-only verification appropriate to their role.

## Architecture

Layered with ports and adapters. Dependencies point inward.

| Layer | Responsibility |
|---|---|
| Presentation | Console menus, user input, result display |
| Application | Use cases, access control, port interfaces |
| Domain | Entities, business rules, validation |
| Infrastructure | JSON file persistence, configuration |

## Documentation

- [Design Documentation](documentation/doc-design.md) -- System context, organisation types, business rules
- [Technical Documentation](documentation/doc-technical.md) -- Architecture patterns, tool system, domain model
- [Architecture Diagram](documentation/architecture-diagram.html) -- Interactive layered architecture and access control matrix

## Tech Stack

| Component | Technology |
|---|---|
| Language | Java 17 |
| Build | Maven |
| Persistence | JSON files (Gson) |
| Terminal UI | JLine 3 |
| Testing | JUnit 5, Mockito |
| Coverage | JaCoCo |
| CI | GitHub Actions |
