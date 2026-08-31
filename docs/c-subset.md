# C subset target

The C compiler is being built incrementally rather than aiming at full
C89/C99 up front. This file describes the "v1" subset (Phase 5) and what's
explicitly deferred.

## v1 subset (Phase 5 target)

**Types**
- `char` — 8-bit
- `int` — 16-bit
- Pointers to either (`char *`, `int *`)
- One-dimensional arrays of either (`char a[N]`, `int a[N]`)

**Declarations**
- Global variables (in RAM, statically allocated — no dynamic memory)
- Local variables inside functions (on the software parameter/data stack —
  see `docs/architecture.md`)
- Function definitions with typed parameters and a return type (including
  `void`)

**Operators**
- Arithmetic: `+ - * / %` (multiply/divide/mod need software routines —
  the 6502 has no hardware multiply or divide)
- Comparison: `== != < > <= >=`
- Logical: `&& || !`
- Assignment: `=` (compound assignment like `+=` deferred, see below)
- Address-of / dereference: `& *`
- Array indexing: `a[i]`

**Control flow**
- `if` / `else`
- `while`
- `for`
- `return`

**Not yet — deferred to later phases**
- `struct` / `union`
- `float` / `double`
- `switch`
- Multi-dimensional arrays
- Dynamic memory (`malloc`/`free`)
- Compound assignment operators (`+=`, `-=`, ...), `++`/`--`
- Most of the standard library — only whatever tiny runtime support the
  compiler itself needs (e.g. software multiply/divide, the console I/O
  device from `docs/architecture.md`) ships initially
- Preprocessor (`#include`, `#define`, macros) — Phase 5 programs are
  single translation units with no preprocessing

## Design notes

- No implicit type promotion rules beyond what's needed for `char`/`int`
  arithmetic to behave sanely — keep the type system as simple as possible
  while still being recognizably C.
- Error on anything outside the subset (unsupported syntax should be a
  clear compiler error, not silently mis-compiled code).

## Status

Not started — this is the Phase 5 target definition, written in Phase 0 so
the roadmap is concrete. Revise as we learn more from building Phases 1-4.
