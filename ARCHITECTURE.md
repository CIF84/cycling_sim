# Bike Science Pro — Architecture

## Purpose

This document explains how Bike Science Pro is organized so humans and AI coding agents can evolve it safely.

The goal is not architecture for its own sake.

The goal is to make the project easier to understand, modify, test and extend.

---

# Product architecture

Bike Science Pro is a cycling decision engine.

It has four conceptual layers:

```text
Inputs
↓
Simulation engines
↓
Decision / insight engines
↓
User experience