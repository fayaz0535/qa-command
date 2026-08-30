import UploadDropzone from "@/components/UploadDropzone";

export default function UploadPage() {
  return (
    <div className="p-6 max-w-2xl mx-auto space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-[#0D1117]">Upload data</h1>
        <p className="text-sm text-gray-500 mt-1">
          Phase 1 supports CSV/XLSX uploads. Re-uploading the same file preserves remarks history
          and detects reopened defects automatically — nothing is ever overwritten.
        </p>
      </div>
      <UploadDropzone />
    </div>
  );
}
