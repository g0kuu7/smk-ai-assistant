import { useEffect, useRef, useState } from "react";
import { sendMessage } from "../services/api";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";

const STORAGE_KEY = "smk-ai-chat-history";

const initialAssistantMessage = {
  sender: "assistant",
  text: "Sveikas! Esu SMK virtualus asistentas. Galiu padėti rasti informaciją apie studijų programas, kainas, stojimą, kontaktus, Moodle ar Classter.",
  links: [],
};

const serviceUnavailableMessage =
  "Atsiprašome, šiuo metu nepavyko gauti atsakymo. Pabandykite dar kartą po kelių minučių arba pasinaudokite SMK svetainėje pateikta informacija.";

const starterQuestions = [
  "Kur yra SMK Vilniuje?",
  "Kiek kainuoja Programavimas ir multimedija?",
  "Ar SMK turi trumpųjų studijų?",
  "Kur prisijungti prie Moodle?",
];

const getSavedMessages = () => {
  try {
    const savedMessages = localStorage.getItem(STORAGE_KEY);

    if (!savedMessages) {
      return [initialAssistantMessage];
    }

    const parsedMessages = JSON.parse(savedMessages);

    if (!Array.isArray(parsedMessages) || parsedMessages.length === 0) {
      return [initialAssistantMessage];
    }

    return parsedMessages;
  } catch {
    return [initialAssistantMessage];
  }
};

function ChatWindow({ clearTrigger }) {
  const [messages, setMessages] = useState(getSavedMessages);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const lastAssistantMessageRef = useRef(null);
  const hasMountedRef = useRef(false);

  const hasStartedConversation = messages.some((message) => message.sender === "user");

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (!hasMountedRef.current) {
      hasMountedRef.current = true;
      return;
    }

    const freshMessages = [initialAssistantMessage];
    setMessages(freshMessages);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(freshMessages));
  }, [clearTrigger]);

  useEffect(() => {
    const scrollTimeout = setTimeout(() => {
      const lastMessage = messages[messages.length - 1];

      if (lastMessage?.sender === "assistant" && hasStartedConversation) {
        lastAssistantMessageRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
        return;
      }

      messagesEndRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }, 90);

    return () => clearTimeout(scrollTimeout);
  }, [messages, isLoading, hasStartedConversation]);

  const buildHistory = () => {
    return messages.slice(-8).map((msg) => ({
      role: msg.sender,
      text: msg.text,
    }));
  };

  const handleSendMessage = async (message) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isLoading) return;

    const history = buildHistory();

    setMessages((prev) => [
      ...prev,
      { sender: "user", text: trimmedMessage, links: [] },
    ]);

    setIsLoading(true);

    try {
      const data = await sendMessage(trimmedMessage, history);

      const delay = 350 + Math.random() * 350;
      await new Promise((resolve) => setTimeout(resolve, delay));

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: data.reply || serviceUnavailableMessage,
          links: data.links || [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: serviceUnavailableMessage,
          links: [
            {
              label: "SMK svetainė",
              url: "https://smk.lt/",
            },
            {
              label: "Kontaktai",
              url: "https://smk.lt/kontaktai/",
            },
          ],
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const lastAssistantIndex = messages.reduce((lastIndex, message, index) => {
    return message.sender === "assistant" ? index : lastIndex;
  }, -1);

  return (
    <section className="chat-window">
      {!hasStartedConversation && (
        <div className="chat-window__quick-start">
          <div className="chat-window__top">
            <div>
              <p className="chat-window__eyebrow">Dažniausi klausimai</p>
              <h3 className="chat-window__heading">Kuo galiu padėti?</h3>
            </div>
          </div>

          <div className="chat-window__starters">
            <div className="chat-window__starter-list">
              {starterQuestions.map((question) => (
                <button
                  key={question}
                  type="button"
                  className="chat-window__starter-button"
                  onClick={() => handleSendMessage(question)}
                  disabled={isLoading}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="chat-window__messages">
        {messages.map((message, index) => {
          const isLastAssistantMessage =
            hasStartedConversation &&
            message.sender === "assistant" &&
            index === lastAssistantIndex;

          return (
            <div
              key={`${message.sender}-${index}`}
              className="chat-window__message-anchor"
              ref={isLastAssistantMessage ? lastAssistantMessageRef : null}
            >
              <ChatMessage
                sender={message.sender}
                text={message.text}
                links={message.links}
              />
            </div>
          );
        })}

        {isLoading && (
          <div className="message message--assistant">
            <div className="message__avatar">AI</div>

            <div className="message__bubble message__bubble--loading">
              <div className="message__sender">SMK AI</div>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef}></div>
      </div>

      <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
    </section>
  );
}

export default ChatWindow;