"use client";

import { useEffect, useState } from "react";
import { Sparkles, Download, Copy, CheckCircle2, Loader2 } from "lucide-react";
import { draftEmail, downloadEml, getSendConfig, updateSendConfig } from "@/lib/api";
import type { EmailDraft } from "@/lib/types";

export default function EmailPage() {
  const [draft, setDraft] = useState<EmailDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [keyMessage, setKeyMessage] = useState("");
  const [ask, setAsk] = useState("");
  const [html, setHtml] = useState("");
  const [recipients, setRecipients] = useState("");
  const [cc, setCc] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getSendConfig().then((cfg) => {
      setRecipients(cfg.recipients.join(", "));
      setCc(cfg.cc.join(", "));
    }).catch(() => {});
  }, []);

  const generate = async () => {
    setLoading(true);
    setReviewed(false);
    try {
      const d = await draftEmail();
      setDraft(d);
      setKeyMessage(d.key_message);
      setAsk(d.ask);
      setHtml(d.html);
    } finally {
      setLoading(false);
    }
  };

  const applyEdit = (field: "key_message" | "ask", value: string) => {
    if (!draft) return;
    const original = field === "key_message" ? draft.key_message : draft.ask;
    setHtml((prev) => (original ? prev.replace(original, value) : prev));
    if (field === "key_message") setKeyMessage(value);
    else setAsk(value);
    setReviewed(false);
  };

  const parseEmails = (s: string) => s.split(",").map((e) => e.trim()).filter(Boolean);

  const saveRecipients = async () => {
    await updateSendConfig({
      recipients: parseEmails(recipients), cc: parseEmails(cc), send_time: "08:00",
    });
  };

  const handleDownloadEml = async () => {
    if (!draft) return;
    const blob = await downloadEml(draft.subject, html, parseEmails(recipients), parseEmails(cc), draft.attachments);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "qa-command-daily-report.eml";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const handleCopyHtml = async () => {
    await navigator.clipboard.writeText(html);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[#0D1117]">Daily Report</h1>
          <p className="text-sm text-gray-500 mt-1">
            Review-then-send: nothing here sends automatically. Generate, edit, then download or copy for
            the DM to send from Outlook.
          </p>
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="flex items-center gap-2 bg-qc-primary text-white text-sm font-medium px-4 py-2 rounded-md
                     hover:bg-qc-primary-hover disabled:opacity-50"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          Generate today's draft
        </button>
      </div>

      {!draft ? (
        <div className="bg-white border border-black/[0.08] rounded-xl p-10 text-center text-sm text-gray-400">
          No draft yet — click "Generate today's draft" above.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="space-y-4">
            <div className="bg-white border border-black/[0.08] rounded-xl p-4 shadow-sm space-y-3">
              <div className="text-sm font-semibold text-[#0D1117]">Edit before sending</div>
              <label className="block text-xs text-gray-500">
                Key message
                <textarea
                  value={keyMessage}
                  onChange={(e) => applyEdit("key_message", e.target.value)}
                  rows={2}
                  className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
                />
              </label>
              <label className="block text-xs text-gray-500">
                Today's Ask
                <textarea
                  value={ask}
                  onChange={(e) => applyEdit("ask", e.target.value)}
                  rows={2}
                  className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
                />
              </label>
              <label className="block text-xs text-gray-500">
                Recipients (comma-separated)
                <input
                  value={recipients}
                  onChange={(e) => setRecipients(e.target.value)}
                  onBlur={saveRecipients}
                  placeholder="dm@zaimahtech.ae, lead@eibank.com"
                  className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
                />
              </label>
              <label className="block text-xs text-gray-500">
                Cc (comma-separated)
                <input
                  value={cc}
                  onChange={(e) => setCc(e.target.value)}
                  onBlur={saveRecipients}
                  className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleDownloadEml}
                className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                           bg-white text-gray-700 hover:bg-gray-50"
              >
                <Download size={14} /> Download .eml
              </button>
              <button
                onClick={handleCopyHtml}
                className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                           bg-white text-gray-700 hover:bg-gray-50"
              >
                <Copy size={14} /> {copied ? "Copied!" : "Copy HTML"}
              </button>
              <button
                onClick={() => setReviewed(true)}
                disabled={reviewed}
                className={`flex items-center gap-1.5 text-sm rounded-md px-3 py-1.5 font-medium ${
                  reviewed ? "bg-emerald-50 text-emerald-600 border border-emerald-200"
                           : "bg-qc-accent/10 text-qc-accent border border-qc-accent/30 hover:bg-qc-accent/20"
                }`}
              >
                <CheckCircle2 size={14} /> {reviewed ? "Reviewed by DM → ready to share" : "Mark reviewed"}
              </button>
            </div>

            <div className="text-xs text-gray-400">
              Attachments: {Object.keys(draft.attachments).join(", ")}
            </div>
          </div>

          <div className="bg-white border border-black/[0.08] rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-2.5 border-b border-black/[0.08] text-xs text-gray-400 flex items-center justify-between">
              <span>Preview — exactly as stakeholders will see it</span>
              <span>{draft.subject}</span>
            </div>
            <iframe srcDoc={html} className="w-full h-[600px] border-0" title="Email preview" />
          </div>
        </div>
      )}
    </div>
  );
}
