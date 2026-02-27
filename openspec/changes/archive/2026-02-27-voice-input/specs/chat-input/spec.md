# Chat Input — Voice Input Specification

## Purpose

Extends the existing `ChatInput` component with a microphone button that enables voice-based text entry. This spec covers the mic button visibility, recording interaction, visual feedback, transcript integration with the text input, and preservation of existing functionality.

## Requirements

### Requirement: Mic Button Visibility

The system MUST display a microphone button in the prompt bar only when the browser supports the Web Speech API.

#### Scenario: Mic button shown on supported browser

- GIVEN the user opens the application in a browser that supports the Web Speech API
- WHEN the `ChatInput` component renders
- THEN a microphone button MUST be visible in the prompt bar
- AND the button MUST be positioned to the left of the existing send button

#### Scenario: Mic button hidden on unsupported browser

- GIVEN the user opens the application in a browser that does not support the Web Speech API
- WHEN the `ChatInput` component renders
- THEN the microphone button MUST NOT be visible
- AND the rest of the prompt bar MUST render and function identically to its behavior without voice input

### Requirement: Toggle Recording

The system MUST allow the user to start and stop voice recording by clicking the microphone button.

#### Scenario: Start recording by clicking mic button

- GIVEN the mic button is visible
- AND recording is not active
- WHEN the user clicks the mic button
- THEN speech recognition MUST start
- AND the mic button MUST enter its active/recording visual state

#### Scenario: Stop recording by clicking mic button again

- GIVEN recording is active
- WHEN the user clicks the mic button
- THEN speech recognition MUST stop
- AND the mic button MUST return to its idle visual state

### Requirement: Visual Feedback During Recording

The system MUST provide clear visual feedback to indicate that recording is in progress.

#### Scenario: Recording indicator while listening

- GIVEN recording is active
- WHEN the user looks at the mic button
- THEN the button MUST display a visually distinct active state (e.g., color change)
- AND the button SHOULD display a pulsing animation to indicate ongoing recording

#### Scenario: Idle state when not recording

- GIVEN recording is not active
- WHEN the user looks at the mic button
- THEN the button MUST display its default idle appearance
- AND no pulsing animation SHALL be present

### Requirement: Transcript Insertion into Input Field

The system MUST insert transcribed text into the existing textarea input, preserving any text the user has already typed.

#### Scenario: Transcribed text appended to empty input

- GIVEN the textarea input is empty
- AND recording is active
- WHEN speech recognition produces a final transcript
- THEN the transcript text MUST appear in the textarea input

#### Scenario: Transcribed text appended to existing text

- GIVEN the textarea input already contains text
- AND recording is active
- WHEN speech recognition produces a final transcript
- THEN the transcript text MUST be appended after the existing text
- AND a space SHOULD be inserted between the existing text and the new transcript

#### Scenario: User edits transcribed text before sending

- GIVEN the textarea input contains transcribed text
- WHEN the user modifies the text using the keyboard
- THEN the input MUST accept edits normally
- AND the edited text MUST be sent when the user submits the form

### Requirement: Interim Results Display

The system SHOULD show interim (partial) transcription results in the input field for real-time feedback.

#### Scenario: Interim text shown during speech

- GIVEN recording is active
- AND the user is speaking
- WHEN interim results are received from the speech recognition engine
- THEN the interim text SHOULD be displayed in the input field
- AND it MUST be visually distinguishable or replaced by the final result when available

### Requirement: Error Feedback

The system MUST inform the user when a speech recognition error occurs without disrupting the rest of the UI.

#### Scenario: Permission denied feedback

- GIVEN the user clicks the mic button
- WHEN the browser's microphone permission is denied
- THEN the mic button MUST return to its idle state
- AND the system SHOULD display a brief, non-intrusive message or tooltip indicating that microphone access was denied

#### Scenario: Other recognition errors

- GIVEN recording is active
- WHEN a speech recognition error occurs (network, no-speech, etc.)
- THEN the mic button MUST return to its idle state
- AND the system SHOULD display appropriate feedback to the user

### Requirement: No Interference with Existing Functionality

The addition of voice input MUST NOT alter the existing behavior of the `ChatInput` component.

#### Scenario: Text input and send remain functional

- GIVEN the `ChatInput` component has the voice input feature
- WHEN the user types a message and presses Enter
- THEN the message MUST be sent exactly as before
- AND the input field MUST be cleared after sending

#### Scenario: Send button remains functional

- GIVEN the `ChatInput` component has the voice input feature
- WHEN the user clicks the send button
- THEN the message MUST be sent exactly as before

#### Scenario: Loading state disables interaction

- GIVEN the `loading` prop is `true`
- WHEN the `ChatInput` component renders
- THEN the send button MUST remain disabled
- AND the mic button SHOULD be disabled to prevent starting a recording during a pending request

### Requirement: Mic Button Disabled While Loading

The system SHOULD disable the microphone button when a request is in progress to prevent conflicting interactions.

#### Scenario: Mic button disabled during loading

- GIVEN the `loading` prop is `true`
- AND recording is not active
- WHEN the user attempts to click the mic button
- THEN the mic button MUST be disabled
- AND speech recognition MUST NOT start

#### Scenario: Active recording stops when loading begins

- GIVEN recording is active
- WHEN the `loading` prop transitions to `true` (e.g., user sends the message)
- THEN recording SHOULD stop automatically
- AND the mic button MUST transition to its disabled state
