"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { Pencil, Trash2, Plus } from "lucide-react";
import {
  createProduct,
  deleteProduct,
  updateProduct,
  type Product,
} from "@/lib/api";
import { occasions } from "@/lib/occasions";
import { formatPrice } from "@/lib/utils";
import type { Locale } from "@/i18n/routing";

interface FormState {
  slug: string;
  name_it: string;
  name_en: string;
  description_it: string;
  description_en: string;
  priceEuros: string;
  occasion: string;
  is_active: boolean;
}

const emptyForm: FormState = {
  slug: "",
  name_it: "",
  name_en: "",
  description_it: "",
  description_en: "",
  priceEuros: "",
  occasion: "",
  is_active: true,
};

export function ProductsManager({ initial }: { initial: Product[] }) {
  const t = useTranslations("admin.products");
  const locale = useLocale() as Locale;
  const [rows, setRows] = useState<Product[]>(initial);
  const [editingId, setEditingId] = useState<number | "new" | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function openNew() {
    setForm(emptyForm);
    setEditingId("new");
    setError(null);
  }

  function openEdit(p: Product) {
    setForm({
      slug: p.slug,
      name_it: p.name_it,
      name_en: p.name_en,
      description_it: p.description_it ?? "",
      description_en: p.description_en ?? "",
      priceEuros: (p.base_price_cents / 100).toFixed(2),
      occasion: p.occasion ?? "",
      is_active: p.is_active,
    });
    setEditingId(p.id);
    setError(null);
  }

  async function save() {
    setBusy(true);
    setError(null);
    const cents = Math.round(parseFloat(form.priceEuros || "0") * 100);
    try {
      if (editingId === "new") {
        const created = await createProduct({
          slug: form.slug,
          name_it: form.name_it,
          name_en: form.name_en,
          description_it: form.description_it || null,
          description_en: form.description_en || null,
          base_price_cents: cents,
          occasion: form.occasion || null,
          is_active: form.is_active,
        });
        setRows((r) => [...r, created]);
      } else if (typeof editingId === "number") {
        const updated = await updateProduct(editingId, {
          name_it: form.name_it,
          name_en: form.name_en,
          description_it: form.description_it || null,
          description_en: form.description_en || null,
          base_price_cents: cents,
          occasion: form.occasion || null,
          is_active: form.is_active,
        });
        setRows((r) => r.map((p) => (p.id === updated.id ? updated : p)));
      }
      setEditingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("saveError"));
    } finally {
      setBusy(false);
    }
  }

  async function remove(p: Product) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteProduct(p.id);
    setRows((r) => r.filter((x) => x.id !== p.id));
  }

  const field = (
    label: string,
    key: keyof FormState,
    type: "text" | "number" = "text",
  ) => (
    <label className="block text-sm">
      <span className="mb-1 block text-ad-ink-muted">{label}</span>
      <input
        type={type}
        value={form[key] as string}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="h-10 w-full rounded-md border border-ad-border px-3 focus:outline-none focus:ring-2 focus:ring-ad-primary"
      />
    </label>
  );

  return (
    <div className="space-y-4">
      {editingId === null && (
        <div className="flex justify-end">
          <button
            onClick={openNew}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-ad-primary px-4 text-sm font-medium text-white hover:bg-ad-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ad-primary focus-visible:ring-offset-2"
          >
            <Plus className="h-4 w-4" aria-hidden /> {t("new")}
          </button>
        </div>
      )}

      {editingId !== null && (
        <div className="rounded-xl border border-ad-border bg-ad-surface p-5">
          <h2 className="mb-4 text-lg font-semibold text-ad-ink">
            {editingId === "new" ? t("create") : t("update")}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {editingId === "new" && field(t("slug"), "slug")}
            {field(t("price"), "priceEuros", "number")}
            {field(t("nameIt"), "name_it")}
            {field(t("nameEn"), "name_en")}
            {field(t("descIt"), "description_it")}
            {field(t("descEn"), "description_en")}
            <label className="block text-sm">
              <span className="mb-1 block text-ad-ink-muted">
                {t("occasion")}
              </span>
              <select
                value={form.occasion}
                onChange={(e) =>
                  setForm({ ...form, occasion: e.target.value })
                }
                className="h-10 w-full rounded-md border border-ad-border bg-ad-surface px-3 focus:outline-none focus:ring-2 focus:ring-ad-primary"
              >
                <option value="">{t("none")}</option>
                {occasions.map((o) => (
                  <option key={o.slug} value={o.slug}>
                    {o.label[locale]}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 self-end text-sm text-ad-ink">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) =>
                  setForm({ ...form, is_active: e.target.checked })
                }
                className="h-4 w-4"
              />
              {t("active")}
            </label>
          </div>

          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

          <div className="mt-5 flex gap-2">
            <button
              onClick={save}
              disabled={busy}
              className="h-10 rounded-md bg-ad-primary px-5 text-sm font-medium text-white hover:bg-ad-primary-hover disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ad-primary focus-visible:ring-offset-2"
            >
              {t("save")}
            </button>
            <button
              onClick={() => setEditingId(null)}
              className="h-10 rounded-md border border-ad-border px-5 text-sm font-medium text-ad-ink hover:bg-ad-primary-soft"
            >
              {t("cancel")}
            </button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-ad-border bg-ad-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ad-border text-left text-ad-ink-muted">
              <th className="p-3 font-medium">{t("colName")}</th>
              <th className="p-3 font-medium">{t("colOccasion")}</th>
              <th className="p-3 text-right font-medium">{t("colPrice")}</th>
              <th className="p-3 font-medium">{t("colStatus")}</th>
              <th className="p-3 text-right font-medium">{t("colActions")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-b border-ad-border last:border-0">
                <td className="p-3">
                  <div className="font-medium text-ad-ink">{p.name_en}</div>
                  <div className="text-ad-ink-muted">{p.name_it}</div>
                </td>
                <td className="p-3 text-ad-ink-muted">{p.occasion ?? "—"}</td>
                <td className="p-3 text-right tabular-nums text-ad-ink">
                  {formatPrice(p.base_price_cents, locale)}
                </td>
                <td className="p-3">
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className={
                        "h-2 w-2 rounded-full " +
                        (p.is_active ? "bg-green-600" : "bg-slate-400")
                      }
                      aria-hidden
                    />
                    {p.is_active ? t("statusActive") : t("statusHidden")}
                  </span>
                </td>
                <td className="p-3">
                  <div className="flex justify-end gap-1">
                    <button
                      onClick={() => openEdit(p)}
                      aria-label={t("edit")}
                      className="flex h-9 w-9 items-center justify-center rounded-md text-ad-ink-muted hover:bg-ad-primary-soft hover:text-ad-primary"
                    >
                      <Pencil className="h-4 w-4" aria-hidden />
                    </button>
                    <button
                      onClick={() => remove(p)}
                      aria-label={t("delete")}
                      className="flex h-9 w-9 items-center justify-center rounded-md text-ad-ink-muted hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
