"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { getSession } from "@/features/auth/services/auth-service";
import {
  createProduct,
  listProducts,
  type Product,
} from "@/features/products/services/product-service";
import {
  createOpportunity,
  listOpportunities,
  updateOpportunity,
  type Opportunity,
} from "@/features/opportunities/services/opportunity-service";
import {
  createInitiative,
  listInitiatives,
  type Initiative,
} from "@/features/initiatives/services/initiative-service";
import { listObjectives, type Objective } from "@/features/okrs/services/okr-service";
import { useI18n } from "@/components/i18n-provider";

type FormState = { name: string; description: string; vision: string };
type OpportunityFormState = { title: string; description: string; objective_ids: string[] };
type InitiativeFormState = {
  title: string;
  objective: string;
  scope: string;
  out_of_scope: string;
  objective_ids: string[];
};
type CreationTab = "product" | "opportunity" | "initiative";
type CreationModal = CreationTab | null;

const emptyProduct: FormState = { name: "", description: "", vision: "" };
const emptyOpportunity: OpportunityFormState = { title: "", description: "", objective_ids: [] };
const emptyInitiative: InitiativeFormState = {
  title: "",
  objective: "",
  scope: "",
  out_of_scope: "",
  objective_ids: [],
};

export function WorkspaceContext({ section }: { section?: CreationTab }) {
  const { t } = useI18n();
  const [products, setProducts] = useState<Product[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [initiatives, setInitiatives] = useState<Initiative[]>([]);
  const [objectives, setObjectives] = useState<Objective[]>([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [selectedOpportunityId, setSelectedOpportunityId] = useState("");
  const [productForm, setProductForm] = useState(emptyProduct);
  const [opportunityForm, setOpportunityForm] = useState(emptyOpportunity);
  const [initiativeForm, setInitiativeForm] = useState(emptyInitiative);
  const [activeTab, setActiveTab] = useState<CreationTab>("product");
  const [loading, setLoading] = useState(() =>
    Boolean(getSession()?.workspaceIds[0]),
  );
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [creationModal, setCreationModal] = useState<CreationModal>(null);
  const [editingOpportunityId, setEditingOpportunityId] = useState<string | null>(null);

  const session = getSession();
  const workspaceId = session?.workspaceIds[0] ?? "";
  const visibleSection = section ?? activeTab;

  const refreshContext = useCallback(
    async (productId = "") => {
      if (!workspaceId) return;
      const [productResult, opportunityResult, objectiveResult] = await Promise.all([
        listProducts(workspaceId),
        listOpportunities(workspaceId),
        listObjectives(workspaceId),
      ]);
      setProducts(productResult.items);
      const nextProductId = productId || productResult.items[0]?.id || "";
      setSelectedProductId(nextProductId);
      const nextOpportunities = opportunityResult.filter(
        (opportunity) => opportunity.product_id === nextProductId,
      );
      setOpportunities(nextOpportunities);
      setSelectedOpportunityId(nextOpportunities[0]?.id || "");
      setInitiatives(nextProductId ? await listInitiatives(nextProductId) : []);
      setObjectives(objectiveResult.filter((objective) => objective.product_id === nextProductId));
    },
    [workspaceId],
  );

  useEffect(() => {
    if (!workspaceId) return;
    Promise.resolve()
      .then(() => refreshContext())
      .catch((error: unknown) =>
        setMessage(
          error instanceof Error ? error.message : t("workspace.loadError"),
        ),
      )
      .finally(() => setLoading(false));
  }, [refreshContext, t, workspaceId]);

  async function handleProductSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session || !workspaceId) return;
    setSaving("product");
    setMessage(null);
    try {
      const product = await createProduct({
        ...productForm,
        workspace_id: workspaceId,
        created_by: session.subject,
      });
      setProductForm(emptyProduct);
      await refreshContext(product.id);
      setCreationModal(null);
      setActiveTab("opportunity");
      setMessage(t("workspace.productCreated"));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : t("workspace.saveError"),
      );
    } finally {
      setSaving(null);
    }
  }

  async function handleOpportunitySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProductId) return;
    setSaving("opportunity");
    setMessage(null);
    try {
      const opportunity = editingOpportunityId
        ? await updateOpportunity(editingOpportunityId, {
            title: opportunityForm.title,
            description: opportunityForm.description,
            objective_ids: opportunityForm.objective_ids,
            expected_version: opportunities.find((item) => item.id === editingOpportunityId)?.version ?? 1,
          })
        : await createOpportunity({
            ...opportunityForm,
            product_id: selectedProductId,
          });
      setOpportunityForm(emptyOpportunity);
      await refreshContext(selectedProductId);
      setCreationModal(null);
      setEditingOpportunityId(null);
      setSelectedOpportunityId(opportunity.id);
      setActiveTab("initiative");
      setMessage(editingOpportunityId ? t("workspace.opportunityUpdated") : t("workspace.opportunityCreated"));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : t("workspace.saveError"),
      );
    } finally {
      setSaving(null);
    }
  }

  async function handleInitiativeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOpportunityId || !selectedProductId) return;
    setSaving("initiative");
    setMessage(null);
    try {
      await createInitiative(selectedOpportunityId, {
        ...initiativeForm,
        product_id: selectedProductId,
        objective_ids: initiativeForm.objective_ids,
        out_of_scope: initiativeForm.out_of_scope || undefined,
      });
      setInitiativeForm(emptyInitiative);
      await refreshContext(selectedProductId);
      setCreationModal(null);
      setMessage(t("workspace.initiativeCreated"));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : t("workspace.saveError"),
      );
    } finally {
      setSaving(null);
    }
  }

  if (!session)
    return (
      <section className="empty-state">
        <h1>{t("workspace.title")}</h1>
        <p>{t("workspace.signIn")}</p>
        <Link className="primary-button" href="/login">
          {t("overview.signIn")}
        </Link>
      </section>
    );
  if (loading)
    return (
      <section className="empty-state">
        <p>{t("workspace.loading")}</p>
      </section>
    );
  if (!workspaceId)
    return (
      <section className="empty-state">
        <h1>{t("workspace.title")}</h1>
        <p>{t("workspace.notConfigured")}</p>
      </section>
    );

  return (
    <div className="stack-lg workspace-page">
      <section className="dashboard-intro">
        <div>
          <span className="eyebrow">{t("workspace.eyebrow")}</span>
          <h1>{t("workspace.title")}</h1>
          <p>{t("workspace.description")}</p>
        </div>
        <span className="context-chip">{workspaceId}</span>
      </section>
      {message && (
        <div className="notice-box" role="status">
          {message}
        </div>
      )}
      <section
        className="creation-tabs"
        aria-label={t("workspace.creationTabs")}
      >
        {!section && (
          <div className="workspace-tabs" role="tablist">
            <button
              className={
                activeTab === "product"
                  ? "workspace-tab is-active"
                  : "workspace-tab"
              }
              role="tab"
              aria-selected={activeTab === "product"}
              type="button"
              onClick={() => setActiveTab("product")}
            >
              <span>01</span>
              {t("workspace.productTitle")}
              <strong>{products.length}</strong>
            </button>
            <button
              className={
                activeTab === "opportunity"
                  ? "workspace-tab is-active"
                  : "workspace-tab"
              }
              role="tab"
              aria-selected={activeTab === "opportunity"}
              type="button"
              onClick={() => setActiveTab("opportunity")}
            >
              <span>02</span>
              {t("workspace.opportunityTitle")}
              <strong>{opportunities.length}</strong>
            </button>
            <button
              className={
                activeTab === "initiative"
                  ? "workspace-tab is-active"
                  : "workspace-tab"
              }
              role="tab"
              aria-selected={activeTab === "initiative"}
              type="button"
              onClick={() => setActiveTab("initiative")}
            >
              <span>03</span>
              {t("workspace.initiativeTitle")}
              <strong>{initiatives.length}</strong>
            </button>
          </div>
        )}
        {visibleSection === "product" && (
          <article
            className="creation-panel workspace-tab-panel"
            role="tabpanel"
          >
            <div className="section-heading">
              <div>
                <span className="eyebrow">
                  01 / {t("workspace.productTitle")}
                </span>
                <h2>{t("workspace.productTitle")}</h2>
              </div>
              <button
                className="primary-button compact"
                type="button"
                onClick={() => setCreationModal("product")}
              >
                {t("workspace.newProduct")}
              </button>
            </div>
            <p>{t("workspace.productDescription")}</p>
            <div className="context-record-list">
              {products.length ? (
                products.map((product) => (
                  <div className="context-record" key={product.id}>
                    <strong>{product.name}</strong>
                    <span>
                      {product.description || t("overview.noDescription")}
                    </span>
                    <small>{product.status}</small>
                  </div>
                ))
              ) : (
                <p className="empty-state compact-empty">
                  {t("workspace.noProducts")}
                </p>
              )}
            </div>
          </article>
        )}
        {visibleSection === "opportunity" && (
          <article
            className="creation-panel workspace-tab-panel"
            role="tabpanel"
          >
            <div className="section-heading">
              <div>
                <span className="eyebrow">
                  02 / {t("workspace.opportunityTitle")}
                </span>
                <h2>{t("workspace.opportunityTitle")}</h2>
              </div>
              <button
                className="primary-button compact"
                type="button"
                disabled={!selectedProductId}
                onClick={() => {
                  setOpportunityForm(emptyOpportunity);
                  setEditingOpportunityId(null);
                  setCreationModal("opportunity");
                }}
              >
                {t("workspace.newOpportunity")}
              </button>
            </div>
            <p>{t("workspace.opportunityDescription")}</p>
            <label className="standalone-field">
              {t("workspace.productSelect")}
              <select
                value={selectedProductId}
                onChange={(event) => {
                  const value = event.target.value;
                  setSelectedProductId(value);
                  setSelectedOpportunityId("");
                  Promise.all([
                    listOpportunities(workspaceId),
                    listInitiatives(value),
                    listObjectives(workspaceId),
                  ]).then(([items, nextInitiatives, objectiveResult]) => {
                    setOpportunities(
                      items.filter((item) => item.product_id === value),
                    );
                    setInitiatives(nextInitiatives);
                    setObjectives(objectiveResult.filter((objective) => objective.product_id === value));
                    setInitiativeForm((current) => ({ ...current, objective_ids: [] }));
                  });
                }}
              >
                <option value="">{t("workspace.selectProduct")}</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="context-record-list">
              {opportunities.length ? (
                (() => {
                  const objectiveGroups = objectives.map((objective) => ({
                    objective,
                    opportunities: opportunities.filter((opportunity) =>
                      (opportunity.objective_ids ?? []).includes(objective.id),
                    ),
                  })).filter((group) => group.opportunities.length > 0);
                  const groupedOpportunityIds = new Set(
                    objectiveGroups.flatMap((group) => group.opportunities.map((opportunity) => opportunity.id)),
                  );
                  const ungroupedOpportunities = opportunities.filter(
                    (opportunity) => !groupedOpportunityIds.has(opportunity.id),
                  );
                  const renderOpportunity = (opportunity: Opportunity) => (
                    <div className="context-record" key={opportunity.id}>
                      <strong>{opportunity.title}</strong>
                      <span>{opportunity.description}</span>
                      <small>{opportunity.status}</small>
                      <button
                        className="text-link"
                        type="button"
                        onClick={() => {
                          setOpportunityForm({
                            title: opportunity.title,
                            description: opportunity.description,
                            objective_ids: opportunity.objective_ids ?? [],
                          });
                          setEditingOpportunityId(opportunity.id);
                          setCreationModal("opportunity");
                        }}
                      >
                        {t("workspace.editOpportunity")}
                      </button>
                    </div>
                  );
                  return (
                    <>
                      {objectiveGroups.map(({ objective, opportunities: groupedOpportunities }) => (
                        <section className="opportunity-group" key={objective.id}>
                          <h3>{objective.title}</h3>
                          <div className="opportunity-group-list">
                            {groupedOpportunities.map(renderOpportunity)}
                          </div>
                        </section>
                      ))}
                      {ungroupedOpportunities.length > 0 && (
                        <section className="opportunity-group">
                          <h3>{t("workspace.opportunitiesWithoutObjective")}</h3>
                          <div className="opportunity-group-list">
                            {ungroupedOpportunities.map(renderOpportunity)}
                          </div>
                        </section>
                      )}
                    </>
                  );
                })()
              ) : (
                <p className="empty-state compact-empty">
                  {t("workspace.noOpportunities")}
                </p>
              )}
            </div>
          </article>
        )}
        {visibleSection === "initiative" && (
          <article
            className="creation-panel workspace-tab-panel"
            role="tabpanel"
          >
            <div className="section-heading">
              <div>
                <span className="eyebrow">
                  03 / {t("workspace.initiativeTitle")}
                </span>
                <h2>{t("workspace.initiativeTitle")}</h2>
              </div>
              <button
                className="primary-button compact"
                type="button"
                disabled={!selectedOpportunityId}
                onClick={() => setCreationModal("initiative")}
              >
                {t("workspace.newInitiative")}
              </button>
            </div>
            <p>{t("workspace.initiativeDescription")}</p>
            <label className="standalone-field">
              {t("workspace.opportunitySelect")}
              <select
                value={selectedOpportunityId}
                onChange={(event) =>
                  setSelectedOpportunityId(event.target.value)
                }
                disabled={!selectedProductId}
              >
                <option value="">{t("workspace.selectOpportunity")}</option>
                {opportunities.map((opportunity) => (
                  <option key={opportunity.id} value={opportunity.id}>
                    {opportunity.title}
                  </option>
                ))}
              </select>
            </label>
            <div className="context-record-list">
              {initiatives.length ? (
                initiatives.map((initiative) => (
                  <div className="context-record" key={initiative.id}>
                    <strong>{initiative.title}</strong>
                    <span>{initiative.objective}</span>
                    <small>{initiative.status}</small>
                  </div>
                ))
              ) : (
                <p className="empty-state compact-empty">
                  {t("workspace.noInitiatives")}
                </p>
              )}
            </div>
          </article>
        )}
      </section>
      {creationModal && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => setCreationModal(null)}
        >
          <section
            className="assessment-modal context-create-modal"
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="modal-header">
              <div>
                <span className="eyebrow">{editingOpportunityId ? t("workspace.editRecord") : t("workspace.newRecord")}</span>
                <h2>
                  {creationModal === "product"
                    ? t("workspace.productTitle")
                    : creationModal === "opportunity"
                      ? editingOpportunityId ? t("workspace.editOpportunity") : t("workspace.opportunityTitle")
                      : t("workspace.initiativeTitle")}
                </h2>
              </div>
              <button
                className="modal-close"
                type="button"
                aria-label={t("workspace.closeModal")}
                onClick={() => {
                  setCreationModal(null);
                  setEditingOpportunityId(null);
                }}
              >
                ×
              </button>
            </header>
            {creationModal === "product" && (
              <form
                onSubmit={handleProductSubmit}
                className="creation-form context-modal-form"
              >
                <label>
                  {t("workspace.name")}
                  <input
                    required
                    value={productForm.name}
                    onChange={(event) =>
                      setProductForm({
                        ...productForm,
                        name: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  {t("workspace.descriptionField")}
                  <textarea
                    required
                    rows={3}
                    value={productForm.description}
                    onChange={(event) =>
                      setProductForm({
                        ...productForm,
                        description: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  {t("workspace.vision")}
                  <textarea
                    rows={2}
                    value={productForm.vision}
                    onChange={(event) =>
                      setProductForm({
                        ...productForm,
                        vision: event.target.value,
                      })
                    }
                  />
                </label>
                <button
                  className="primary-button"
                  disabled={saving !== null}
                  type="submit"
                >
                  {saving === "product"
                    ? t("workspace.saving")
                    : t("workspace.createProduct")}
                </button>
              </form>
            )}
            {creationModal === "opportunity" && (
              <form
                onSubmit={handleOpportunitySubmit}
                className="creation-form context-modal-form"
              >
                <label>
                  {t("workspace.titleField")}
                  <input
                    required
                    value={opportunityForm.title}
                    onChange={(event) =>
                      setOpportunityForm({
                        ...opportunityForm,
                        title: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  {t("workspace.descriptionField")}
                  <textarea
                    required
                    rows={3}
                    value={opportunityForm.description}
                    onChange={(event) =>
                      setOpportunityForm({
                        ...opportunityForm,
                        description: event.target.value,
                      })
                    }
                  />
                </label>
                <fieldset>
                  <legend>{t("workspace.objectivesSelect")}</legend>
                  {objectives.length ? objectives.map((objective) => (
                    <label key={objective.id}>
                      <input
                        type="checkbox"
                        checked={opportunityForm.objective_ids.includes(objective.id)}
                        onChange={(event) => setOpportunityForm({
                          ...opportunityForm,
                          objective_ids: event.target.checked
                            ? [...opportunityForm.objective_ids, objective.id]
                            : opportunityForm.objective_ids.filter((id) => id !== objective.id),
                        })}
                      />
                      {objective.title}
                    </label>
                  )) : <small>{t("workspace.noObjectives")}</small>}
                </fieldset>
                <button
                  className="primary-button"
                  disabled={saving !== null || !selectedProductId}
                  type="submit"
                >
                  {saving === "opportunity"
                    ? t("workspace.saving")
                    : editingOpportunityId ? t("workspace.saveOpportunity") : t("workspace.createOpportunity")}
                </button>
              </form>
            )}
            {creationModal === "initiative" && (
              <form
                onSubmit={handleInitiativeSubmit}
                className="creation-form context-modal-form"
              >
                <label>
                  {t("workspace.titleField")}
                  <input
                    required
                    value={initiativeForm.title}
                    onChange={(event) =>
                      setInitiativeForm({
                        ...initiativeForm,
                        title: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  {t("workspace.objective")}
                  <textarea
                    required
                    rows={2}
                    value={initiativeForm.objective}
                    onChange={(event) =>
                      setInitiativeForm({
                        ...initiativeForm,
                        objective: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  {t("workspace.scope")}
                  <textarea
                    required
                    rows={2}
                    value={initiativeForm.scope}
                    onChange={(event) =>
                      setInitiativeForm({
                        ...initiativeForm,
                        scope: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  {t("workspace.outOfScope")}
                  <textarea
                    rows={2}
                    value={initiativeForm.out_of_scope}
                    onChange={(event) =>
                      setInitiativeForm({
                        ...initiativeForm,
                        out_of_scope: event.target.value,
                      })
                    }
                  />
                </label>
                <fieldset>
                  <legend>{t("workspace.objectivesSelect")}</legend>
                  {objectives.length ? objectives.map((objective) => (
                    <label key={objective.id}>
                      <input
                        type="checkbox"
                        checked={initiativeForm.objective_ids.includes(objective.id)}
                        onChange={(event) => setInitiativeForm({
                          ...initiativeForm,
                          objective_ids: event.target.checked
                            ? [...initiativeForm.objective_ids, objective.id]
                            : initiativeForm.objective_ids.filter((id) => id !== objective.id),
                        })}
                      />
                      {objective.title}
                    </label>
                  )) : <small>{t("workspace.noObjectives")}</small>}
                </fieldset>
                <button
                  className="primary-button"
                  disabled={saving !== null || !selectedOpportunityId}
                  type="submit"
                >
                  {saving === "initiative"
                    ? t("workspace.saving")
                    : t("workspace.createInitiative")}
                </button>
              </form>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
