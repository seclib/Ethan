"use client";

import { motion, AnimatePresence } from "framer-motion";

interface ApprovalModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "info";
}

export function ApprovalModal({
  open, onClose, onConfirm,
  title, description,
  confirmLabel = "Confirmer",
  cancelLabel = "Annuler",
  variant = "info",
}: ApprovalModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="approval-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          <motion.div
            className="approval-modal"
            data-variant={variant}
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.92, opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            <div className="approval-header">
              <span className="approval-title">{title}</span>
              <button className="approval-close" onClick={onClose}>✕</button>
            </div>
            {description && <div className="approval-desc">{description}</div>}
            <div className="approval-actions">
              <button className="approval-btn approval-btn--cancel" onClick={onClose}>
                {cancelLabel}
              </button>
              <button className="approval-btn approval-btn--confirm" onClick={onConfirm}>
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}