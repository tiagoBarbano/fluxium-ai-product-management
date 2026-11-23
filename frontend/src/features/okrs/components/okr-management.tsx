"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useI18n } from "@/components/i18n-provider";
import { getSession } from "@/features/auth/services/auth-service";
import {
  listProducts,
  type Product,
} from "@/features/products/services/product-service";
import {
  createObjective,
  listObjectives,
  updateObjective,
  type Objective,
} from "@/features/okrs/services/okr-service";

type KeyResultForm = {
  id?: string;
  metric: string;
  target: string;
  due_date: string;
  current_value: string;
  unit: string;
};
type ObjectiveForm = {
  title: string;
  description: string;
  product_id: string;
  key_results: KeyResultForm[];
};

type ModalState = { mode: "create" | "edit"; objective?: Objective } | null;

const emptyKeyResult = (): KeyResultForm => ({
  metric: "",
  target: "",
  due_date: "",
  current_value: "",
  unit: "",
});
const emptyForm = (): ObjectiveForm => ({
  title: "",
  description: "",
  product_id: "",
  key_results: [emptyKeyResult()],
});

function formFromObjective(objective: Objective): ObjectiveForm {
  return {
    title: objective.title,
    description: objective.description,
    product_id: objective.product_id ?? "",
    key_results: objective.key_results.map((result) => ({
      id: result.id,
      metric: result.metric,
      target: String(result.target),
      due_date: result.due_date,
      current_value:
        result.current_value === null ? "" : String(result.current_value),
      unit: result.unit ?? "",
    })),
  };
}

function toKeyResultInput(result: KeyResultForm, includeId = false) {
  return {
    ...(includeId && result.id ? { id: result.id } : {}),
    metric: result.metric,
    target: result.target,
    due_date: result.due_date,
    ...(result.current_value.trim()
      ? { current_value: result.current_value }
      : {}),
    ...(result.unit.trim() ? { unit: result.unit } : {}),
  };
}

export function OkrManagement() {
  const { t } = useI18n();
  const session = getSession();
  const workspaceId = session?.workspaceIds[0] ?? "";
  const [objectives, setObjectives] = useState<Objective[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [form, setForm] = useState<ObjectiveForm>(emptyForm);
  const [modal, setModal] = useState<ModalState>(null);
  const [loading, setLoading] = useState(Boolean(workspaceId));
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!workspaceId) return;
    const [objectiveResult, productResult] = await Promise.all([
      listObjectives(workspaceId),
      listProducts(workspaceId),
    ]);
    setObjectives(objectiveResult);
    setProducts(productResult.items);
  }, [workspaceId]);

  useEffect(() => {
    if (!workspaceId) return;
    Promise.resolve()
      .then(refresh)
      .catch((error: unknown) =>
        setMessage(error instanceof Error ? error.message : t("okr.loadError")),
      )
      .finally(() => setLoading(false));
  }, [refresh, t, workspaceId]);

  function openCreate() {
    setMessage(null);
    setForm(emptyForm());
    setModal({ mode: "create" });
  }

  function openEdit(objective: Objective) {
    setMessage(null);
    setForm(formFromObjective(objective));
    setModal({ mode: "edit", objective });
  }

  function updateKeyResult(index: number, changes: Partial<KeyResultForm>) {
    setForm((current) => ({
      ...current,
      key_results: current.key_results.map((result, resultIndex) =>
        resultIndex === index ? { ...result, ...changes } : result,
      ),
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!workspaceId || !form.product_id) {
      setMessage(t("okr.contextRequired"));
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      if (modal?.mode === "edit" && modal.objective) {
        await updateObjective(modal.objective.id, {
          title: form.title,
          description: form.description,
          key_results: form.key_results.map((result) =>
            toKeyResultInput(result, true),
          ),
        });
      } else {
        await createObjective(workspaceId, {
          title: form.title,
          description: form.description,
          key_results: form.key_results.map((result) =>
            toKeyResultInput(result),
          ),
          product_id: form.product_id,
        });
      }
      await refresh();
      setModal(null);
      setMessage(t(modal?.mode === "edit" ? "okr.updated" : "okr.created"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("okr.saveError"));
    } finally {
      setSaving(false);
    }
  }

  if (!session)
    return (
      <section className="empty-state">
        <h1>{t("okr.title")}</h1>
        <p>{t("okr.signIn")}</p>
      </section>
    );
  if (loading)
    return (
      <section className="empty-state">
        <p>{t("okr.loading")}</p>
      </section>
    );
  if (!workspaceId)
    return (
      <section className="empty-state">
        <p>{t("okr.noWorkspace")}</p>
      </section>
    );

  return (
    <div className="stack-lg workspace-page">
      <section className="dashboard-intro">
        <div>
          <span className="eyebrow">{t("okr.eyebrow")}</span>
          <h1>{t("okr.title")}</h1>
          <p>{t("okr.description")}</p>
        </div>
        <button className="primary-button" type="button" onClick={openCreate}>
          {t("okr.newObjective")}
        </button>
      </section>
      {message && (
        <div className="notice-box" role="status">
          {message}
        </div>
      )}
      <section className="creation-panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">{t("okr.objectivesEyebrow")}</span>
            <h2>{t("okr.objectivesTitle")}</h2>
          </div>
          <strong>{objectives.length}</strong>
        </div>
        {objectives.length === 0 ? (
          <p className="empty-state compact-empty">{t("okr.empty")}</p>
        ) : (
          <div className="context-record-list okr-table">
            {objectives.map((objective) => (
              <article className="context-record okr-record" key={objective.id}>
                <div className="okr-summary">
                  <strong>{objective.title}</strong>
                  <span>{objective.description}</span>
                  <small>
                    {objective.key_results.length} {t("okr.keyResults")} ·{" "}
                    {t("okr.productContext")}
                  </small>
                </div>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => openEdit(objective)}
                >
                  {t("okr.edit")}
                </button>
                <div className="okr-key-results">
                  {objective.key_results.map((result) => (
                    <div key={result.id}>
                      <span>{result.metric}</span>
                      <strong>
                        {result.target}
                        {result.unit ? ` ${result.unit}` : ""}
                      </strong>
                      <small>
                        {t("okr.until")} {result.due_date}
                      </small>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
      {modal && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => setModal(null)}
        >
          <section
            className="assessment-modal context-create-modal"
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="modal-header">
              <div>
                <span className="eyebrow">{t("okr.modalEyebrow")}</span>
                <h2>
                  {modal.mode === "edit"
                    ? t("okr.editObjective")
                    : t("okr.newObjective")}
                </h2>
              </div>
              <button
                className="modal-close"
                type="button"
                aria-label={t("workspace.closeModal")}
                onClick={() => setModal(null)}
              >
                ×
              </button>
            </header>
            <form
              className="creation-form context-modal-form"
              onSubmit={submit}
            >
              <label>
                {t("okr.objectiveTitle")}
                <input
                  required
                  value={form.title}
                  onChange={(event) =>
                    setForm({ ...form, title: event.target.value })
                  }
                />
              </label>
              <label>
                {t("okr.objectiveDescription")}
                <textarea
                  required
                  rows={3}
                  value={form.description}
                  onChange={(event) =>
                    setForm({ ...form, description: event.target.value })
                  }
                />
              </label>
              {modal.mode === "create" && (
                <label>
                  {t("okr.productContext")}
                  <select
                    required
                    value={form.product_id}
                    onChange={(event) =>
                      setForm({ ...form, product_id: event.target.value })
                    }
                  >
                    <option value="">{t("okr.selectProduct")}</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <div className="okr-form-section">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">
                      {t("okr.keyResultsEyebrow")}
                    </span>
                    <h3>{t("okr.keyResultsTitle")}</h3>
                  </div>
                  <button
                    className="secondary-button compact"
                    type="button"
                    onClick={() =>
                      setForm({
                        ...form,
                        key_results: [...form.key_results, emptyKeyResult()],
                      })
                    }
                  >
                    {t("okr.addKeyResult")}
                  </button>
                </div>
                {form.key_results.map((result, index) => (
                  <div className="okr-form-row" key={result.id ?? index}>
                    <label>
                      {t("okr.metric")}
                      <input
                        required
                        value={result.metric}
                        onChange={(event) =>
                          updateKeyResult(index, { metric: event.target.value })
                        }
                      />
                    </label>
                    <label>
                      {t("okr.target")}
                      <input
                        required
                        type="number"
                        step="any"
                        value={result.target}
                        onChange={(event) =>
                          updateKeyResult(index, { target: event.target.value })
                        }
                      />
                    </label>
                    <label>
                      {t("okr.dueDate")}
                      <input
                        required
                        type="date"
                        value={result.due_date}
                        onChange={(event) =>
                          updateKeyResult(index, {
                            due_date: event.target.value,
                          })
                        }
                      />
                    </label>
                    <label>
                      {t("okr.unit")}
                      <input
                        value={result.unit}
                        onChange={(event) =>
                          updateKeyResult(index, { unit: event.target.value })
                        }
                      />
                    </label>
                    {form.key_results.length > 1 && (
                      <button
                        className="text-link"
                        type="button"
                        onClick={() =>
                          setForm({
                            ...form,
                            key_results: form.key_results.filter(
                              (_, resultIndex) => resultIndex !== index,
                            ),
                          })
                        }
                      >
                        {t("okr.removeKeyResult")}
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                className="primary-button"
                disabled={saving}
                type="submit"
              >
                {saving ? t("workspace.saving") : t("okr.save")}
              </button>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
