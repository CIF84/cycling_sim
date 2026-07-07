# Bike Science Pro — Design Principles

> Good software is not software with the most features.
> Good software helps users make better decisions with the least possible effort.

These principles guide every product and UX decision in Bike Science Pro.

---

# 1. Reveal complexity progressively

Bike Science Pro is a sophisticated simulation engine.

It should never *feel* like one.

Users should discover capabilities naturally as they progress through the workflow. The interface should expose only the complexity needed for the current step.

Good:

Route → Rider → Bike → Compare → Insights

Bad:

A screen containing dozens of inputs with no context.

---

# 2. Derive the obvious

Never ask users for information that can be inferred confidently.

If two scenarios differ only in rider attributes, the application already knows this is a rider comparison.

If the route changes while the rider stays the same, the application already knows this is a route comparison.

Intelligence should reduce user effort, not increase it.

---

# 3. Explain before asking

Every input should have an obvious purpose.

Before asking users to provide information, make it clear why the information matters and what questions it will help answer.

Users should understand the value before investing effort.

---

# 4. Every section answers one question

Each section of the interface exists for one purpose.

Route Intelligence

"What kind of ride is this?"

Ride Briefing

"What should I expect?"

Performance Analysis

"What matters most?"

Decision Engine

"What should I do?"

Sections should never overlap unnecessarily.

---

# 5. Insights over data

Raw numbers are not the product.

Insights are.

Instead of merely displaying:

Aerodynamics: +2.4 min

Explain:

Aerodynamic improvements are expected to save roughly four times more time than reducing bike weight on this route.

Numbers support conclusions.

Conclusions support decisions.

---

# 6. Compare, don't calculate

The simulation engine performs calculations.

Bike Science Pro exists to compare scenarios.

Everything should reinforce comparison:

- split-screen layout
- scenario deltas
- cause attribution
- recommendations

Comparison is the product.

---

# 7. Recommendations require context

Advice without context is poor advice.

The same recommendation may be excellent for one comparison and irrelevant for another.

Recommendations must always reflect:

- the rider
- the route
- the equipment
- the comparison objective

Context comes first.

Recommendations follow.

---

# 8. Intelligence adapts to intent

Users should rarely choose analysis modes manually.

The application should infer intent whenever possible.

Examples:

Same rider + same route + changed equipment

→ Equipment optimization

Different riders + same route

→ Rider comparison

Same rider + different routes

→ Route suitability

If ambiguity exists, ask.

Otherwise, infer.

---

# 9. Help users answer questions, not fill forms

People do not open Bike Science Pro because they enjoy entering rider weight, CdA or tire pressure.

They open it because they have a question.

Examples:

"Would losing 5 kg matter?"

"Should I buy faster tires?"

"Which route should I ride?"

"Who is likely to be faster?"

The interface should always feel like it is helping answer those questions.

---

# 10. Build trust through transparency

Every important conclusion should be explainable.

Users should understand:

- what assumptions were made
- why a recommendation was generated
- which variables had the greatest influence
- where uncertainty exists

A trustworthy decision engine explains its reasoning.

# 11. Assign ownership before implementation

Every meaningful responsibility should have a clear owner (module, component, or engine). 

Once ownership is established, implementation becomes much easier to reason about, test, and evolve. 

Architecture should answer “who owns this?” before answering “how is it implemented?”

---

---

## Product philosophy

Bike Science Pro is not a cycling calculator.

It is not a ride planner.

It is not a bike fitting tool.

Bike Science Pro is a cycling decision engine.

Its purpose is simple:

Model scenarios.
Compare outcomes.
Make better decisions.