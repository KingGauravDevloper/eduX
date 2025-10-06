'use client';

import { useState } from 'react';

export default function HomePage() {
  const [prompt, setPrompt] = useState('Learn the basics of React in 1 day');
  const [days, setDays] = useState(1);
  const [minutes, setMinutes] = useState(15);

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/generate-full-course', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          days: parseInt(days),
          daily_commitment_minutes: parseInt(minutes),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);

    } catch (e) {
      console.error("There was an error:", e);
      setError("Failed to generate course. Please check if the backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };
  
  // Helper to get the first day's data from the result
  const firstDay = result?.course_outline?.[0];

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-white p-8">
      <div className="w-full max-w-2xl text-center">
        <h1 className="text-5xl font-bold">eduX Course Generator</h1>
        <p className="mt-4 text-lg text-gray-400">
          Enter your learning goal below to get started.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
          {/* ... (The form is the same as before) ... */}
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., I want to learn Python for data science"
            className="w-full h-32 p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            required
          />
          <div className="flex gap-4">
            <input type="number" value={days} onChange={(e) => setDays(e.target.value)} className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required />
            <input type="number" value={minutes} onChange={(e) => setMinutes(e.target.value)} className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required />
          </div>
          <button type="submit" disabled={isLoading} className="w-full p-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed">
            {isLoading ? 'Generating... Please wait...' : 'Generate Course'}
          </button>
        </form>

        {error && (
          <div className="mt-8 p-4 bg-red-900 border border-red-700 rounded-lg">
            <p className="font-bold text-red-300">An Error Occurred</p>
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* --- NEW RESULTS DISPLAY --- */}
        {firstDay && (
          <div className="mt-8 p-4 w-full bg-gray-800 border border-gray-700 rounded-lg text-left">
            <h2 className="text-2xl font-bold mb-4">{firstDay.title}</h2>
            <p className="mb-4 text-gray-400">{firstDay.description}</p>
            
            {firstDay.video_file_path ? (
              <video 
                // Construct the full URL to the video file
                src={`http://127.0.0.1:8000/videos/${firstDay.video_file_path.split('\\').pop()}`}
                controls 
                className="w-full rounded-lg"
              >
                Your browser does not support the video tag.
              </video>
            ) : (
              <p className="text-yellow-400">Video is not available for this lesson.</p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}