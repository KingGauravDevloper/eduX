'use client';

import { useState } from 'react';

export default function HomePage() {
  // Form input states
  const [prompt, setPrompt] = useState('');
  const [days, setDays] = useState(7);
  const [minutes, setMinutes] = useState(15);

  // State to handle loading and results
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
        headers: {
          'Content-Type': 'application/json',
        },
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
      console.error("There was an error processing your request:", e);
      setError("Failed to generate course. Please check if the backend server is running and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-white p-8">
      <div className="w-full max-w-2xl text-center">
        <h1 className="text-5xl font-bold">
          eduX Course Generator
        </h1>
        <p className="mt-4 text-lg text-gray-400">
          Enter your learning goal below to get started.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., I want to learn Python for data science in 1 week"
            className="w-full h-32 p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            required
          />
          <div className="flex gap-4">
            <input
              type="number"
              value={days}
              onChange={(e) => setDays(e.target.value)}
              className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Number of days"
              required
            />
            <input
              type="number"
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
              className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Minutes per day"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full p-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Generating... Please wait...' : 'Generate Course'}
          </button>
        </form>

        {error && (
          <div className="mt-8 p-4 bg-red-900 border border-red-700 rounded-lg">
            <p className="font-bold text-red-300">An Error Occurred</p>
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-8 p-4 w-full bg-gray-800 border border-gray-700 rounded-lg text-left">
            <h2 className="text-2xl font-bold mb-4">Generation Complete!</h2>
            <pre className="whitespace-pre-wrap text-sm text-gray-300">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </main>
  );
}