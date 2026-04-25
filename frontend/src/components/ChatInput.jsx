import { useState } from "react";

function ChatInput({ onSend, isLoading }) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const trimmedMessage = message.trim();
    if (!trimmedMessage || isLoading) return;

    onSend(trimmedMessage);
    setMessage("");
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        className="chat-input__field"
        placeholder="Parašyk klausimą apie SMK..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isLoading}
        maxLength={500}
      />

      <button
        className="chat-input__button"
        type="submit"
        disabled={isLoading || !message.trim()}
      >
        {isLoading ? "..." : "Siųsti"}
      </button>
    </form>
  );
}

export default ChatInput;
