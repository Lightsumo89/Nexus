
import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";

function Frame({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="auth">
      <Link to="/" className="back">
        ‹ Back
      </Link>
      <h1>{title}</h1>
      {children}
    </div>
  );
}

export function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [adult, setAdult] = useState(false);
  const [acceptedAgreement, setAcceptedAgreement] = useState(false);
  const [registrationToken, setRegistrationToken] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [devCode, setDevCode] = useState("");
  const [stage, setStage] = useState<"signup" | "verify">("signup");
  const [notice, setNotice] = useState("");
  const nav = useNavigate();
  const qc = useQueryClient();

  const signup = useMutation({
    mutationFn: () =>
      api<{
        registration_token: string;
        dev_code?: string;
      }>("/auth/signup", {
        body: {
          email,
          password,
          password_confirmation: passwordConfirmation,
          is_adult: adult,
          accepted_agreement: acceptedAgreement,
        },
      }),
    onSuccess: (data) => {
      setRegistrationToken(data.registration_token);
      setDevCode(data.dev_code ?? "");
      setVerificationCode("");
      setNotice("");
      setStage("verify");
    },
  });

  const verify = useMutation({
    mutationFn: () =>
      api("/auth/verify", {
        body: {
          registration_token: registrationToken,
          code: verificationCode,
        },
      }),
    onSuccess: async () => {
      sessionStorage.removeItem("pickup.devVerify");
      await qc.invalidateQueries({ queryKey: ["me"] });
      nav("/onboarding");
    },
  });

  const resend = useMutation({
    mutationFn: () =>
      api<{
        dev_code?: string;
      }>("/auth/resend", {
        body: {
          registration_token: registrationToken,
        },
      }),
    onSuccess: (data) => {
      setDevCode(data.dev_code ?? "");
      setVerificationCode("");
      setNotice("A new verification code has been requested.");
      resend.reset();
    },
  });

  const submitSignup = (e: FormEvent) => {
    e.preventDefault();
    setNotice("");
    signup.mutate();
  };

  const submitVerification = (e: FormEvent) => {
    e.preventDefault();
    verify.mutate();
  };

  if (stage === "verify") {
    return (
      <Frame title="Verify your email">
        <form className="stack" onSubmit={submitVerification}>
          <p>
            Enter the six-digit verification code sent to{" "}
            <strong>{email}</strong>.
          </p>

          <label>
            Verification code
            <input
              type="text"
              value={verificationCode}
              onChange={(e) =>
                setVerificationCode(
                  e.target.value.replace(/\D/g, "").slice(0, 6)
                )
              }
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              minLength={6}
              maxLength={6}
              placeholder="123456"
              required
            />
          </label>

          {devCode && (
            <p className="muted">
              Development code: <strong>{devCode}</strong>
            </p>
          )}

          {notice && <p className="ok">{notice}</p>}
          {verify.error && (
            <p className="error">{verify.error.message}</p>
          )}
          {resend.error && (
            <p className="error">{resend.error.message}</p>
          )}

          <button
            type="submit"
            disabled={verify.isPending || verificationCode.length !== 6}
          >
            {verify.isPending ? "Verifying…" : "Verify email"}
          </button>

          <button
            type="button"
            disabled={resend.isPending}
            onClick={() => {
              setNotice("");
              resend.mutate();
            }}
          >
            {resend.isPending ? "Requesting code…" : "Resend code"}
          </button>

          <p className="muted">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </form>
      </Frame>
    );
  }

  return (
    <Frame title="Create your account">
      <form className="stack" onSubmit={submitSignup}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={10}
            autoComplete="new-password"
            required
          />
          <small className="muted">At least 10 characters.</small>
        </label>

        <label>
          Confirm password
          <input
            type="password"
            value={passwordConfirmation}
            onChange={(e) => setPasswordConfirmation(e.target.value)}
            minLength={10}
            autoComplete="new-password"
            required
          />
        </label>

        <label className="check">
          <input
            type="checkbox"
            checked={adult}
            onChange={(e) => setAdult(e.target.checked)}
            required
          />
          I confirm that I am 18 or older.
        </label>

        <label className="check">
          <input
            type="checkbox"
            checked={acceptedAgreement}
            onChange={(e) => setAcceptedAgreement(e.target.checked)}
            required
          />
          I agree to the applicable terms and policies.
        </label>

        {passwordConfirmation &&
          password !== passwordConfirmation && (
            <p className="error">Passwords do not match.</p>
          )}

        {signup.error && (
          <p className="error">{signup.error.message}</p>
        )}

        <button
          type="submit"
          disabled={
            signup.isPending ||
            password !== passwordConfirmation ||
            !adult ||
            !acceptedAgreement
          }
        >
          {signup.isPending ? "Creating account…" : "Continue"}
        </button>

        <p className="muted">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </Frame>
  );
}

export function Login() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useMutation({
    mutationFn: () => api("/auth/login", { body: { email, password } }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
      nav("/explore");
    },
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate();
  };

  return (
    <Frame title="Log in">
      <form className="stack" onSubmit={submit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        {login.error && <p className="error">{login.error.message}</p>}

        <button disabled={login.isPending}>
          {login.isPending ? "Logging in…" : "Log in"}
        </button>

        <p className="muted">
          <Link to="/forgot">Forgot password?</Link> ·{" "}
          <Link to="/signup">Create account</Link>
        </p>
      </form>
    </Frame>
  );
}

export function Verify() {
  return (
    <Frame title="Email verification">
      <p>
        To verify your email, return to the signup process and enter the
        verification code you received.
      </p>
      <Link className="button" to="/signup">
        Return to signup
      </Link>
    </Frame>
  );
}

export function Forgot() {
  const [email, setEmail] = useState("");
  const send = useMutation({
    mutationFn: () => api("/auth/forgot", { body: { email } }),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    send.mutate();
  };

  return (
    <Frame title="Reset your password">
      <form className="stack" onSubmit={submit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>

        {send.isSuccess && (
          <p className="ok">
            If that email has an account, a reset link is on its way.
          </p>
        )}

        {send.error && <p className="error">{send.error.message}</p>}

        <button disabled={send.isPending}>
          {send.isPending ? "Sending…" : "Send reset link"}
        </button>
      </form>
    </Frame>
  );
}

export function Reset() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const reset = useMutation({
    mutationFn: () =>
      api("/auth/reset", {
        body: {
          token: params.get("token") ?? "",
          password,
        },
      }),
    onSuccess: () => nav("/login"),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    reset.mutate();
  };

  return (
    <Frame title="Choose a new password">
      <form className="stack" onSubmit={submit}>
        <label>
          New password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={10}
            autoComplete="new-password"
            required
          />
        </label>

        <label>
          Confirm new password
          <input
            type="password"
            value={passwordConfirmation}
            onChange={(e) => setPasswordConfirmation(e.target.value)}
            minLength={10}
            autoComplete="new-password"
            required
          />
        </label>

        {passwordConfirmation && password !== passwordConfirmation && (
          <p className="error">Passwords do not match.</p>
        )}

        {reset.error && <p className="error">{reset.error.message}</p>}

        <button
          disabled={
            reset.isPending ||
            password !== passwordConfirmation ||
            password.length < 10
          }
        >
          {reset.isPending ? "Saving…" : "Save password"}
        </button>
      </form>
    </Frame>
  );
}