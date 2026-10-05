import { useState, type FormEvent } from "react";

import { useAuth } from "../auth/AuthContext";
import { navigate } from "../routes";

type AuthPageProps = {
  mode: "login" | "register";
  authError: string | null;
};

function AuthPage({ mode, authError }: AuthPageProps) {
  const { login, register, busy } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState(authError ?? "");
  const [success, setSuccess] = useState("");
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (isRegister && password !== confirmation) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Use a password with at least 8 characters.");
      return;
    }

    try {
      if (isRegister) {
        await register(email.trim(), password);
        setSuccess("Account created. Opening your private workspace...");
        window.setTimeout(() => navigate("/"), 450);
      } else {
        await login(email.trim(), password);
        navigate("/");
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Authentication could not be completed.");
    }
  }

  return (
    <main className="auth-page">
      <header className="auth-topbar">
        <a className="brand-mark auth-brand" href="/" onClick={(event) => { event.preventDefault(); navigate("/"); }}>
          <span className="brand-glyph">N</span>
          <span>NEXUS</span>
        </a>
        <a className="auth-back-link" href="/" onClick={(event) => { event.preventDefault(); navigate("/"); }}>
          ← Back to search
        </a>
      </header>

      <div className="auth-layout">
        <section className="auth-intro">
          <span className="hero-kicker"><span className="signal-line" /> PRIVATE INTELLIGENCE</span>
          <h1>{isRegister ? "Start with a private space." : "Return to your research."}</h1>
          <p>
            {isRegister
              ? "Create an account to keep your local research and private vault scoped to you."
              : "Sign in to continue with your private vault, saved evidence, and grounded research."}
          </p>
          <div className="auth-assurance">
            <span className="assurance-mark" aria-hidden="true">⌑</span>
            <span>Private workspace · local-first intelligence</span>
          </div>
        </section>

        <section className="auth-panel" aria-labelledby="auth-heading">
          <div className="auth-panel-heading">
            <span className="section-kicker">{isRegister ? "NEW ACCOUNT" : "ACCOUNT ACCESS"}</span>
            <h2 id="auth-heading">{isRegister ? "Create account" : "Sign in"}</h2>
            <p>{isRegister ? "Your private space starts here." : "Your workspace is ready when you are."}</p>
          </div>

          <form className="auth-form" onSubmit={(event) => void handleSubmit(event)}>
            <label htmlFor="auth-email">Email</label>
            <input
              autoComplete="email"
              id="auth-email"
              maxLength={254}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
              type="email"
              value={email}
            />

            <label htmlFor="auth-password">Password</label>
            <input
              autoComplete={isRegister ? "new-password" : "current-password"}
              id="auth-password"
              maxLength={256}
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />

            {isRegister && (
              <>
                <label htmlFor="auth-confirm-password">Confirm password</label>
                <input
                  autoComplete="new-password"
                  id="auth-confirm-password"
                  maxLength={256}
                  minLength={8}
                  onChange={(event) => setConfirmation(event.target.value)}
                  required
                  type="password"
                  value={confirmation}
                />
              </>
            )}

            {error && <div className="auth-feedback error" role="alert">{error}</div>}
            {success && <div className="auth-feedback success" role="status">{success}</div>}
            <button className="action-button primary auth-submit" disabled={busy} type="submit">
              {busy ? (isRegister ? "Creating account..." : "Signing in...") : (isRegister ? "Create account" : "Sign in")}
              {!busy && <span aria-hidden="true">→</span>}
            </button>
          </form>

          <p className="auth-switch">
            {isRegister ? "Already have an account?" : "New to NEXUS?"}{" "}
            <a
              href={isRegister ? "/login" : "/register"}
              onClick={(event) => {
                event.preventDefault();
                navigate(isRegister ? "/login" : "/register");
              }}
            >
              {isRegister ? "Sign in" : "Create an account"}
            </a>
          </p>
        </section>
      </div>
      <footer className="auth-footer">NEXUS · Private by design</footer>
    </main>
  );
}

export default AuthPage;