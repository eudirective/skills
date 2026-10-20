# Consultation assurance host capability decision

**Decision date:** 2026-10-20
**Scope:** FreeMovement Law skills plugin 0.50.0 / core 0.49.0
**Status:** bounded local structural validation is available; production host release enforcement is not implemented.

## Capability result

| Candidate | Pre-output veto | Bind gate result to exact released answer | Decision |
| --- | --- | --- | --- |
| Skills-only plugin used in ChatGPT | No supported skill instruction can intercept or veto a completed answer. A skill tells the model how to work. | No | `not implemented / external host dependency` |
| Codex local command-line workflow | A local wrapper can validate a receipt and withhold the exact local answer artifact it reads. It only governs calls routed through that wrapper. | Yes, for the exact local receipt and answer byte strings in that invocation; it is not authenticated approval and does not govern other output channels. | Opt-in local wrapper is implemented by `scripts/consultation_release_gate.py`; not a production host gate. |
| Codex Desktop plugin lifecycle hook | Official documentation describes a `Stop` hook and plugin `hooks.json` entry. The hook can ask Codex to continue with a new instruction when it returns `decision: "block"`; it does not describe a hard rejection of the turn. The hook is available only for manually installed plugins and plugins with lifecycle hooks are not eligible for the public plugin directory. `suppressOutput` is documented as unsupported. | The hook receives the last assistant message, but no target-deployment end-to-end test establishes immutable answer binding or a final release veto for this plugin. | Documented capability is unsuitable as verified production enforcement for this skills-only plugin. No hook was installed or added. |

## Evidence and sources

Reviewed 2026-10-20:

- OpenAI, [Build plugins](https://developers.openai.com/plugins/build/plugins): lifecycle hook support and its manually-installed/public-directory boundary; plugin manifest hook configuration.
- OpenAI, [Hooks](https://learn.chatgpt.com/docs/hooks): Stop hook input and `decision: "block"` continuation behavior; `suppressOutput` is not implemented.
- OpenAI, [Skills](https://developers.openai.com/plugins/concepts/skills): skills provide reusable instructions and workflows, not a host output interceptor.

The documentation review is not a runtime test of ChatGPT or Codex Desktop. No plugin was installed, no lifecycle hook was exercised, and no hosted answer was intercepted.

## Consequences

- `consultation_route_gate.py` checks only the privacy-minimised route receipt and artifacts it declares. It cannot prove that a conditional workflow or relevant C27 check was not omitted, that model-declared work occurred, or that a reference is truthful.
- `consultation_release_gate.py` is an optional local integrity wrapper for an exact local artifact. It rejects changed answer or receipt bytes and reruns structural validation. Its binding JSON is not signed, does not authenticate who approved anything, and does not intercept other output channels.
- A skills-only ChatGPT consultation can still bypass both local scripts. Therefore `host enforcement: not implemented` must remain visible wherever execution provenance is reported.
- A future hard release gate requires an explicitly supported host integration and a target-deployment smoke test that proves the host withholds the exact answer on a failed check.
