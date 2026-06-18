# ANTI-DRIFT CONTRACT (ADC) v1.0

## Purpose

This contract defines the immutable behavioral, architectural, and interface requirements for a module.

Any future modification must comply with this contract unless the owner explicitly authorizes a contract revision.

The objective is to prevent:

* Feature erosion
* Silent regressions
* Architectural drift
* Logic replacement
* Output format changes
* Hidden simplifications
* AI-generated rewrites that alter intended behavior

---

# MODULE IDENTIFICATION

Module Name:
<MODULE_NAME>

Module Version: <VERSION>

Owner: <OWNER>

Status:
LOCKED BASELINE

Date Locked: <DATE>

---

# CORE PURPOSE LOCK

The primary purpose of this module is:

<DESCRIBE PRIMARY PURPOSE>

Future modifications may enhance functionality but may not alter the primary purpose.

Any change that alters the primary purpose constitutes architectural drift.

---

# PUBLIC API LOCK

The following exported functions are considered public interfaces:

* function_a()
* function_b()
* function_c()

Rules:

1. Existing public functions may not be removed.
2. Existing public functions may not be renamed.
3. Existing function signatures may not change.
4. Existing return structures may not change.
5. Existing dictionary keys may not be removed.
6. Existing report fields may not be removed.

Allowed:

* Additional optional fields
* Additional optional parameters
* New helper functions

Forbidden:

* Breaking API changes
* Silent interface changes

---

# OUTPUT CONTRACT

Current outputs are considered authoritative.

The following outputs must remain compatible:

* Return dictionaries
* DataFrame structures
* Journal outputs
* Report outputs
* Export outputs

Rules:

1. Existing fields must remain present.
2. Existing field names must remain unchanged.
3. Existing report sections must remain unchanged.
4. Existing output ordering should be preserved.

Additive expansion is allowed.

Destructive modification is prohibited.

---

# LOGIC PRESERVATION CONTRACT

Existing analytical logic is considered intentional.

Future modifications must:

* Extend logic
* Refine logic
* Fix defects

Future modifications must not:

* Replace logic wholesale
* Simplify logic without approval
* Remove analytical pathways
* Reduce signal coverage
* Remove pattern recognition rules

When logic changes occur:

The previous logic must be documented.

The reason for modification must be documented.

---

# DATA CONTRACT

Input expectations are locked.

If data normalization exists:

* It must remain self-contained.
* Existing accepted input formats must continue to work.

Backward compatibility is mandatory.

---

# ERROR HANDLING CONTRACT

Silent failure is prohibited.

Requirements:

* Exceptions must be logged.
* Invalid states must be identifiable.
* Failures must be observable.

Temporary fallbacks are allowed.

Silent degradation is prohibited.

---

# PERFORMANCE CONTRACT

Optimizations are allowed only if:

1. Functional outputs remain identical.
2. Public interfaces remain identical.
3. Journal outputs remain identical.

Performance improvements must not alter behavior.

---

# JOURNAL CONTRACT

If journal generation exists:

Journal structure is locked.

Allowed:

* Additional sections
* Additional metrics

Forbidden:

* Removing sections
* Renaming sections
* Reordering sections without approval

---

# AI MODIFICATION RULES

Any AI modifying this module must:

1. Read the entire file.
2. Preserve all existing functionality.
3. Preserve all public APIs.
4. Preserve all outputs.
5. Preserve all journal structures.
6. Preserve all data contracts.
7. Document every change.

AI may not:

* Rewrite the module from scratch.
* Collapse logic into simplified versions.
* Remove code because it appears unused.
* Replace analytical systems with placeholders.
* Convert functionality into TODO items.

---

# REGRESSION PREVENTION

Before a modification is considered valid:

The following questions must all be answered YES:

* Does every public function still exist?
* Do all outputs still exist?
* Do all report sections still exist?
* Do all dictionary keys still exist?
* Does all existing analytical logic still execute?
* Are all previous use cases still supported?

If any answer is NO:

The modification is rejected.

---

# CHANGE APPROVAL REQUIREMENT

The following actions require explicit owner approval:

* Function removal
* API changes
* Output format changes
* Journal structure changes
* Logic replacement
* Architectural redesign
* Data model changes

Without approval:

These actions are prohibited.

---

# GOLDEN RULE

Enhancement is permitted.

Replacement is not.

Extension is permitted.

Reduction is not.

Additive evolution is permitted.

Destructive evolution is prohibited.
