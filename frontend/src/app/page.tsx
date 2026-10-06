"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState<string>("Connecting to backend...");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/health`)
      .then((res) => {
        if (!res.ok) throw new Error("Backend response not ok");
        return res.json();
      })
      .then((data) => {
        setStatus(data.message || "backend connected");
      })
      .catch(() => {
        setStatus("Failed to connect to backend");
      });
  }, []);

  return (
    <main className="min-h-screen flex items-center justify-center bg-black text-white font-sans p-4">
      <p className="text-xl font-medium tracking-tight">
        {status}
      </p>
    </main>
  );
}
