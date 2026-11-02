# Viewer delivery gate

Status: **PASS** for the implemented viewer. The analytical hypothesis result is separately reported as failed for real-data short runs; a UI pass does not change that result.

Owner selected antislop during construction and an analyst workbench with light pitch, compact controls and clear labels. Direction and reasons are in `DESIGN.md`. No optional skill installation or repository routing modification was performed.

## Interaction record

| Control or state | Status | Observed result |
|---|---|---|
| Search | PASS | Player/name and exact candidate-ID searches narrow results; unmatched search yields an empty message. |
| Match split | PASS | Development shows 495, held-out 306, combined catalogue 801. |
| Coverage category | PASS | Gap filter shows 44 held-out candidates; continuous and brief-gap options switch catalogue membership. |
| Detected-trio filter | PASS | Filters actual `all_involved_detected` flag; interface explains its restricted scope. |
| Ambiguity filter | PASS | Close-alternative cases are retrievable; combined filters can produce a verified empty state. |
| Candidate selector | PASS | Selecting known IDs updates player names, measurement details, pitch and timeline together. |
| Play / Pause | PASS | Button changes to Pause and clock advances; pausing stops playback. Playback stops at replay end. |
| Speed | PASS | 2x playback advances frames faster; selection is wired into interval duration. |
| Back / Forward | PASS | Frame clock changes by 0.2 s; endpoint controls disable appropriately. |
| Transfer frame | PASS | Jumps to the incoming confirmation frame, e.g. 16:09.4 in the 1.9 s gap example. |
| Scrubber | PASS | Keyboard ArrowLeft/ArrowRight changes frame and restores the prior clock on reversal. |
| Nearest link | PASS | Black dashed baseline link appears over the proposed assignment replay. |
| Proximity edges | PASS | 8 m opponent edges draw; goalkeepers are excluded via the exported goalkeeper flag. |
| Focus control | PASS | Unchecking shows full pitch and checking restores the transfer view. |
| Download | PASS | Browser generated a real CSV, read back as 801 rows; export remains the complete catalogue when filters narrow the view. |
| Theme | PASS | Light/dark control changes actual theme and label; both were visually inspected. Canvas and legend retain their readable tactical-board background. |
| Keyboard focus | PASS | Tab moved from transfer control to speed; computed focus outline was solid and visible. Native buttons, selects, search and slider remain keyboard operable. Escape stops playback. |
| Loading state | PASS | Initial HTML announces loading of the embedded catalogue until JSON binding completes; no network data fetch is required. |
| Empty state | PASS | Zero-result search hides workbench with computed `display:none` and gives a corrective instruction. |
| Error state | PASS | A separate malformed-JSON fixture shows a specific rebuild instruction, hides replay and disables data selection controls; fixture tab was closed after checking. |
| Console | PASS | Browser dev log returned no error/warning entries on the actual viewer after overlay/candidate interactions. |

## Hard gate

| Rule | Status | Evidence |
|---|---|---|
| R-02, authored copy | PASS | Authored UI uses ordinary punctuation; no em dash. Source quotations remain source material. |
| R-03, responsive layout | PASS | Phone and tablet checks found and fixed range margin and revision-hash overflow; final narrow check has equal client/scroll width. |
| R-17, statistics | PASS | Counts and rates bind to frozen JSON; all 801 candidate gaps independently reconciled. |
| R-18, testimonials | PASS | None included. |
| R-23, assets and structure | PASS | Owner chose workbench direction; requested pitch animation and searchable collection use actual tracking. No logo, avatar or fabricated identity. |
| R-24, navigation | PASS | Skip link targets playback; sole external attribution link is the verified upstream repository. |
| R-25, contrast | PASS | Twelve foreground/background pairs computed with WCAG luminance formula; all text pairs >=4.5, all tested non-text pairs >=3. Minimum non-text ratio 4.16. |
| R-26, functional controls | PASS | Every control listed above has observed behavior. |
| R-27, data states | PASS | Loading text, corrected zero-result state and isolated corrupt-JSON error fixture verified. |
| R-28, FAQ | PASS | No FAQ is present. |
| R-32, keyboard | PASS | Native semantic controls, visible focus, Tab/arrow operation and Escape handler verified. |
| R-33, source edits | PASS | UI features are authored in `viewer/template.html`; builder substitutes only the frozen data payload. |
| R-34, themes | PASS | Both themes inspected; contrast tokens and fixed-light pitch/legend preserve readability. |
| R-35, execution | PASS | Built and opened viewer in real in-app browser; element-by-element interaction record above. |
| R-36, claims | PASS | No claim of tactical accuracy improvement, known coaching assignment, communication failure or defensive blame. |
| R-37, direction | PASS | Owner choice and design read recorded before UI generation. |
| R-38, content | PASS | Every player, event and metric derives from the verified inputs; empty/error states carry explicit explanations. |

## Purpose gate

| Rule | Status | Reason / evidence |
|---|---|---|
| R-01, palette | PASS | Team blue/slate and outgoing amber/incoming green encode spatial roles; no decorative gradient. |
| R-04, icons | PASS | No generic icon library; player geometry serves the transfer mechanism. |
| R-06, typography | PASS | Editorial Georgia title and system sans-serif controls have written legibility reasons. |
| R-07, background | PASS | Pitch markings are the actual coordinate reference, not decorative page texture. |
| R-08, arrows | PASS | Controls use action text; no decorative arrow treatment. |
| R-09, badges | PASS | No promotional capsule badges. |
| R-10, glass | PASS | None used. |
| R-12, shadows | PASS | None used. |
| R-13, glow | PASS | None used. |
| R-14, cards | PASS | No feature-card grid; replay and evidence follow the analyst's inspection task. |
| R-19, motion | PASS | User-initiated tracking playback illustrates position changes; no decorative/autoplay loop. Reduced-motion preference is respected. |
| R-22, illustration | PASS | All pitch marks come from actual replay positions; no generic illustration. |

## Liveliness and craftsmanship

| Item | Status | Evidence |
|---|---|---|
| Dials | PASS | ENERGY 1 / RHYTHM 2 / MOTION 2 declared in design record. |
| Dial consistency | PASS | Calm controls, wide spatial focal point, evidence below/alongside, purposeful replay motion. |
| Focal point | PASS | Pitch dominates the workbench, with transfer trio shapes and current assignment link. |
| Structural whitespace | PASS | Selection, replay, measurement and caveats use separate spacing bands. |
| Accent | PASS | Amber/green highlight the outgoing/incoming pair at the mechanism being inspected. |
| Identity motif | PASS | A/O/I circles, square and triangle recur in pitch, key and video. |
| Design read | PASS | Recorded before UI construction in `DESIGN.md`. |
| C-1, intent | PASS | Major visual decisions have explicit reasons. |
| C-2, completeness | PASS | Every visible interactive control was exercised. |
| C-3, composition | PASS | Sections support selection, spatial inspection and evidence interpretation. |
| C-4, resilience | PASS | Empty/corrupt data states, narrow reflow, themes, focus and control endpoints checked. Text uses relative sizes and content reflow. |
| C-5, evidence | PASS | Metrics bind to outputs; synthetic and tactical claims remain distinct. |
| R-05, layout | PASS | Workbench follows candidate selection and replay needs, with no promotional shell. |
| R-11, radius | PASS | Small consistent control radii; no pill-card system. |
| R-15, actions | PASS | Play, transfer frame, frame stepping and download name their real actions. |
| R-16, copy | PASS | Plain functional wording; no unsupported marketing claims. |
| R-20, identity | PASS | The transfer-specific shapes, pitch and observation key identify a football review instrument. |
| R-21, theme choice | PASS | Owner-selected light workbench plus a working dark option. |
| R-29, color system | PASS | Three role colors plus one transfer accent, with neutrals for context. |
| R-30, originality | PASS | No reference-product clone or borrowed dashboard shell. |
| R-31, reasons | PASS | Color, typography, layout, spacing, shapes and motion reasons are recorded. |

Video verification: FFprobe confirms 32.000 seconds, 1280 x 720, 20 fps, 640 frames. Intro, both real examples and results-card frames were visually inspected. Context labels distinguish the measured transfer window from surrounding replay time.
