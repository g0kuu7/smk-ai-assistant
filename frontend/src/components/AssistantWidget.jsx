import { useEffect, useRef, useState } from "react";
import ChatWindow from "./ChatWindow";

function AssistantWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [clearTrigger, setClearTrigger] = useState(0);

  const panelRef = useRef(null);
  const buttonRef = useRef(null);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const handleClearChat = () => {
    setClearTrigger((prev) => prev + 1);
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event) => {
      const clickedInsidePanel = panelRef.current?.contains(event.target);
      const clickedButton = buttonRef.current?.contains(event.target);

      if (!clickedInsidePanel && !clickedButton) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  return (
    <div className="assistant-widget">
      <div
        className="assistant-widget__panel"
        ref={panelRef}
        style={{ display: isOpen ? "flex" : "none" }}
      >
        <div className="assistant-widget__header">
          <div className="assistant-widget__brand">
            <div className="assistant-widget__logo">SMK</div>

            <div>
              <div className="assistant-widget__title-row">
                <h2 className="assistant-widget__title">SMK AI asistentas</h2>
                <span className="assistant-widget__status">
                  <span></span>
                  Online
                </span>
              </div>

              <p className="assistant-widget__subtitle">
                Virtuali pagalba apie studijas, stojimą ir studentų sistemas
              </p>
            </div>
          </div>

          <div className="assistant-widget__actions">
            <button type="button" onClick={handleClearChat}>
              Išvalyti
            </button>
            <button type="button" onClick={handleToggle}>
              Uždaryti
            </button>
          </div>
        </div>

        <ChatWindow clearTrigger={clearTrigger} />
      </div>

      <button
        ref={buttonRef}
        type="button"
        className={`assistant-widget__floating-button ${isOpen ? "is-open" : ""}`}
        onClick={handleToggle}
        aria-label={isOpen ? "Uždaryti AI asistentą" : "Atidaryti AI asistentą"}
      >
        {isOpen ? (
          <span className="assistant-widget__close-icon">×</span>
        ) : (
          <>
            <span className="assistant-widget__spark">✦</span>
            <span>AI</span>
          </>
        )}
      </button>
    </div>
  );
}

export default AssistantWidget;