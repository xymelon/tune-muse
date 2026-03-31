# Feature Specification: AI Music Recommendation via Vocal Analysis

**Feature Branch**: `001-ai-music-recommend`
**Created**: 2026-03-29
**Status**: Draft
**Input**: User description: "Build a web-based AI music recommendation product from scratch. Users upload audio or sing directly; the system analyzes melody, rhythm, mood, timbre, and expression traits to recommend suitable song directions, genres, and styles — without heavy reliance on existing music databases. Prioritizes lowering the barrier for users to express musical preferences, with analysis over recognition, relevance over quantity, explainable recommendations, honest confidence levels, and minimal audio data processing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record and Analyze Singing (Priority: P1)

A user opens the web app and records themselves singing a short segment (10–60 seconds) directly in the browser. The system captures the audio, processes it through AI analysis, and returns a vocal profile summarizing the user's melody range, rhythm patterns, emotional expression, and timbre characteristics. The user sees a clear, visual breakdown of their vocal traits before any recommendations are generated.

**Why this priority**: This is the core value proposition — enabling users to express their musical identity simply by singing. Without audio capture and analysis, no recommendations can be generated. This story alone delivers immediate value: users discover their vocal characteristics.

**Independent Test**: Can be fully tested by recording a 30-second vocal clip and verifying that the system returns a vocal profile with at least melody range, rhythm stability, mood tendency, and timbre type — all displayed in a user-friendly visual format.

**Acceptance Scenarios**:

1. **Given** a user on the home page, **When** they tap "Record" and sing for 15 seconds then tap "Stop", **Then** the system displays a processing indicator and within 30 seconds shows a vocal analysis profile with at least 4 trait dimensions (melody, rhythm, mood, timbre).
2. **Given** a user who has finished recording, **When** the analysis completes, **Then** each trait dimension includes a plain-language description (e.g., "Your voice has a warm, mid-range tone with gentle vibrato") rather than raw numerical scores alone.
3. **Given** a user in a noisy environment, **When** the recording quality is too low for reliable analysis, **Then** the system notifies the user and suggests re-recording in a quieter setting instead of producing unreliable results.

---

### User Story 2 - Upload Audio for Analysis (Priority: P2)

A user who has a pre-recorded audio file (e.g., a voice memo of themselves singing) uploads it through the web app instead of recording live. The system accepts common audio formats, runs the same AI analysis pipeline, and returns the same vocal profile and recommendations as the live recording flow.

**Why this priority**: Many users already have recordings of themselves singing. Supporting file upload broadens access and removes the friction of needing to sing on the spot. It reuses the same analysis pipeline, making it a natural extension of P1.

**Independent Test**: Can be fully tested by uploading a 30-second MP3 or WAV file and verifying that the system returns the same type of vocal profile as the live recording flow.

**Acceptance Scenarios**:

1. **Given** a user on the home page, **When** they select "Upload Audio" and choose an MP3 file under 10 MB, **Then** the system accepts the file, shows a progress indicator, and displays the vocal analysis profile within 30 seconds.
2. **Given** a user uploads an audio file longer than 3 minutes, **Then** the system analyzes a representative segment (first 60 seconds of vocal content) and informs the user which portion was analyzed.
3. **Given** a user uploads a non-audio file or a corrupted file, **Then** the system displays a clear error message listing supported formats (MP3, WAV, M4A, OGG) and invites them to try again.

---

### User Story 3 - Receive Personalized Song Recommendations (Priority: P1)

After the vocal analysis is complete (from either recording or upload), the system generates personalized song recommendations. Rather than linking to a specific track database, recommendations describe song directions: genre/style categories, tempo ranges, vocal complexity levels, mood alignment, and example reference songs where available. Each recommendation includes an explanation of why it matches the user's vocal profile.

**Why this priority**: This is the product's ultimate deliverable — connecting vocal analysis to actionable song practice recommendations. Without this, the analysis alone has limited utility for the stated goal of helping people find songs to practice and perform.

**Independent Test**: Can be fully tested by completing a vocal analysis and verifying that the system returns 3–8 recommendation cards, each with genre/style, tempo range, vocal difficulty, mood alignment, and an explanation of the match.

**Acceptance Scenarios**:

1. **Given** a completed vocal analysis profile, **When** the user views the recommendation screen, **Then** the system displays 3–8 recommendation entries, each showing: song direction/genre, tempo range, vocal difficulty level, mood alignment, and a 1–2 sentence explanation of why this direction suits the user.
2. **Given** a recommendation result, **When** the user reads an explanation, **Then** the explanation references specific traits from the user's vocal analysis (e.g., "Your stable mid-range and warm timbre suit ballad-style songs at 70–90 BPM").
3. **Given** a recommendation result, **When** confidence in a particular recommendation is low, **Then** the system clearly labels it as "exploratory" or "worth trying" rather than presenting it with the same certainty as high-confidence matches.

---

### User Story 4 - View and Compare Analysis History (Priority: P3)

A returning user can view their past analysis sessions and compare how their vocal profile has evolved over time. This supports the practice-oriented goal: users can track progress as they develop their singing abilities and see how their recommended song directions shift.

**Why this priority**: This supports long-term engagement and the practice use case, but requires user accounts and persistence — more infrastructure than the core analysis/recommendation loop. It is valuable but not essential for initial launch.

**Independent Test**: Can be fully tested by completing two analyses on different days, then viewing the history page and verifying both sessions appear with dates, vocal profiles, and a comparison view highlighting changes.

**Acceptance Scenarios**:

1. **Given** a user with 2+ past analysis sessions, **When** they navigate to the history page, **Then** each session is listed with date, a summary of vocal traits, and the recommendations generated.
2. **Given** a user viewing their history, **When** they select two sessions to compare, **Then** the system shows a side-by-side or overlay view highlighting changes in vocal traits (e.g., "Range expanded from C3–G4 to C3–A4").

---

### Edge Cases

- What happens when the user sings extremely quietly or whispers? The system MUST detect insufficient vocal signal and prompt for a louder performance rather than producing a misleading analysis.
- What happens when the uploaded audio contains only instrumental music with no vocals? The system MUST detect the absence of vocal content and inform the user that vocal input is required.
- What happens when the user sings in a language the system has not been trained on? The analysis MUST focus on acoustic and musical properties (melody, rhythm, timbre, mood) which are language-agnostic, and MUST NOT penalize or mischaracterize non-English singing.
- What happens when the browser does not support microphone access? The system MUST detect the limitation, show a clear message, and suggest using the file upload path instead.
- What happens when network connectivity is lost mid-analysis? The system MUST not lose the recorded audio and MUST allow the user to retry analysis when connectivity is restored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to record audio directly in the browser using the device microphone with a single tap to start/stop.
- **FR-002**: System MUST accept audio file uploads in MP3, WAV, M4A, and OGG formats, with a maximum file size of 10 MB.
- **FR-003**: System MUST extract and analyze at least four vocal trait dimensions from the audio: melody range, rhythm patterns, emotional mood, and timbre characteristics.
- **FR-004**: System MUST generate a visual vocal profile displaying each analyzed trait in plain-language descriptions accessible to non-musicians.
- **FR-005**: System MUST generate 3–8 personalized song direction recommendations based on the vocal profile, including genre/style, tempo range, vocal difficulty, and mood alignment.
- **FR-006**: Each recommendation MUST include an explanation linking the recommendation to specific traits in the user's vocal profile.
- **FR-007**: System MUST label recommendation confidence honestly — distinguishing high-confidence matches from exploratory suggestions.
- **FR-008**: System MUST process audio locally on the client as much as possible; only derived feature data (not raw audio) should be sent to the server for AI analysis, in accordance with the minimal audio data processing principle.
- **FR-009**: System MUST handle degraded audio quality gracefully — detecting low signal-to-noise ratios and prompting users to re-record rather than producing unreliable results.
- **FR-010**: System MUST detect non-vocal audio (pure instrumental) and inform the user that vocal content is required.
- **FR-011**: System MUST support audio analysis regardless of the language the user sings in, focusing on acoustic properties rather than lyric recognition.
- **FR-012**: System MUST provide a history of past analyses for returning users, displaying dates, vocal profiles, and recommendations for each session.
- **FR-013**: System MUST allow users to compare two past analysis sessions side by side to track vocal development over time.
- **FR-014**: System MUST work across modern browsers (Chrome, Firefox, Safari, Edge) on both desktop and mobile devices.

### Key Entities

- **User**: A person using the system. Key attributes: identifier (anonymous or registered), list of analysis sessions, creation date.
- **Audio Input**: A captured or uploaded audio segment. Key attributes: source type (recording/upload), duration, format, quality assessment score, timestamp.
- **Vocal Profile**: The AI-generated analysis result for one audio input. Key attributes: melody range, rhythm stability score, mood classification, timbre description, expression traits, confidence level per trait.
- **Recommendation**: A song direction suggestion derived from a vocal profile. Key attributes: genre/style label, tempo range, vocal difficulty level, mood alignment, match explanation, confidence level.
- **Analysis Session**: A single end-to-end interaction from audio input to recommendations. Key attributes: timestamp, audio input reference, vocal profile, list of recommendations, user reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 80% of first-time users successfully complete the full flow (record/upload → analysis → view recommendations) without external assistance within 3 minutes.
- **SC-002**: Vocal analysis results are returned within 30 seconds of recording/upload completion for audio segments up to 60 seconds.
- **SC-003**: At least 70% of users rate the recommendation explanations as "understandable" or "very understandable" in post-session feedback.
- **SC-004**: The system correctly detects and rejects non-vocal or low-quality audio in 90%+ of cases, preventing misleading analysis.
- **SC-005**: Users who return for a second session within 30 days report that recommendations feel "relevant" or "very relevant" to their singing ability at a rate of 60%+.
- **SC-006**: The system handles 500 concurrent analysis sessions without degradation in response time beyond the 30-second threshold.
- **SC-007**: No raw audio data is stored on servers after analysis is complete — only derived vocal profile data persists.

## Assumptions

- Users have a modern browser with Web Audio API support and microphone access for the recording flow. Users without microphone access can still use the upload path.
- The initial release targets web browsers only; native mobile apps are out of scope for v1.
- User accounts are optional for a single analysis session but required for history/comparison features (P3). Anonymous sessions use browser local storage.
- The system does not need to identify specific songs ("what song is this?"). It analyzes vocal characteristics and recommends song *directions*, not exact tracks.
- Audio analysis uses AI/ML models hosted on the backend. The specific model architecture is an implementation decision, not a specification concern.
- The recommendation engine maps vocal profiles to song characteristics using a curated trait-to-genre/style knowledge base, not a comprehensive song database. Reference song examples in recommendations are illustrative, not exhaustive.
- Supported languages for the interface are English and Chinese (Simplified) for v1, but vocal analysis itself is language-agnostic.
- The 10 MB upload limit accommodates roughly 5 minutes of compressed audio, which exceeds the useful analysis window.
