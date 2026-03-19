"use client";

import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "../../components/AuthProvider";
import { useOperatorContext } from "../../components/useOperatorContext";
import { createPrincipal, fetchPrincipals } from "../../lib/api/client";
import type { Principal, PrincipalRole } from "../../lib/api/types";

export default function UsersPage() {
  const context = useOperatorContext();
  const { principal } = useAuth();
  const [users, setUsers] = useState<Principal[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [principalId, setPrincipalId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState<PrincipalRole>("operator");

  const isAdmin = principal?.role === "admin";

  useEffect(() => {
    if (context.loading || context.error || !isAdmin) {
      return;
    }

    let cancelled = false;
    async function loadUsers() {
      setLoadingUsers(true);
      setUsersError(null);
      try {
        const response = await fetchPrincipals(context.token, context.businessId);
        if (!cancelled) {
          setUsers(response.items);
        }
      } catch (err) {
        if (!cancelled) {
          setUsersError(err instanceof Error ? err.message : "Failed to load users.");
        }
      } finally {
        if (!cancelled) {
          setLoadingUsers(false);
        }
      }
    }

    void loadUsers();
    return () => {
      cancelled = true;
    };
  }, [context.businessId, context.error, context.loading, context.token, isAdmin]);

  const handleCreateUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      await createPrincipal(context.token, context.businessId, {
        principal_id: principalId.trim(),
        display_name: displayName.trim() || undefined,
        role,
      });
      const refreshed = await fetchPrincipals(context.token, context.businessId);
      setUsers(refreshed.items);
      setPrincipalId("");
      setDisplayName("");
      setRole("operator");
      setSubmitSuccess("User record created.");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to create user.");
    } finally {
      setSubmitting(false);
    }
  };

  if (context.loading) {
    return <section className="panel">Loading users...</section>;
  }
  if (context.error) {
    return <section className="panel">Error: {context.error}</section>;
  }
  if (!isAdmin) {
    return (
      <section className="panel stack">
        <h1>Users</h1>
        <p className="hint muted">User administration is available to admin principals only.</p>
      </section>
    );
  }

  return (
    <section className="panel stack">
      <h1>Users</h1>
      <p>
        Business: <code>{context.businessId}</code>
      </p>

      <form onSubmit={(event) => void handleCreateUser(event)} className="stack">
        <h2>Create User</h2>
        <label htmlFor="principal-id">User ID</label>
        <input
          id="principal-id"
          value={principalId}
          onChange={(event) => setPrincipalId(event.target.value)}
          placeholder="user@example.com"
          required
        />

        <label htmlFor="display-name">Display Name (optional)</label>
        <input
          id="display-name"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Operator Name"
        />

        <label htmlFor="user-role">Role</label>
        <select id="user-role" value={role} onChange={(event) => setRole(event.target.value as PrincipalRole)}>
          <option value="operator">operator</option>
          <option value="admin">admin</option>
        </select>

        <button className="primary" type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create User"}
        </button>
      </form>

      {submitSuccess ? <p className="hint">{submitSuccess}</p> : null}
      {submitError ? <p className="hint error">{submitError}</p> : null}
      {loadingUsers ? <p className="hint muted">Loading users...</p> : null}
      {usersError ? <p className="hint error">{usersError}</p> : null}

      <table className="table">
        <thead>
          <tr>
            <th>User ID</th>
            <th>Display Name</th>
            <th>Role</th>
            <th>Active</th>
            <th>Last Auth</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.display_name}</td>
              <td>{user.role}</td>
              <td>{user.is_active ? "yes" : "no"}</td>
              <td>{user.last_authenticated_at || "never"}</td>
            </tr>
          ))}
          {!loadingUsers && users.length === 0 ? (
            <tr>
              <td colSpan={5}>No users found for this business.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}
