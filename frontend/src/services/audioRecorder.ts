/**
 * Audio recording service: wraps the MediaRecorder API.
 * Provides one-click recording functionality, decoding the recorded audio into an AudioBuffer for feature extraction.
 */

/**
 * Request microphone permission and record audio.
 * After recording ends, returns an AudioBuffer for feature analysis and the raw Blob.
 *
 * @returns A controller object; call stop() to end recording and get the result
 *
 * @example
 *   const recorder = await startRecording()
 *   // ... user sings ...
 *   const { audioBuffer, blob } = await recorder.stop()
 */
export async function startRecording(): Promise<{
  stop: () => Promise<{ audioBuffer: AudioBuffer; blob: Blob }>
  isRecording: () => boolean
}> {
  // Check browser support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error(
      'Your browser does not support microphone access. Please use the file upload option instead.',
    )
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const mediaRecorder = new MediaRecorder(stream)
  const chunks: Blob[] = []

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data)
  }

  mediaRecorder.start()

  return {
    isRecording: () => mediaRecorder.state === 'recording',

    stop: () =>
      new Promise((resolve, reject) => {
        mediaRecorder.onstop = async () => {
          // Stop microphone stream
          stream.getTracks().forEach((track) => track.stop())

          const blob = new Blob(chunks, { type: 'audio/webm' })
          try {
            const arrayBuffer = await blob.arrayBuffer()
            const audioContext = new AudioContext()
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
            await audioContext.close()
            resolve({ audioBuffer, blob })
          } catch (err) {
            reject(new Error('Failed to process the recording. Please try again.'))
          }
        }

        mediaRecorder.onerror = () => {
          stream.getTracks().forEach((track) => track.stop())
          reject(new Error('Recording failed. Please check your microphone.'))
        }

        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
        }
      }),
  }
}
