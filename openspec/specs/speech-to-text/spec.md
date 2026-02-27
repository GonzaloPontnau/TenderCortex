# Speech-to-Text Specification

## Purpose

Provides browser-native speech-to-text capability via the Web Speech API, encapsulated in a reusable React hook (`useSpeechToText`). This spec covers feature detection, speech recognition lifecycle, transcript management, error handling, and cleanup.

## Requirements

### Requirement: Browser Compatibility Detection

The system MUST detect whether the browser supports the Web Speech API (`SpeechRecognition` or `webkitSpeechRecognition`) and expose an `isSupported` flag.

#### Scenario: Browser supports Web Speech API

- GIVEN the user opens the application in a Chromium-based browser (Chrome, Edge, Brave, Arc)
- WHEN the `useSpeechToText` hook initializes
- THEN `isSupported` MUST be `true`

#### Scenario: Browser does not support Web Speech API

- GIVEN the user opens the application in a browser without Web Speech API support (e.g., Firefox, Safari)
- WHEN the `useSpeechToText` hook initializes
- THEN `isSupported` MUST be `false`
- AND no `SpeechRecognition` instance SHALL be created

### Requirement: Start Listening

The system MUST expose a `startListening()` function that initiates speech recognition when the Web Speech API is supported.

#### Scenario: Successfully start listening

- GIVEN `isSupported` is `true`
- AND `isListening` is `false`
- WHEN the user invokes `startListening()`
- THEN `isListening` MUST transition to `true`
- AND the browser MUST request microphone permission (if not already granted)
- AND speech recognition MUST begin capturing audio

#### Scenario: Start listening when already listening

- GIVEN `isListening` is `true`
- WHEN the user invokes `startListening()`
- THEN the system SHOULD ignore the call without error
- AND `isListening` MUST remain `true`

#### Scenario: Start listening when unsupported

- GIVEN `isSupported` is `false`
- WHEN the user invokes `startListening()`
- THEN the system MUST NOT throw an error
- AND `isListening` MUST remain `false`

### Requirement: Stop Listening

The system MUST expose a `stopListening()` function that halts speech recognition.

#### Scenario: Successfully stop listening

- GIVEN `isListening` is `true`
- WHEN the user invokes `stopListening()`
- THEN `isListening` MUST transition to `false`
- AND speech recognition MUST stop capturing audio

#### Scenario: Stop listening when not listening

- GIVEN `isListening` is `false`
- WHEN the user invokes `stopListening()`
- THEN the system SHOULD ignore the call without error

### Requirement: Transcript Management

The system MUST expose a `transcript` value containing the final recognized text. The system SHOULD also provide interim (partial) results for real-time feedback.

#### Scenario: Final transcript produced after speech

- GIVEN `isListening` is `true`
- AND the user speaks a phrase
- WHEN the Web Speech API emits a result with `isFinal` set to `true`
- THEN the `transcript` value MUST be updated with the finalized text
- AND the finalized text MUST be appended to any previously accumulated transcript within the same listening session

#### Scenario: Interim results available during speech

- GIVEN `isListening` is `true`
- AND the user is actively speaking
- WHEN the Web Speech API emits a result with `isFinal` set to `false`
- THEN the system SHOULD expose interim text for display purposes
- AND interim text MUST NOT be committed to the final `transcript`

#### Scenario: Transcript resets between sessions

- GIVEN the user has completed a listening session (stopped listening)
- WHEN the user invokes `startListening()` again
- THEN the `transcript` MUST be reset to an empty string

### Requirement: Language Configuration

The system MUST configure speech recognition with Spanish (`es-ES`) as the default language.

#### Scenario: Default language is Spanish

- GIVEN the `useSpeechToText` hook initializes
- WHEN a `SpeechRecognition` instance is created
- THEN the `lang` property MUST be set to `es-ES`

### Requirement: Error Handling

The system MUST handle speech recognition errors gracefully and expose an `error` state.

#### Scenario: Microphone permission denied

- GIVEN `isListening` is `false`
- WHEN the user invokes `startListening()`
- AND the browser's microphone permission prompt is denied
- THEN `isListening` MUST transition back to `false`
- AND `error` MUST contain a descriptive message indicating permission was denied

#### Scenario: Network error during recognition

- GIVEN `isListening` is `true`
- WHEN the Web Speech API emits a `network` error event
- THEN `isListening` MUST transition to `false`
- AND `error` MUST contain a descriptive message

#### Scenario: Recognition ends unexpectedly

- GIVEN `isListening` is `true`
- WHEN the Web Speech API fires an `onend` event without the user explicitly stopping
- THEN `isListening` MUST transition to `false`

### Requirement: Cleanup on Unmount

The system MUST stop any active speech recognition and release resources when the hook's host component unmounts.

#### Scenario: Component unmounts while listening

- GIVEN `isListening` is `true`
- WHEN the component using the hook unmounts
- THEN speech recognition MUST be stopped
- AND no further state updates SHALL occur
