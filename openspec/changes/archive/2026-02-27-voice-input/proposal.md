# Proposal: Voice Input for Chat Prompt Bar

## Intent

Users interacting with TenderCortex often need to ask lengthy or detailed questions about tender documents. Typing complex queries can be slow and inconvenient, especially on devices with limited keyboard comfort. Adding voice input to the chat prompt bar allows users to dictate their questions naturally, reducing friction and improving the overall user experience. This is a purely frontend enhancement with zero backend impact.

## Scope

### In Scope
- Microphone toggle button added to the `ChatInput` component, positioned to the left of the existing send button
- Integration with the browser-native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) for real-time speech-to-text
- Custom React hook (`useSpeechToText`) encapsulating all Web Speech API logic, state management, and browser compatibility detection
- Visual feedback indicating recording state (button color change, pulsing animation)
- Transcribed text inserted into the existing textarea input, allowing the user to review, edit, and send as a normal text prompt
- Graceful degradation: hide the mic button or show a tooltip when the browser does not support the Web Speech API
- Spanish language recognition as default (matching the existing UI language), with fallback to browser default

### Out of Scope
- Backend speech-to-text processing or API integration (e.g., Whisper, Google Cloud Speech)
- Audio file upload or pre-recorded audio transcription
- Continuous / always-on listening mode
- Multi-language switching UI (future enhancement)
- Voice command interpretation (e.g., "send message", "clear input")
- Mobile-specific optimizations beyond standard responsive behavior

## Approach

1. **Create a `useSpeechToText` custom hook** that wraps the Web Speech API. The hook will expose: `transcript`, `isListening`, `isSupported`, `startListening()`, `stopListening()`, and `error` state. It will use `webkitSpeechRecognition` with a fallback check, set `interimResults: true` for real-time feedback, and configure `lang: 'es-ES'` by default.

2. **Modify `ChatInput.tsx`** to import the hook, add a microphone button to the left of the send button, and wire the transcript output into the existing `input` state. When the user stops recording, the final transcript appends to any existing text in the input field.

3. **Style the mic button** using TailwindCSS 4, matching the existing design system (slate/orange gradient palette, rounded buttons, hover/active transitions). Add a pulsing ring animation when actively recording.

4. **Handle edge cases**: browser compatibility check on mount, permission denial error handling, auto-stop after silence timeout (Web Speech API handles this natively), and cleanup of the recognition instance on unmount.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/components/ChatInput.tsx` | Modified | Add mic button, integrate `useSpeechToText` hook, wire transcript to input state |
| `frontend/src/hooks/useSpeechToText.ts` | New | Custom hook encapsulating Web Speech API logic |
| `frontend/src/types.ts` | Modified (if needed) | Add TypeScript declarations for `webkitSpeechRecognition` if not covered by existing types |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Web Speech API not supported in Firefox/Safari | High | Feature-detect on mount; hide mic button when unsupported; no degraded UX for non-Chrome users since the text input remains fully functional |
| Microphone permission denied by user | Medium | Catch the `not-allowed` error, display a non-intrusive tooltip or brief message, revert button to idle state |
| Interim transcript flickers or duplicates text | Low | Use the `isFinal` flag from `SpeechRecognitionResult` to only commit final segments to input state; keep interim results in a separate display-only state |
| Speech recognition stops unexpectedly | Low | Listen for `onerror` and `onend` events in the hook; auto-reset `isListening` state and allow the user to restart |

## Rollback Plan

Since this change is purely additive frontend code with no backend or data model changes:
1. Remove the `useSpeechToText.ts` hook file.
2. Revert `ChatInput.tsx` to its previous version (remove mic button and hook import).
3. Remove any added type declarations from `types.ts`.
4. No database migrations, API changes, or configuration changes to revert.

## Dependencies

- **Web Speech API**: Browser-native, no npm packages required. Supported in Chromium-based browsers (Chrome, Edge, Arc, Brave). Partial or no support in Firefox and Safari.
- No new npm dependencies needed.

## Success Criteria

- [ ] Mic button is visible in the chat input bar on supported browsers
- [ ] Mic button is hidden or disabled with a tooltip on unsupported browsers
- [ ] Clicking the mic button requests microphone permission and starts transcription
- [ ] Speech is transcribed in real-time and appears in the textarea input
- [ ] User can edit the transcribed text before sending
- [ ] Clicking the mic button again (or the user stopping speech) ends recording
- [ ] Denying microphone permission does not break the UI or throw unhandled errors
- [ ] Existing text input and send functionality remain completely unaffected
- [ ] The component passes ESLint checks with the existing flat config
