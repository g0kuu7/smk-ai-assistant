const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api";

export async function sendMessage(message, history = []) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ message, history }),
      signal: controller.signal,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      return {
        reply:
          data?.reply ||
          "Atsiprašome, šiuo metu nepavyko gauti atsakymo. Pabandykite dar kartą po kelių minučių.",
        links: data?.links || [],
      };
    }

    return {
      reply:
        data?.reply ||
        "Atsiprašome, šiuo metu nepavyko gauti atsakymo. Pabandykite dar kartą po kelių minučių.",
      links: data?.links || [],
    };
  } finally {
    clearTimeout(timeoutId);
  }
}