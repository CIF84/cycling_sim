# AI Engineering Specifications

## Purpose

This document captures reusable specification patterns for working with AI coding agents.

The goal is not to write vague prompts.

The goal is to write clear engineering specifications that preserve intent, reduce ambiguity, and make changes reviewable.

---

# Core Principles

## 1. Define the goal

State what should change and why.

## 2. Define the scope

Be explicit about what the agent may change.

## 3. Define non-goals

Be explicit about what must not change.

## 4. Preserve behavior unless requested

For refactors, the default expectation is zero behavior change.

## 5. Require verification

Every task should specify how success is checked.

## 6. Ask for explanation

The agent should explain:
- what changed
- what did not change
- why decisions were made
- how it verified the work

---

# Refactor Specification Template

```text
Refactor [PROJECT / MODULE] without changing behavior.

Goal:
[Describe the architectural improvement.]

Task:
[Describe exactly what should be moved, renamed, split, or reorganized.]

Target files:
- [file/module 1]
- [file/module 2]

Move only:
- [function / class / responsibility]
- [function / class / responsibility]

Requirements

---

# Architecture Specification

* Goal
* Purpose
* Ownership
* Scope
* Non-goals
* Verification