# Design: Voice Input for Chat Prompt Bar

## Technical Approach

Add a browser-native speech-to-text capability to the existing `ChatInput` component via a new `useSpeechToText` custom hook. The hook encapsulates all Web Speech API lifecycle management, browser feature detection, and state transitions. The mic button slots into the existing input bar layout alongside the send button. No backend changes, no new npm dependencies, and the feature degrades gracefully to invisible when the browser lacks support.

This maps directly to the proposal's four-step approach: hook creation, ChatInput modification, Tailwind styling, and edge-case handling.

## Architecture Decisions

### Decision: Single custom hook (`useSpeechToText`) vs. component-level inline logic

**Choice**: Dedicated hook at `frontend/src/hooks/useSpeechToText.ts`
**Alternatives considered**: Inlining all Web Speech API logic directly inside `ChatInput.tsx`
**Rationale**: The project already follows a hooks-based extraction pattern (`useRFP.ts` encapsulates all API logic). A dedicated hook keeps `ChatInput` focused on presentation, makes the speech logic independently testable, and allows reuse if voice input is ever needed elsewhere.

### Decision: State model — `useReducer` vs. multiple `useState`

**Choice**: Multiple `useState` calls (matching `useRFP` conventions)
**Alternatives considered**: `useReducer` with a state machine for recording lifecycle
**Rationale**: The existing codebase uses `useState` throughout (`useRFP`, `ChatInput`, `App`). The speech hook only has four state variables (`transcript`, `interimTranscript`, `isListening`, `error`), which is within the complexity threshold where `useState` remains clear. `isSupported` is derived from a one-time check, not reactive state.

### Decision: Transcript delivery — append-on-stop vs. live-bind

**Choice**: Append final transcript to `input` on recognition end; show interim transcript as a visual hint only
**Alternatives considered**: (A) Continuously overwrite the textarea value with the running transcript, (B) Append every final segment immediately
**Rationale**: Append-on-stop avoids cursor-fighting when the user types and speaks simultaneously. Interim text is shown as a subtle overlay or suffix so the user sees real-time feedback, but the textarea `input` state only changes once recognition produces a final result or the user stops. This matches the proposal's requirement that "transcribed text appears in the textarea" and "user can edit before sending." Option B (append each final segment immediately) is also viable but creates fragmented text during natural pauses.

### Decision: Mic button placement — left of send vs. inside textarea vs. separate row

**Choice**: Left of the send button, inside the same `div` container, absolutely positioned
**Alternatives considered**: (A) A floating button above the input, (B) Inside the textarea as a suffix icon
**Rationale**: The current layout uses `position: absolute; right: 4` for the send button. Adding the mic button at `right: 14` (to the left of send) keeps the visual weight balanced and requires minimal layout changes. The proposal explicitly states "to the left of the send button."

### Decision: Browser compatibility strategy — runtime detection vs. build-time polyfill

**Choice**: Runtime feature detection via `typeof window.SpeechRecognition !== 'undefined' || typeof window.webkitSpeechRecognition !== 'undefined'`
**Alternatives considered**: (A) Installing `@anthropic/speech-polyfill` or similar, (B) Compile-time `navigator.userAgent` sniffing
**Rationale**: The Web Speech API cannot be meaningfully polyfilled without a backend service (which is out of scope). Runtime detection is the standard approach and lets us conditionally render the mic button. No new dependencies needed.

### Decision: Pulsing animation — Tailwind `animate-pulse` vs. custom CSS keyframes

**Choice**: Custom `@keyframes` rule in `index.css` for a pulsing ring effect around the mic button
**Alternatives considered**: Using Tailwind's built-in `animate-pulse` class
**Rationale**: `animate-pulse` applies an opacity fade, but the proposal calls for a "pulsing ring animation" — a concentric ring expanding outward from the button. This requires a `box-shadow` or pseudo-element animation that Tailwind's built-in utility does not cover. The project already has custom CSS in `index.css` (scrollbar styles, selection color, transition timing), so adding a keyframe there is consistent.

## Data Flow

```
  User clicks mic button
         │
         ▼
  useSpeechToText.startListening()
         │
         ├── Creates SpeechRecognition instance
         ├── Sets lang = 'es-ES', interimResults = true
         ├── Registers onresult / onerror / onend
         └── Calls recognition.start()
                  │
                  ▼
  ┌────────────────────────────────┐
  │   SpeechRecognition (browser)  │
  │   fires onresult events        │
  └────────┬───────────────────────┘
           │
           ▼
  Hook processes results:
    ├── interimTranscript ← concatenation of non-final results
    └── transcript ← concatenation of final results
           │
           ▼
  User clicks mic button again (or recognition fires onend)
         │
         ▼
  useSpeechToText.stopListening()
    ├── recognition.stop()
    ├── isListening = false
    └── returns final transcript
           │
           ▼
  ChatInput receives transcript via hook
    ├── setInput(prev => prev + (prev ? ' ' : '') + transcript)
    ├── Clears hook transcript
    └── User can now edit and send normally
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/hooks/useSpeechToText.ts` | Create | Custom hook encapsulating Web Speech API: feature detection, start/stop lifecycle, interim/final transcript state, error handling, cleanup on unmount |
| `frontend/src/components/ChatInput.tsx` | Modify | Import and use `useSpeechToText` hook; add mic button to the left of send button; wire transcript to `input` state on recording end; conditionally render mic button based on `isSupported`; adjust textarea `pr-*` padding to accommodate the new button |
| `frontend/src/index.css` | Modify | Add `@keyframes pulse-ring` animation for the recording indicator |

## Interfaces / Contracts

### `useSpeechToText` hook API

```typescript
// frontend/src/hooks/useSpeechToText.ts

interface UseSpeechToTextReturn {
  /** Final accumulated transcript from the current/last session */
  transcript: string;
  /** Interim (not yet finalized) transcript — display only */
  interimTranscript: string;
  /** Whether the microphone is currently recording */
  isListening: boolean;
  /** Whether the browser supports the Web Speech API */
  isSupported: boolean;
  /** Last error message, or null */
  error: string | null;
  /** Begin speech recognition */
  startListening: () => void;
  /** End speech recognition and finalize transcript */
  stopListening: () => void;
  /** Reset transcript and error state */
  resetTranscript: () => void;
}

interface UseSpeechToTextOptions {
  /** BCP 47 language tag. Default: 'es-ES' */
  lang?: string;
  /** Whether to collect interim results. Default: true */
  interimResults?: boolean;
  /** Whether recognition restarts automatically after onend. Default: false */
  continuous?: boolean;
}

function useSpeechToText(options?: UseSpeechToTextOptions): UseSpeechToTextReturn;
```

### Web Speech API type augmentation

```typescript
// Inline in useSpeechToText.ts (module-scoped declaration)

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string;
  readonly message: string;
}

interface SpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}
```

### ChatInput updated props (no change)

The `ChatInputProps` interface remains unchanged — the hook is consumed internally, not passed as props.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `useSpeechToText` hook: start/stop lifecycle, transcript accumulation, error handling, unsupported browser behavior | Mock `window.SpeechRecognition` constructor; fire synthetic `onresult`, `onerror`, `onend` events; assert state transitions. Use `@testing-library/react` `renderHook` if test infra is set up, otherwise manual verification. |
| Unit | `ChatInput` rendering: mic button visibility when supported/unsupported, button state toggling, transcript-to-input wiring | Render `ChatInput` with mocked `useSpeechToText` return values; assert button presence/absence and class changes. |
| Manual | End-to-end: speak into mic on Chrome, verify text appears, edit, send | Manual QA in Chrome/Edge. Verify Firefox/Safari graceful degradation (no mic button visible). |
| Lint | ESLint pass | Run `npx eslint` with existing flat config to verify no regressions. |

## Migration / Rollout

No migration required. This is a purely additive frontend feature:
- No database changes
- No API changes
- No environment variable changes
- No feature flags needed (the mic button self-hides on unsupported browsers)
- Rollback is simply reverting the three file changes listed above

## Open Questions

- [ ] Should the mic button show a tooltip ("Tu navegador no soporta entrada de voz") on unsupported browsers, or be completely invisible? The proposal says "hide or show a tooltip" — a decision should be made before implementation. **Recommendation**: hide completely to avoid visual noise for Firefox/Safari users who cannot use the feature.
- [ ] Should `continuous` mode be enabled (recognition keeps going after pauses) or single-shot (stops after one utterance)? The proposal says "no continuous/always-on listening" is in scope, but the Web Speech API's `continuous` property controls whether it auto-stops after a phrase. **Recommendation**: set `continuous: false` so recognition stops naturally after a pause, matching user expectation of "speak one thought, review, send."
