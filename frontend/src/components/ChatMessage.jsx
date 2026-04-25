function ChatMessage({ sender, text, links = [] }) {
  const isAssistant = sender === "assistant";

  return (
    <div className={`message message--${sender}`}>
      {isAssistant && <div className="message__avatar">AI</div>}

      <div className="message__bubble">
        <div className="message__sender">{isAssistant ? "SMK AI" : "Tu"}</div>
        <div className="message__text">{text}</div>

        {isAssistant && links.length > 0 && (
          <div className="message__links-wrapper">
            <div className="message__links-title">Naudingos nuorodos</div>

            <div className="message__links">
              {links.map((link, index) => (
                <a
                  key={`${link.url}-${index}`}
                  href={link.url}
                  target="_blank"
                  rel="noreferrer"
                  className="message__link-button"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
