# Tasks: Voice Input for Chat Prompt Bar

## Phase 1: Infrastructure / Foundation

- [x] 1.1 Create `frontend/src/hooks/useSpeechToText.ts` with Web Speech API type declarations (`SpeechRecognitionEvent`, `SpeechRecognitionErrorEvent`, `SpeechRecognition` interface, and `Window` global augmentation for `SpeechRecognition` / `webkitSpeechRecognition`)
- [x] 1.2 In `useSpeechToText.ts`, implement the `UseSpeechToTextOptions` interface (`lang?: string`, `interimResults?: boolean`, `continuous?: boolean`) and the `UseSpeechToTextReturn` interface (`transcript`, `interimTranscript`, `isListening`, `isSupported`, `error`, `startListening`, `stopListening`, `resetTranscript`)
- [x] 1.3 In `useSpeechToText.ts`, implement the `isSupported` detection logic: check `typeof window.SpeechRecognition !== 'undefined' || typeof window.webkitSpeechRecognition !== 'undefined'` on hook initialization; store as a constant (not reactive state)

## Phase 2: Core Implementation — useSpeechToText Hook

- [x] 2.1 In `useSpeechToText.ts`, implement `startListening()`: guard against `!isSupported` and `isListening === true`; create a `SpeechRecognition` instance; set `lang` (default `'es-ES'`), `interimResults` (default `true`), `continuous` (default `false`); register `onresult`, `onerror`, `onend` handlers; call `recognition.start()`; set `isListening = true` and clear `error`
- [x] 2.2 In `useSpeechToText.ts`, implement the `onresult` handler: iterate `event.results` from `event.resultIndex`; separate `isFinal` results (append to `transcript` state) from interim results (set `interimTranscript` state); ensure interim text is never committed to `transcript`
- [x] 2.3 In `useSpeechToText.ts`, implement `stopListening()`: guard against `!isListening`; call `recognition.stop()`; set `isListening = false`
- [x] 2.4 In `useSpeechToText.ts`, implement `onerror` handler: map error codes (`not-allowed` → permission denied message, `network` → network error message, others → generic message); set `error` state; set `isListening = false`
- [x] 2.5 In `useSpeechToText.ts`, implement `onend` handler: set `isListening = false` (handles unexpected stops and natural speech-end)
- [x] 2.6 In `useSpeechToText.ts`, implement `resetTranscript()`: clear `transcript`, `interimTranscript`, and `error` to initial values
- [x] 2.7 In `useSpeechToText.ts`, implement cleanup via `useEffect` return: if recognition instance exists and `isListening` is true, call `recognition.abort()`; prevent state updates after unmount using a ref flag

## Phase 3: Core Implementation — ChatInput Integration

- [x] 3.1 In `frontend/src/components/ChatInput.tsx`, import `useSpeechToText` from `../hooks/useSpeechToText` and invoke the hook at the top of the component, destructuring `transcript`, `interimTranscript`, `isListening`, `isSupported`, `error`, `startListening`, `stopListening`, `resetTranscript`
- [x] 3.2 In `ChatInput.tsx`, add a `useEffect` that watches `transcript`: when `transcript` is non-empty, append it to the existing `input` state (with a space separator if `input` is non-empty), then call `resetTranscript()`
- [x] 3.3 In `ChatInput.tsx`, add a `useEffect` that watches the `loading` prop: when `loading` transitions to `true` and `isListening` is `true`, call `stopListening()` to auto-stop recording on message send
- [x] 3.4 In `ChatInput.tsx`, add a mic toggle button to the left of the existing send button inside the button container: conditionally render only when `isSupported` is `true`; `onClick` toggles between `startListening()` and `stopListening()`; set `disabled` when `loading` is `true`; use a microphone SVG icon (inline or from an icon set already in use)
- [x] 3.5 In `ChatInput.tsx`, apply conditional CSS classes to the mic button: idle state uses `text-slate-400 hover:text-orange-500` (matching existing palette); active/recording state uses `text-red-500` with the `animate-pulse-ring` class
- [x] 3.6 In `ChatInput.tsx`, adjust the textarea's right padding (`pr-*` class) to accommodate the new mic button alongside the send button (increase from current value to allow space for both buttons)
- [x] 3.7 In `ChatInput.tsx`, optionally display a brief error tooltip/message near the mic button when `error` is non-null (e.g., a small `<span>` that auto-hides after a few seconds)

## Phase 4: Styling

- [x] 4.1 In `frontend/src/index.css`, add a `@keyframes pulse-ring` animation: define a ring expanding outward with decreasing opacity (using `box-shadow` or a pseudo-element scale transform)
- [x] 4.2 In `frontend/src/index.css`, add the `.animate-pulse-ring` utility class that applies the `pulse-ring` keyframe with appropriate duration (`1.5s`), iteration (`infinite`), and timing function (`ease-out`)

## Phase 5: Testing

- [ ] 5.1 Create `frontend/src/__tests__/useSpeechToText.test.ts` (or co-located test file): mock `window.SpeechRecognition` constructor; test that `isSupported` is `true` when mock is present and `false` when removed
- [ ] 5.2 Test `startListening()`: verify `isListening` transitions to `true`, `recognition.start()` is called, and calling `startListening()` while already listening is a no-op
- [ ] 5.3 Test `startListening()` when unsupported: verify `isListening` remains `false` and no error is thrown
- [ ] 5.4 Test `onresult` handler: fire a synthetic result event with `isFinal: true`; assert `transcript` is updated; fire event with `isFinal: false`; assert `interimTranscript` is updated but `transcript` is not
- [ ] 5.5 Test `stopListening()`: verify `isListening` transitions to `false` and `recognition.stop()` is called
- [ ] 5.6 Test error handling: fire synthetic `onerror` with `error: 'not-allowed'`; assert `error` state contains permission message and `isListening` is `false`
- [ ] 5.7 Test cleanup on unmount: verify `recognition.abort()` is called when component unmounts while listening
- [ ] 5.8 Test `ChatInput` rendering: mock `useSpeechToText` to return `isSupported: true`; assert mic button is present in DOM; mock `isSupported: false`; assert mic button is absent
- [ ] 5.9 Test `ChatInput` mic button toggle: simulate click; verify `startListening` is called; simulate click again; verify `stopListening` is called
- [ ] 5.10 Test `ChatInput` transcript integration: set mock `transcript` to a value; verify `input` state is updated with appended text
- [ ] 5.11 Test `ChatInput` loading state: set `loading` prop to `true`; verify mic button is disabled
- [ ] 5.12 Run `npx eslint frontend/src/` and verify zero new lint errors or warnings from the added/modified files

## Phase 6: Manual Verification

- [ ] 6.1 Open the app in Chrome/Edge: verify mic button is visible, click it, speak, verify transcript appears in textarea, edit text, send message — confirm end-to-end flow works
- [ ] 6.2 Open the app in Firefox: verify mic button is NOT visible and all existing functionality works identically
- [ ] 6.3 In Chrome, deny microphone permission when prompted: verify mic button returns to idle, error feedback is shown, and no console errors occur
