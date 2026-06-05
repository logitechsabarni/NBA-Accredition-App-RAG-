export default function ConfirmDialog({
  open,
  title,
  description,
  onConfirm,
  onCancel,
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

      <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-[400px]">

        <h2 className="text-xl font-bold">
          {title}
        </h2>

        <p className="mt-2 text-slate-500">
          {description}
        </p>

        <div className="flex justify-end gap-3 mt-6">

          <button
            onClick={onCancel}
            className="px-4 py-2 border rounded-lg"
          >
            Cancel
          </button>

          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-red-600 text-white rounded-lg"
          >
            Confirm
          </button>

        </div>

      </div>

    </div>
  );
}
