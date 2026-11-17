export type RiskStatus =
  | "PENDING"
  | "CLEAR"
  | "REVIEW"
  | "HOLD";

export type ApprovalStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED";

export type ReviewStatus =
  | "NOT_REQUIRED"
  | "PENDING"
  | "CLEARED"
  | "REJECTED";

export type VerificationStatus =
  | "NOT_REQUIRED"
  | "PENDING"
  | "VERIFIED";

export type UserRole =
  | "FINANCE_REVIEWER"
  | "FINANCE_APPROVER"
  | "ADMIN";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
}

export interface InvoiceItem {
  id: number;
  description: string;
  quantity: string;
  unit_price: string;
  line_total: string;
}

export interface RiskFinding {
  id: number;
  invoice_id: number;
  rule_code: string;
  severity: string;
  action: string;
  message: string;
  evidence: Record<string, unknown>;
  created_at: string;
}

export interface Invoice {
  id: number;
  vendor_id: number | null;
  vendor_name: string | null;
  invoice_number: string | null;
  invoice_date: string | null;

  gstin: string | null;
  bank_account: string | null;
  ifsc: string | null;

  subtotal: string | null;
  tax: string | null;
  total: string | null;

  source_filename: string;

  extraction_method: string;
  extraction_status: string;
  extraction_confidence: number;
  field_confidence: Record<string, number>;

  extraction_warning: string | null;

  risk_status: RiskStatus;
  risk_score: number;
  risk_findings: RiskFinding[];

  approval_status: ApprovalStatus;

  review_status: ReviewStatus;
  reviewed_by_id: number | null;
  reviewed_at: string | null;
  review_note: string | null;

  verification_status: VerificationStatus;
  verified_by_id: number | null;
  verified_at: string | null;
  verification_method: string | null;
  verification_reference: string | null;
  verification_note: string | null;

  approved_by_id: number | null;
  approved_at: string | null;

  rejected_by_id: number | null;
  rejected_at: string | null;
  rejection_reason: string | null;

  uploaded_at: string;
  items: InvoiceItem[];
}

export interface AuditEvent {
  id: number;
  invoice_id: number | null;
  actor_id: number | null;
  action: string;
  outcome: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface GlobalAuditEvent {
  id: number;
  invoice_id: number | null;
  invoice_number: string | null;
  actor_id: number | null;
  actor_name: string;
  action: string;
  outcome: string;
  details: Record<string, unknown>;
  created_at: string;
}