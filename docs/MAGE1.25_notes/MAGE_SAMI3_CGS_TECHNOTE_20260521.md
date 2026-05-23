# CGS MAGE-SAMI3 Technical Notes, 2026-05-21

Source:

- `https://cgs.jhuapl.edu/MAGE/sami3.php`

## Official CGS Points

The CGS MAGE SAMI3 page frames SAMI3 as a global 3-D physics-based model of the ionosphere/plasmasphere system. It evolves seven ion species:

- `H+`
- `He+`
- `N+`
- `O+`
- `N2+`
- `NO+`
- `O2+`

It solves temperature equations for:

- `H+`
- `He+`
- `O+`
- electrons

It includes ion inertia along geomagnetic field lines, which is important for topside ionosphere and plasmasphere regimes.

## Intended MAGE Role

The CGS page states that SAMI3 has two intended roles in MAGE:

- A plasmasphere component within `GAMERA`.
- An ionosphere component for `WACCM-X`.

For the WACCM-X side, WACCM-X is expected to provide SAMI3 with:

- neutral composition
- neutral temperature
- neutral winds

This matches the current local `WACCM-X -> SAMI3` minimum implementation direction, but the official wording confirms that winds are part of the intended interface, not an optional diagnostic.

## Electrodynamic Coupling Point

The CGS page says SAMI3 determines the low- to mid-latitude electrostatic potential from a neutral-wind dynamo potential equation. In MAGE, SAMI3 is expected to receive the high-latitude potential from `REMIX`.

This is important for our local roadmap:

- `WACCM-X -> SAMI3` should continue to provide neutral composition, temperature, and winds.
- `REMIX -> SAMI3` should be added for high-latitude potential or equivalent electric-field forcing.
- The current local version does not yet provide REMIX `POT` or `E-field` to SAMI3.

## Local Gap Relative To Official Intent

Current local `WACCM-X -> SAMI3` status:

- Implemented: `T`, `U`, `V`, `H`, `N`, `O`, `N2`, `NO`, `O2`.
- Stored but not used by SAMI3 neutral override: `OMEGA`, `UI`, `VI`, `WI`.
- Not implemented: `He` neutral override.
- Not implemented: geometric vertical neutral wind.
- Not implemented: time-dependent multi-snapshot forcing.
- Not implemented: `REMIX -> SAMI3` high-latitude potential or E-field input.
- Not implemented: `SAMI3 -> GAMERA/REMIX` plasma feedback.

## Recommended Interface Priority

The official CGS page supports this next-step order:

1. Add `REMIX POT` or equivalent mapped `E-field` into SAMI3 as high-latitude electrodynamic forcing.
2. Extend WACCM-X neutral forcing from one snapshot to time-dependent forcing.
3. Add missing neutral fields where physically defensible, especially `He` and a correct geometric vertical neutral wind if available.
4. Only then consider `SAMI3 -> GAMERA` or `SAMI3 -> REMIX` feedback through plasma moments, density, or conductance-like diagnostics.

## Interpretation For Current MAGE-WACCMX Work

The current local MAGE-WACCMX path already proves a stable WACCM-X/MAGE/REMIX exchange:

- `MAGE/REMIX -> WACCM-X`: `POT`, `AVG_ENG`, `NUM_FLUX`
- `WACCM-X -> MAGE/REMIX`: `SIGMAP`, `SIGMAH`, `NSRHS`

The current local WACCM-X/SAMI3 path proves a separate neutral-background override:

- `WACCM-X -> SAMI3`: neutral composition, neutral temperature, horizontal neutral winds

The missing official-style bridge is therefore:

- `REMIX -> SAMI3`: high-latitude potential or E-field
- optionally later `SAMI3 -> GAMERA/REMIX`: ionosphere/plasmasphere plasma state feedback
